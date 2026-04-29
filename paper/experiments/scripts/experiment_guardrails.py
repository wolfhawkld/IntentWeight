#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Protocol metadata and comparability guardrails for retrieval experiments."""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
DEFAULT_RESULTS_DIR = SCRIPT_DIR.parent / "results"

TASK_TYPES = {
    "pubmedqa": "evidence_retrieval",
    "emanual": "evidence_retrieval",
    "cuad": "evidence_retrieval",
    "banking77": "intent_retrieval_proxy",
}

REQUIRED_METHODS = {"bm25", "dense", "hybrid_rrf"}
METRIC_PREFIXES = ("recall@", "mrr@", "ndcg@")
CORPUS_SAMPLING_STRATEGIES = {"first", "gt_anchored", "auto"}


def load_json_list(path: Path) -> List[Mapping]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def query_record_split(query: Mapping) -> str | None:
    split = query.get("split")
    if split:
        return str(split)
    metadata = query.get("metadata")
    if isinstance(metadata, Mapping) and metadata.get("split"):
        return str(metadata["split"])
    return None


def query_splits(queries: Sequence[Mapping]) -> List[str]:
    splits = sorted({split for query in queries if (split := query_record_split(query))})
    return splits


def describe_query_split(queries: Sequence[Mapping]) -> str:
    splits = query_splits(queries)
    if not splits:
        return "unknown"
    if len(splits) == 1:
        return splits[0]
    return "mixed"


def filter_queries_by_split(queries: Sequence[Mapping], split: str | None) -> List[Mapping]:
    if split is None or split == "all":
        return list(queries)
    filtered = [query for query in queries if query_record_split(query) == split]
    if not filtered:
        raise ValueError(f"No queries found for split={split!r}")
    return filtered


def positive_or_none(value: int | None, name: str) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def apply_query_controls(
    queries: Sequence[Mapping],
    *,
    query_split: str | None = None,
    max_queries: int | None = None,
) -> List[Mapping]:
    max_queries = positive_or_none(max_queries, "max_queries")
    filtered = filter_queries_by_split(queries, query_split)
    if max_queries is not None:
        filtered = filtered[:max_queries]
    return filtered


def _record_chunk_id(chunk: Mapping) -> str:
    chunk_id = chunk.get("chunk_id") or chunk.get("id")
    if chunk_id is None:
        raise ValueError(f"Corpus chunk missing chunk_id/id: {chunk}")
    return str(chunk_id)


def _query_ground_truth(query: Mapping) -> set[str]:
    return {str(chunk_id) for chunk_id in (query.get("ground_truth_chunk_ids") or [])}


def resolve_corpus_sampling(dataset: str, max_corpus: int | None, corpus_sampling: str | None = None) -> str:
    strategy = corpus_sampling or "auto"
    if strategy not in CORPUS_SAMPLING_STRATEGIES:
        raise ValueError(f"Unknown corpus_sampling={strategy!r}; expected one of {sorted(CORPUS_SAMPLING_STRATEGIES)}")
    if strategy == "auto":
        return "gt_anchored" if dataset == "cuad" and max_corpus is not None else "first"
    return strategy


def apply_corpus_controls(
    corpus: Sequence[Mapping],
    *,
    max_corpus: int | None = None,
    queries: Sequence[Mapping] | None = None,
    corpus_sampling: str = "first",
    random_seed: int = 13,
) -> List[Mapping]:
    max_corpus = positive_or_none(max_corpus, "max_corpus")
    if max_corpus is None:
        return list(corpus)
    if corpus_sampling == "first":
        return list(corpus[:max_corpus])
    if corpus_sampling != "gt_anchored":
        raise ValueError(f"Unknown corpus_sampling={corpus_sampling!r}")
    if queries is None:
        raise ValueError("queries are required for gt_anchored corpus sampling")

    corpus_by_id = {_record_chunk_id(chunk): chunk for chunk in corpus}
    anchored_ids: List[str] = []
    seen: set[str] = set()
    for query in queries:
        for chunk_id in sorted(_query_ground_truth(query)):
            if chunk_id in corpus_by_id and chunk_id not in seen:
                anchored_ids.append(chunk_id)
                seen.add(chunk_id)

    if len(anchored_ids) > max_corpus:
        raise ValueError(
            f"gt_anchored sample needs {len(anchored_ids)} GT chunks but max_corpus={max_corpus}; "
            "increase max_corpus or reduce max_queries."
        )

    remaining = [chunk for chunk in corpus if _record_chunk_id(chunk) not in seen]
    rng = random.Random(random_seed)
    rng.shuffle(remaining)
    selected = [corpus_by_id[chunk_id] for chunk_id in anchored_ids]
    selected.extend(remaining[: max_corpus - len(selected)])
    return selected


def _compact_number(value: object) -> str:
    if value in (None, ""):
        return "full"
    return str(value)


def corpus_scope(
    num_corpus_chunks: int,
    num_total_corpus_chunks: int | None,
    max_corpus: int | None,
    corpus_sampling: str = "first",
) -> str:
    if max_corpus is not None:
        return f"{corpus_sampling}_{max_corpus}" if corpus_sampling != "first" else f"first_{max_corpus}"
    if num_total_corpus_chunks is not None and num_corpus_chunks < num_total_corpus_chunks:
        return f"subset_{num_corpus_chunks}_of_{num_total_corpus_chunks}"
    return "full"


def gt_corpus_coverage(queries: Sequence[Mapping], corpus: Sequence[Mapping]) -> Dict[str, object]:
    corpus_ids = {_record_chunk_id(chunk) for chunk in corpus}
    num_queries_with_gt = 0
    num_queries_with_gt_in_corpus = 0
    num_gt_refs = 0
    num_gt_refs_in_corpus = 0

    for query in queries:
        gt = _query_ground_truth(query)
        if not gt:
            continue
        num_queries_with_gt += 1
        in_corpus = gt & corpus_ids
        if in_corpus:
            num_queries_with_gt_in_corpus += 1
        num_gt_refs += len(gt)
        num_gt_refs_in_corpus += len(in_corpus)

    query_coverage = num_queries_with_gt_in_corpus / num_queries_with_gt if num_queries_with_gt else 1.0
    ref_coverage = num_gt_refs_in_corpus / num_gt_refs if num_gt_refs else 1.0
    return {
        "num_queries_with_gt": num_queries_with_gt,
        "num_queries_with_gt_in_corpus": num_queries_with_gt_in_corpus,
        "num_queries_gt_missing_from_corpus": num_queries_with_gt - num_queries_with_gt_in_corpus,
        "num_gt_refs": num_gt_refs,
        "num_gt_refs_in_corpus": num_gt_refs_in_corpus,
        "num_gt_refs_missing_from_corpus": num_gt_refs - num_gt_refs_in_corpus,
        "gt_query_coverage": query_coverage,
        "gt_ref_coverage": ref_coverage,
        "gt_corpus_guardrail": "pass" if num_queries_with_gt == num_queries_with_gt_in_corpus else "fail",
    }


def assert_gt_corpus_coverage(queries: Sequence[Mapping], corpus: Sequence[Mapping]) -> Dict[str, object]:
    coverage = gt_corpus_coverage(queries, corpus)
    if coverage["num_queries_gt_missing_from_corpus"]:
        raise ValueError(
            "GT corpus coverage guardrail failed: "
            f"{coverage['num_queries_gt_missing_from_corpus']} of {coverage['num_queries_with_gt']} "
            "queries with GT have no GT chunk in the selected corpus."
        )
    return coverage


def query_scope(query_split: str, max_queries: int | None) -> str:
    prefix = f"split_{query_split}" if query_split not in {"unknown", "mixed"} else query_split
    if max_queries is not None:
        return f"{prefix}_first_{max_queries}"
    return prefix


def experiment_scope(dataset: str, query_split: str, max_queries: int | None, max_corpus: int | None) -> str:
    if max_queries is not None or max_corpus is not None:
        return "smoke_only" if dataset == "cuad" else "sample"
    if query_split == "test":
        return "heldout_test"
    if query_split == "mixed":
        return "historical_mixed_split"
    return "full"


def _metric_ks(metrics: Mapping) -> str:
    if "ks" in metrics and isinstance(metrics["ks"], list):
        return ",".join(str(k) for k in metrics["ks"])
    ks = sorted({key.split("@", 1)[1] for key in metrics if any(key.startswith(prefix) for prefix in METRIC_PREFIXES)})
    return ",".join(ks)


def comparable_group(row: Mapping) -> str:
    return "|".join(
        [
            f"dataset={row.get('dataset', '')}",
            f"query_scope={row.get('query_scope', '')}",
            f"corpus_scope={row.get('corpus_scope', '')}",
            f"top_k={row.get('top_k', '')}",
            f"ks={row.get('metric_ks', '')}",
        ]
    )


def build_run_metadata(
    *,
    dataset: str,
    queries: Sequence[Mapping],
    all_queries: Sequence[Mapping],
    corpus: Sequence[Mapping],
    all_corpus: Sequence[Mapping],
    max_queries: int | None = None,
    max_corpus: int | None = None,
    corpus_sampling: str = "first",
    requested_query_split: str | None = None,
    top_k: int | None = None,
    ks: Sequence[int] | None = None,
) -> Dict[str, object]:
    actual_split = describe_query_split(queries)
    splits = query_splits(queries)
    c_scope = corpus_scope(len(corpus), len(all_corpus), max_corpus, corpus_sampling)
    q_scope = query_scope(actual_split, max_queries)
    coverage = gt_corpus_coverage(queries, corpus)
    row = {
        "dataset": dataset,
        "task_type": TASK_TYPES.get(dataset, "unknown"),
        "query_split": actual_split,
        "query_splits": splits,
        "requested_query_split": requested_query_split or "all",
        "query_scope": q_scope,
        "scope": experiment_scope(dataset, actual_split, max_queries, max_corpus),
        "corpus_scope": c_scope,
        "corpus_sampling": corpus_sampling,
        "num_total_corpus_chunks": len(all_corpus),
        "num_query_candidates": len(filter_queries_by_split(all_queries, requested_query_split)),
        "metric_ks": ",".join(str(k) for k in ks) if ks else "",
        **coverage,
    }
    if top_k is not None:
        row["top_k"] = top_k
    row["comparable_group"] = comparable_group(row)
    row["is_comparable"] = ""
    row["notes"] = notes_for_row({**row, "dataset": dataset})
    return row


def notes_for_row(row: Mapping) -> str:
    notes: List[str] = []
    dataset = str(row.get("dataset", ""))
    query_split_value = str(row.get("query_split", ""))
    scope = str(row.get("scope", ""))
    method = str(row.get("method", ""))
    model = str(row.get("model", ""))

    if dataset == "pubmedqa":
        notes.append("GT is abstract context section-level, not strict answer-supporting sentence evidence.")
    if dataset == "banking77":
        notes.append("Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions.")
    if query_split_value == "mixed":
        notes.append("Mixed train/validation/test queries; keep out of held-out main table.")
    if scope in {"sample", "smoke_only"}:
        notes.append("Sampled query/corpus scope; use only with matching comparison group.")
    if dataset == "cuad" and scope == "smoke_only":
        notes.append("CUAD smoke/sample result; not a full-corpus held-out result.")
    if row.get("gt_corpus_guardrail") == "fail":
        notes.append("Invalid GT coverage: at least one evaluated GT query has no GT chunk in the selected corpus.")
    if row.get("corpus_sampling") == "gt_anchored":
        notes.append("Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors.")
    if method in {"dense", "hybrid_rrf"} and model == "sentence-transformers/all-MiniLM-L6-v2":
        notes.append("Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large.")
    return " ".join(notes)


def enrich_metrics_row(row: Mapping, data_dir: Path) -> Dict[str, object]:
    enriched: Dict[str, object] = dict(row)
    dataset = str(enriched.get("dataset", ""))
    queries_path = data_dir / f"{dataset}_queries.json"
    if queries_path.exists():
        all_queries = load_json_list(queries_path)
        selected_queries = apply_query_controls(
            all_queries,
            query_split=str(enriched.get("requested_query_split") or "all"),
            max_queries=_int_or_none(enriched.get("max_queries")),
        )
        enriched.setdefault("query_split", describe_query_split(selected_queries))
        enriched.setdefault("query_splits", query_splits(selected_queries))
        enriched.setdefault("query_scope", query_scope(str(enriched["query_split"]), _int_or_none(enriched.get("max_queries"))))
        enriched.setdefault("num_query_candidates", len(filter_queries_by_split(all_queries, str(enriched.get("requested_query_split") or "all"))))
    else:
        enriched.setdefault("query_split", "unknown")
        enriched.setdefault("query_splits", [])
        enriched.setdefault("query_scope", query_scope(str(enriched["query_split"]), _int_or_none(enriched.get("max_queries"))))

    enriched.setdefault("task_type", TASK_TYPES.get(dataset, "unknown"))
    num_corpus = _int_or_none(enriched.get("num_corpus_chunks")) or 0
    total_corpus = _int_or_none(enriched.get("num_total_corpus_chunks")) or num_corpus
    max_corpus = _int_or_none(enriched.get("max_corpus"))
    max_queries = _int_or_none(enriched.get("max_queries"))
    enriched["num_total_corpus_chunks"] = total_corpus
    corpus_sampling = str(enriched.get("corpus_sampling") or ("first" if max_corpus is not None else "full"))
    if corpus_sampling == "full":
        corpus_sampling = "first"
    enriched.setdefault("corpus_scope", corpus_scope(num_corpus, total_corpus, max_corpus, corpus_sampling))
    enriched.setdefault("scope", experiment_scope(dataset, str(enriched["query_split"]), max_queries, max_corpus))
    if "gt_corpus_guardrail" not in enriched:
        corpus_path = data_dir / f"{dataset}_corpus.json"
        if queries_path.exists() and corpus_path.exists():
            all_queries = load_json_list(queries_path)
            all_corpus = load_json_list(corpus_path)
            selected_queries = apply_query_controls(
                all_queries,
                query_split=str(enriched.get("requested_query_split") or "all"),
                max_queries=max_queries,
            )
            selected_corpus = apply_corpus_controls(
                all_corpus,
                max_corpus=max_corpus,
                queries=selected_queries,
                corpus_sampling=corpus_sampling,
            )
            enriched.update(gt_corpus_coverage(selected_queries, selected_corpus))
    enriched["metric_ks"] = enriched.get("metric_ks") or _metric_ks(enriched)
    enriched["comparable_group"] = comparable_group(enriched)
    enriched["notes"] = notes_for_row(enriched)
    return enriched


def _int_or_none(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _stringify_csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    return value


def load_metrics_rows(results_dir: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in sorted(results_dir.glob("*_metrics.json")):
        with path.open("r", encoding="utf-8") as f:
            row = json.load(f)
        if isinstance(row, MutableMapping):
            if str(row.get("method", "")) not in REQUIRED_METHODS:
                continue
            row["source_metrics_file"] = path.name
            rows.append(dict(row))
    return rows


def apply_comparison_guardrails(rows: Sequence[Mapping]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    output = [dict(row) for row in rows]
    for row in output:
        grouped[str(row["comparable_group"])].append(row)

    for group_rows in grouped.values():
        methods = {str(row.get("method", "")) for row in group_rows}
        has_required_methods = REQUIRED_METHODS.issubset(methods)
        for row in group_rows:
            notes = str(row.get("notes", ""))
            if not has_required_methods:
                extra = "Comparison group missing one or more BM25/dense/hybrid rows with the same query and corpus scope."
                notes = f"{notes} {extra}".strip()
            row["is_comparable"] = str(has_required_methods).lower()
            row["notes"] = notes
    return output


def write_comparison_csv(rows: Sequence[Mapping], output_path: Path) -> None:
    metric_keys = sorted({key for row in rows for key in row if any(str(key).startswith(prefix) for prefix in METRIC_PREFIXES)})
    fieldnames = [
        "dataset",
        "task_type",
        "method",
        "model",
        "scope",
        "query_split",
        "query_splits",
        "query_scope",
        "corpus_scope",
        "corpus_sampling",
        "comparable_group",
        "is_comparable",
        "num_queries",
        "num_skipped_no_gt",
        "num_queries_with_gt",
        "num_queries_with_gt_in_corpus",
        "num_queries_gt_missing_from_corpus",
        "num_gt_refs",
        "num_gt_refs_in_corpus",
        "num_gt_refs_missing_from_corpus",
        "gt_query_coverage",
        "gt_ref_coverage",
        "gt_corpus_guardrail",
        "num_total_queries",
        "num_query_candidates",
        "num_corpus_chunks",
        "num_total_corpus_chunks",
        "max_queries",
        "max_corpus",
        "top_k",
        "metric_ks",
        *metric_keys,
        "elapsed_sec",
        "notes",
        "source_metrics_file",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (str(r.get("dataset", "")), str(r.get("method", "")), str(r.get("model", "")))):
            writer.writerow({key: _stringify_csv_value(value) for key, value in row.items()})


def build_comparison(results_dir: Path, data_dir: Path, output_path: Path) -> List[Dict[str, object]]:
    rows = [enrich_metrics_row(row, data_dir) for row in load_metrics_rows(results_dir)]
    rows = apply_comparison_guardrails(rows)
    write_comparison_csv(rows, output_path)
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build retrieval baseline comparison table with protocol guardrails")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_DIR / "retrieval_baseline_comparison.csv",
    )
    args = parser.parse_args(argv)

    rows = build_comparison(args.results_dir, args.data_dir, args.output)
    print(f"Wrote {len(rows)} rows: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
