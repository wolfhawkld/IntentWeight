#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task51 experiment artifact validation framework.

The script audits already-generated experiment artifacts. It does not rerun
retrieval, reranking, or LLM generation. The checks are intentionally split
into three reviewer-facing layers:

- dimension: dataset, query, ranking, and artifact-shape consistency;
- statistics: paired CSV/JSON sanity, CI ordering, p-value ranges, and token
  ratio arithmetic;
- display: Markdown report readiness for paper-facing summaries.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "paper" / "experiments" / "task51_experiment_manifest.json"
DEFAULT_OUTPUT_PREFIX = ROOT / "paper" / "experiments" / "results" / "task51_experiment_validation_audit"


PAIRED_REQUIRED_COLUMNS = (
    "num_queries",
    "method_hit@10",
    "baseline_hit@10",
    "hit_delta_mean",
    "hit_delta_ci_low",
    "hit_delta_ci_high",
    "token_ratio",
    "token_saving_percent",
    "token_saving_ci_low",
    "token_saving_ci_high",
    "mcnemar_p_two_sided",
)

SUMMARY_REQUIRED_ANY = (
    ("hit@10", "method_hit@10"),
)


@dataclass
class Check:
    experiment: str
    role: str
    category: str
    item: str
    status: str
    source: str
    detail: str


class Audit:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def add(
        self,
        *,
        experiment: str,
        role: str,
        category: str,
        item: str,
        status: str,
        source: str,
        detail: str,
    ) -> None:
        self.checks.append(Check(experiment, role, category, item, status, source, detail))

    def pass_(self, experiment: str, role: str, category: str, item: str, source: str, detail: str) -> None:
        self.add(
            experiment=experiment,
            role=role,
            category=category,
            item=item,
            status="PASS",
            source=source,
            detail=detail,
        )

    def warn(self, experiment: str, role: str, category: str, item: str, source: str, detail: str) -> None:
        self.add(
            experiment=experiment,
            role=role,
            category=category,
            item=item,
            status="WARN",
            source=source,
            detail=detail,
        )

    def error(self, experiment: str, role: str, category: str, item: str, source: str, detail: str) -> None:
        self.add(
            experiment=experiment,
            role=role,
            category=category,
            item=item,
            status="ERROR",
            source=source,
            detail=detail,
        )


def resolve_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: str | Path) -> str:
    path = resolve_path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json_list(path: Path) -> list[Mapping[str, Any]]:
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON list, got {type(data).__name__}")
    if not all(isinstance(item, Mapping) for item in data):
        raise ValueError("expected every JSON list item to be an object")
    return list(data)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def query_id(record: Mapping[str, Any]) -> str:
    value = record.get("query_id") or record.get("id")
    if value is None:
        raise ValueError(f"query missing query_id/id: {record}")
    return str(value)


def chunk_id(record: Mapping[str, Any]) -> str:
    value = record.get("chunk_id") or record.get("id")
    if value is None:
        raise ValueError(f"corpus chunk missing chunk_id/id: {record}")
    return str(value)


def ground_truth_ids(record: Mapping[str, Any]) -> set[str]:
    value = record.get("ground_truth_chunk_ids", [])
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item) for item in value}
    return {str(value)}


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def is_numeric_column(column: str) -> bool:
    if column in {"seed", "scale"}:
        return False
    if column.endswith("_id") or column in {"run_id", "method_run_id", "baseline_run_id"}:
        return False
    numeric_markers = (
        "hit@",
        "recall@",
        "mrr@",
        "ndcg@",
        "tokens",
        "token_",
        "ratio",
        "percent",
        "delta",
        "ci_",
        "p_",
        "_p_",
        "num_",
        "_count",
        "wins",
        "losses",
        "ties",
        "queries",
    )
    return any(marker in column for marker in numeric_markers)


def is_ranking_list(value: Any) -> bool:
    return isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value)


def coerce_rankings(value: Mapping[str, Any]) -> dict[str, list[str]]:
    return {str(qid): [str(item) for item in ranking] for qid, ranking in value.items()}


def flatten_ranking_variants(data: Any, *, label: str) -> list[tuple[str, dict[str, list[str]]]]:
    if not isinstance(data, Mapping):
        raise ValueError("ranking artifact must be a JSON object")

    if data and all(is_ranking_list(value) for value in data.values()):
        return [(label, coerce_rankings(data))]

    variants: list[tuple[str, dict[str, list[str]]]] = []
    for key, value in data.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"unsupported ranking value under {key!r}")
        if value and all(is_ranking_list(item) for item in value.values()):
            variants.append((str(key), coerce_rankings(value)))
            continue
        if not value:
            variants.append((str(key), {}))
            continue
        for subkey, subvalue in value.items():
            if not isinstance(subvalue, Mapping) or not all(is_ranking_list(item) for item in subvalue.values()):
                raise ValueError(f"unsupported ranking value under {key!r}/{subkey!r}")
            variants.append((f"{key}:seed{subkey}", coerce_rankings(subvalue)))
    return variants


class ArtifactCache:
    def __init__(self) -> None:
        self.query_cache: dict[Path, list[Mapping[str, Any]]] = {}
        self.corpus_cache: dict[Path, list[Mapping[str, Any]]] = {}
        self.query_id_cache: dict[Path, set[str]] = {}
        self.chunk_id_cache: dict[Path, set[str]] = {}

    def queries(self, path: Path) -> list[Mapping[str, Any]]:
        if path not in self.query_cache:
            self.query_cache[path] = load_json_list(path)
        return self.query_cache[path]

    def corpus(self, path: Path) -> list[Mapping[str, Any]]:
        if path not in self.corpus_cache:
            self.corpus_cache[path] = load_json_list(path)
        return self.corpus_cache[path]

    def query_ids(self, path: Path) -> set[str]:
        if path not in self.query_id_cache:
            self.query_id_cache[path] = {query_id(item) for item in self.queries(path)}
        return self.query_id_cache[path]

    def chunk_ids(self, path: Path) -> set[str]:
        if path not in self.chunk_id_cache:
            self.chunk_id_cache[path] = {chunk_id(item) for item in self.corpus(path)}
        return self.chunk_id_cache[path]


def extract_expected_num_queries(experiment: Mapping[str, Any], json_payloads: Sequence[Any]) -> int | None:
    explicit = experiment.get("expected_num_queries")
    if explicit is not None:
        return int(explicit)
    for payload in json_payloads:
        if not isinstance(payload, Mapping):
            continue
        for key in ("test_query_count", "num_queries"):
            if key in payload and finite_float(payload[key]) is not None:
                return int(float(payload[key]))
        config = payload.get("config")
        if isinstance(config, Mapping):
            for key in ("test_query_count", "num_queries"):
                if key in config and finite_float(config[key]) is not None:
                    return int(float(config[key]))
    return None


def validate_dataset(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    dataset: Mapping[str, Any],
    cache: ArtifactCache,
) -> tuple[Path | None, Path | None]:
    queries_path = resolve_path(dataset["queries"]) if dataset.get("queries") else None
    corpus_path = resolve_path(dataset["corpus"]) if dataset.get("corpus") else None
    source = dataset.get("name", "")

    if queries_path is None:
        audit.warn(experiment, role, "dimension", "dataset_queries", source, "no query file configured")
        return None, corpus_path
    if not queries_path.exists():
        audit.error(experiment, role, "dimension", "dataset_queries", display_path(queries_path), "missing query file")
        return queries_path, corpus_path

    try:
        queries = cache.queries(queries_path)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "dataset_queries", display_path(queries_path), str(exc))
        return queries_path, corpus_path

    qids = [query_id(item) for item in queries]
    duplicate_qids = len(qids) - len(set(qids))
    queries_with_gt = sum(1 for item in queries if ground_truth_ids(item))
    expected_queries = dataset.get("expected_queries")
    if expected_queries is not None and len(queries) != int(expected_queries):
        audit.error(
            experiment,
            role,
            "dimension",
            "query_count",
            display_path(queries_path),
            f"expected={expected_queries}, actual={len(queries)}",
        )
    elif duplicate_qids:
        audit.error(
            experiment,
            role,
            "dimension",
            "query_ids",
            display_path(queries_path),
            f"duplicate_query_ids={duplicate_qids}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "queries",
            display_path(queries_path),
            f"queries={len(queries)}, queries_with_gt={queries_with_gt}",
        )

    if not dataset.get("check_corpus_refs", True):
        audit.pass_(
            experiment,
            role,
            "dimension",
            "corpus_ref_check",
            source or display_path(queries_path),
            "skipped by manifest for large or unavailable corpus",
        )
        return queries_path, corpus_path

    if corpus_path is None:
        audit.warn(experiment, role, "dimension", "corpus", source, "no corpus file configured")
        return queries_path, corpus_path
    if not corpus_path.exists():
        audit.error(experiment, role, "dimension", "corpus", display_path(corpus_path), "missing corpus file")
        return queries_path, corpus_path

    try:
        corpus = cache.corpus(corpus_path)
        cids = [chunk_id(item) for item in corpus]
    except Exception as exc:
        audit.error(experiment, role, "dimension", "corpus", display_path(corpus_path), str(exc))
        return queries_path, corpus_path

    duplicate_cids = len(cids) - len(set(cids))
    if duplicate_cids:
        audit.error(
            experiment,
            role,
            "dimension",
            "corpus_chunk_ids",
            display_path(corpus_path),
            f"duplicate_chunk_ids={duplicate_cids}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "corpus",
            display_path(corpus_path),
            f"chunks={len(corpus)}",
        )

    cid_set = set(cids)
    missing_gt_refs = 0
    for item in queries:
        missing_gt_refs += sum(1 for gt in ground_truth_ids(item) if gt not in cid_set)
    if missing_gt_refs:
        audit.error(
            experiment,
            role,
            "dimension",
            "ground_truth_refs",
            f"{display_path(queries_path)} -> {display_path(corpus_path)}",
            f"missing_gt_refs={missing_gt_refs}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "ground_truth_refs",
            f"{display_path(queries_path)} -> {display_path(corpus_path)}",
            "all configured GT refs resolve",
        )
    return queries_path, corpus_path


def validate_result_json(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    path: Path,
) -> Any | None:
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "dimension", "result_json", source, "missing file")
        return None
    try:
        payload = load_json(path)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "result_json", source, str(exc))
        return None

    if isinstance(payload, Mapping):
        keys = sorted(str(key) for key in payload.keys())
        audit.pass_(experiment, role, "dimension", "result_json", source, f"object_keys={len(keys)}")
        if "paired_rows" in payload:
            paired_rows = payload.get("paired_rows")
            if isinstance(paired_rows, list):
                audit.pass_(
                    experiment,
                    role,
                    "statistics",
                    "json_paired_rows",
                    source,
                    f"rows={len(paired_rows)}",
                )
                validate_paired_rows(
                    audit,
                    experiment=experiment,
                    role=role,
                    source=f"{source}:paired_rows",
                    rows=[row for row in paired_rows if isinstance(row, Mapping)],
                    expected_num_queries=None,
                    warn_missing_expected=False,
                )
            else:
                audit.error(experiment, role, "statistics", "json_paired_rows", source, "paired_rows is not a list")
    elif isinstance(payload, list):
        audit.pass_(experiment, role, "dimension", "result_json", source, f"list_rows={len(payload)}")
    else:
        audit.warn(experiment, role, "dimension", "result_json", source, f"type={type(payload).__name__}")
    return payload


def validate_summary_csv(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    path: Path,
    expected_num_queries: int | None,
) -> None:
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "dimension", "summary_csv", source, "missing file")
        return
    try:
        rows = load_csv_rows(path)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "summary_csv", source, str(exc))
        return
    if not rows:
        audit.error(experiment, role, "dimension", "summary_csv", source, "no rows")
        return

    columns = set(rows[0].keys())
    missing_any = [choices for choices in SUMMARY_REQUIRED_ANY if not any(choice in columns for choice in choices)]
    if missing_any:
        audit.warn(
            experiment,
            role,
            "dimension",
            "summary_columns",
            source,
            f"missing_any={missing_any}",
        )
    else:
        audit.pass_(experiment, role, "dimension", "summary_columns", source, f"columns={len(columns)}")

    numeric_errors = count_numeric_errors(rows)
    if numeric_errors:
        audit.error(experiment, role, "statistics", "summary_numeric_values", source, f"errors={numeric_errors}")
    else:
        audit.pass_(experiment, role, "statistics", "summary_numeric_values", source, f"rows={len(rows)}")

    check_num_queries_column(
        audit,
        experiment=experiment,
        role=role,
        source=source,
        rows=rows,
        expected_num_queries=expected_num_queries,
        category="dimension",
        item="summary_num_queries",
    )


def validate_artifact_csv(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    spec: Mapping[str, Any],
) -> None:
    """Validate heterogeneous analysis tables without weakening their schema checks."""
    path = resolve_path(spec["path"])
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "dimension", "artifact_csv", source, "missing file")
        return
    try:
        rows = load_csv_rows(path)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "artifact_csv", source, str(exc))
        return
    if not rows:
        audit.error(experiment, role, "dimension", "artifact_csv", source, "no rows")
        return

    actual_rows = len(rows)
    exact_rows = spec.get("exact_rows")
    min_rows = int(spec.get("min_rows", 1))
    if exact_rows is not None and actual_rows != int(exact_rows):
        audit.error(
            experiment,
            role,
            "dimension",
            "artifact_csv_rows",
            source,
            f"expected={exact_rows}, actual={actual_rows}",
        )
    elif actual_rows < min_rows:
        audit.error(
            experiment,
            role,
            "dimension",
            "artifact_csv_rows",
            source,
            f"minimum={min_rows}, actual={actual_rows}",
        )
    else:
        audit.pass_(experiment, role, "dimension", "artifact_csv_rows", source, f"rows={actual_rows}")

    columns = set(rows[0])
    required_columns = [str(column) for column in spec.get("required_columns", [])]
    missing = [column for column in required_columns if column not in columns]
    if missing:
        audit.error(experiment, role, "dimension", "artifact_csv_columns", source, f"missing={missing}")
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "artifact_csv_columns",
            source,
            f"required={len(required_columns)}, columns={len(columns)}",
        )

    numeric_columns = [str(column) for column in spec.get("numeric_columns", [])]
    allow_empty_numeric = {str(column) for column in spec.get("allow_empty_numeric", [])}
    numeric_errors = 0
    missing_numeric_columns = [column for column in numeric_columns if column not in columns]
    for row in rows:
        for column in numeric_columns:
            if column in row and str(row[column]).strip() == "" and column in allow_empty_numeric:
                continue
            if column in row and finite_float(row[column]) is None:
                numeric_errors += 1
    if missing_numeric_columns or numeric_errors:
        audit.error(
            experiment,
            role,
            "statistics",
            "artifact_csv_numeric",
            source,
            f"missing_columns={missing_numeric_columns}, invalid_values={numeric_errors}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "statistics",
            "artifact_csv_numeric",
            source,
            f"columns={len(numeric_columns)}, rows={actual_rows}",
        )

    unit_interval_columns = [str(column) for column in spec.get("unit_interval_columns", [])]
    range_errors = 0
    missing_range_columns = [column for column in unit_interval_columns if column not in columns]
    for row in rows:
        for column in unit_interval_columns:
            if str(row.get(column, "")).strip() == "" and column in allow_empty_numeric:
                continue
            value = finite_float(row.get(column))
            if value is None or not (0.0 <= value <= 1.0):
                range_errors += 1
    if missing_range_columns or range_errors:
        audit.error(
            experiment,
            role,
            "statistics",
            "artifact_csv_ranges",
            source,
            f"missing_columns={missing_range_columns}, errors={range_errors}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "statistics",
            "artifact_csv_ranges",
            source,
            f"unit_interval_columns={len(unit_interval_columns)}",
        )


def validate_jsonl_artifact(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    spec: Mapping[str, Any],
) -> None:
    """Stream and validate large answer/judgment artifacts."""
    path = resolve_path(spec["path"])
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "dimension", "jsonl_artifact", source, "missing file")
        return

    required_fields = [str(field) for field in spec.get("required_fields", [])]
    non_null_fields = [str(field) for field in spec.get("non_null_fields", [])]
    key_fields = [str(field) for field in spec.get("key_fields", [])]
    unique_keys = bool(spec.get("unique_keys", True))
    records = 0
    malformed = 0
    missing_fields = 0
    null_fields = 0
    duplicate_keys = 0
    seen: set[tuple[str, ...]] = set()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                records += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue
                if not isinstance(row, Mapping):
                    malformed += 1
                    continue
                missing_fields += sum(field not in row for field in required_fields)
                null_fields += sum(row.get(field) is None for field in non_null_fields)
                if key_fields:
                    key = tuple(str(row.get(field)) for field in key_fields)
                    if key in seen:
                        duplicate_keys += 1
                    seen.add(key)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "jsonl_artifact", source, str(exc))
        return

    expected = spec.get("exact_records")
    if expected is not None and records != int(expected):
        audit.error(
            experiment,
            role,
            "dimension",
            "jsonl_records",
            source,
            f"expected={expected}, actual={records}",
        )
    elif records < int(spec.get("min_records", 1)):
        audit.error(experiment, role, "dimension", "jsonl_records", source, f"actual={records}")
    else:
        audit.pass_(experiment, role, "dimension", "jsonl_records", source, f"records={records}")

    if malformed or missing_fields or null_fields:
        audit.error(
            experiment,
            role,
            "dimension",
            "jsonl_schema",
            source,
            f"malformed={malformed}, missing_fields={missing_fields}, null_fields={null_fields}",
        )
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "jsonl_schema",
            source,
            f"required_fields={len(required_fields)}, non_null_fields={len(non_null_fields)}",
        )

    expected_unique = spec.get("exact_unique_keys")
    if expected_unique is not None and len(seen) != int(expected_unique):
        audit.error(
            experiment,
            role,
            "dimension",
            "jsonl_keys",
            source,
            f"expected_unique={expected_unique}, actual_unique={len(seen)}",
        )
    elif unique_keys and duplicate_keys:
        audit.error(experiment, role, "dimension", "jsonl_keys", source, f"duplicate_keys={duplicate_keys}")
    else:
        audit.pass_(
            experiment,
            role,
            "dimension",
            "jsonl_keys",
            source,
            f"unique_keys={len(seen)}, duplicate_records={duplicate_keys}",
        )


def count_numeric_errors(rows: Sequence[Mapping[str, Any]]) -> int:
    errors = 0
    for row in rows:
        for column, value in row.items():
            if not is_numeric_column(str(column)):
                continue
            if str(value).strip() == "":
                continue
            if finite_float(value) is None:
                errors += 1
    return errors


def check_num_queries_column(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    source: str,
    rows: Sequence[Mapping[str, Any]],
    expected_num_queries: int | None,
    category: str,
    item: str,
    warn_if_missing: bool = True,
) -> None:
    if expected_num_queries is None:
        if warn_if_missing:
            audit.warn(experiment, role, category, item, source, "no expected_num_queries configured")
        return
    values = []
    for row in rows:
        value = finite_float(row.get("num_queries"))
        if value is not None:
            values.append(int(value))
    if not values:
        audit.warn(experiment, role, category, item, source, "no num_queries values found")
        return
    unexpected = sorted({value for value in values if value != expected_num_queries})
    if unexpected:
        audit.error(
            experiment,
            role,
            category,
            item,
            source,
            f"expected={expected_num_queries}, unexpected={unexpected}",
        )
    else:
        audit.pass_(experiment, role, category, item, source, f"num_queries={expected_num_queries}")


def validate_paired_csv(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    path: Path,
    expected_num_queries: int | None,
) -> None:
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "statistics", "paired_csv", source, "missing file")
        return
    try:
        rows = load_csv_rows(path)
    except Exception as exc:
        audit.error(experiment, role, "statistics", "paired_csv", source, str(exc))
        return
    if not rows:
        audit.error(experiment, role, "statistics", "paired_csv", source, "no rows")
        return

    columns = set(rows[0].keys())
    missing = [column for column in PAIRED_REQUIRED_COLUMNS if column not in columns]
    if missing:
        audit.error(experiment, role, "statistics", "paired_columns", source, f"missing={missing}")
    else:
        audit.pass_(experiment, role, "statistics", "paired_columns", source, f"columns={len(columns)}")

    validate_paired_rows(
        audit,
        experiment=experiment,
        role=role,
        source=source,
        rows=rows,
        expected_num_queries=expected_num_queries,
    )


def validate_paired_rows(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    source: str,
    rows: Sequence[Mapping[str, Any]],
    expected_num_queries: int | None,
    warn_missing_expected: bool = True,
) -> None:
    if not rows:
        audit.error(experiment, role, "statistics", "paired_rows", source, "no rows")
        return

    numeric_errors = count_numeric_errors(rows)
    if numeric_errors:
        audit.error(experiment, role, "statistics", "paired_numeric_values", source, f"errors={numeric_errors}")
    else:
        audit.pass_(experiment, role, "statistics", "paired_numeric_values", source, f"rows={len(rows)}")

    check_num_queries_column(
        audit,
        experiment=experiment,
        role=role,
        source=source,
        rows=rows,
        expected_num_queries=expected_num_queries,
        category="statistics",
        item="paired_num_queries",
        warn_if_missing=warn_missing_expected,
    )

    arithmetic_errors = 0
    range_errors = 0
    tolerance = 1e-6
    for index, row in enumerate(rows, start=1):
        method_hit = finite_float(row.get("method_hit@10"))
        baseline_hit = finite_float(row.get("baseline_hit@10"))
        hit_delta = finite_float(row.get("hit_delta_mean"))
        if method_hit is not None and baseline_hit is not None and hit_delta is not None:
            if abs((method_hit - baseline_hit) - hit_delta) > tolerance:
                arithmetic_errors += 1

        hit_lo = finite_float(row.get("hit_delta_ci_low"))
        hit_hi = finite_float(row.get("hit_delta_ci_high"))
        if hit_delta is not None and hit_lo is not None and hit_hi is not None:
            if not (hit_lo - tolerance <= hit_delta <= hit_hi + tolerance):
                range_errors += 1

        token_ratio = finite_float(row.get("token_ratio"))
        token_saving_percent = finite_float(row.get("token_saving_percent"))
        if token_ratio is not None and token_saving_percent is not None:
            expected_saving = (1.0 - token_ratio) * 100.0
            if abs(expected_saving - token_saving_percent) > 0.05:
                arithmetic_errors += 1

        saving_mean = finite_float(row.get("token_saving_mean"))
        saving_lo = finite_float(row.get("token_saving_ci_low"))
        saving_hi = finite_float(row.get("token_saving_ci_high"))
        if saving_mean is not None and saving_lo is not None and saving_hi is not None:
            if not (saving_lo - tolerance <= saving_mean <= saving_hi + tolerance):
                range_errors += 1

        for column in ("method_hit@10", "baseline_hit@10", "mcnemar_p_two_sided"):
            value = finite_float(row.get(column))
            if value is not None and not (0.0 - tolerance <= value <= 1.0 + tolerance):
                range_errors += 1

        num_queries = finite_float(row.get("num_queries"))
        method_only = finite_float(row.get("method_only_hits"))
        baseline_only = finite_float(row.get("baseline_only_hits"))
        if num_queries is not None and method_only is not None and baseline_only is not None:
            if method_only + baseline_only > num_queries + tolerance:
                arithmetic_errors += 1

        if index == len(rows):
            break

    if arithmetic_errors:
        audit.error(experiment, role, "statistics", "paired_arithmetic", source, f"errors={arithmetic_errors}")
    else:
        audit.pass_(experiment, role, "statistics", "paired_arithmetic", source, "hit deltas and token ratios consistent")

    if range_errors:
        audit.error(experiment, role, "statistics", "paired_ranges", source, f"errors={range_errors}")
    else:
        audit.pass_(experiment, role, "statistics", "paired_ranges", source, "CI and probability ranges consistent")


def validate_ranking_artifact(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    ranking_spec: Mapping[str, Any],
    queries_path: Path | None,
    corpus_path: Path | None,
    cache: ArtifactCache,
) -> None:
    path = resolve_path(ranking_spec["path"])
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "dimension", "ranking_artifact", source, "missing file")
        return
    try:
        variants = flatten_ranking_variants(load_json(path), label=path.stem)
    except Exception as exc:
        audit.error(experiment, role, "dimension", "ranking_artifact", source, str(exc))
        return

    if not variants:
        audit.error(experiment, role, "dimension", "ranking_variants", source, "no variants")
        return
    audit.pass_(experiment, role, "dimension", "ranking_variants", source, f"variants={len(variants)}")

    query_ids = cache.query_ids(queries_path) if queries_path and queries_path.exists() else None
    chunk_ids = None
    if corpus_path and corpus_path.exists() and ranking_spec.get("check_top_k_chunks") is not None:
        try:
            chunk_ids = cache.chunk_ids(corpus_path)
        except Exception as exc:
            audit.warn(experiment, role, "dimension", "ranking_chunk_refs", source, f"corpus unavailable: {exc}")

    expected_ranked = ranking_spec.get("expected_ranked_queries")
    min_len = int(ranking_spec.get("min_ranking_len", 1))
    top_k = int(ranking_spec.get("check_top_k_chunks", 0) or 0)

    ranked_count_errors = 0
    unknown_query_refs = 0
    short_variants = 0
    duplicate_ranking_refs = 0
    missing_chunk_refs = 0
    length_means: list[float] = []
    for _, rankings in variants:
        if expected_ranked is not None and len(rankings) != int(expected_ranked):
            ranked_count_errors += 1
        if query_ids is not None:
            unknown_query_refs += sum(1 for qid in rankings if qid not in query_ids)
        lengths = [len(items) for items in rankings.values()]
        if lengths:
            length_means.append(mean(lengths))
            if min(lengths) < min_len:
                short_variants += 1
        else:
            short_variants += 1
        for items in rankings.values():
            duplicate_ranking_refs += len(items) - len(set(items))
            if chunk_ids is not None and top_k > 0:
                missing_chunk_refs += sum(1 for item in items[:top_k] if item not in chunk_ids)

    if ranked_count_errors:
        audit.error(
            experiment,
            role,
            "dimension",
            "ranking_query_count",
            source,
            f"expected={expected_ranked}, variant_errors={ranked_count_errors}",
        )
    else:
        detail = f"expected={expected_ranked}, variants={len(variants)}" if expected_ranked is not None else f"variants={len(variants)}"
        audit.pass_(experiment, role, "dimension", "ranking_query_count", source, detail)

    if unknown_query_refs:
        audit.error(experiment, role, "dimension", "ranking_query_ids", source, f"unknown_query_ids={unknown_query_refs}")
    elif query_ids is not None:
        audit.pass_(experiment, role, "dimension", "ranking_query_ids", source, "all ranked query IDs resolve")

    if short_variants:
        audit.warn(experiment, role, "dimension", "ranking_lengths", source, f"variants_below_min_len={short_variants}")
    else:
        avg_len = mean(length_means) if length_means else 0.0
        audit.pass_(experiment, role, "dimension", "ranking_lengths", source, f"avg_variant_mean_len={avg_len:.2f}")

    if duplicate_ranking_refs:
        audit.warn(experiment, role, "dimension", "ranking_duplicate_refs", source, f"duplicate_refs={duplicate_ranking_refs}")
    else:
        audit.pass_(experiment, role, "dimension", "ranking_duplicate_refs", source, "no duplicate chunk IDs within rankings")

    if chunk_ids is not None and top_k > 0:
        if missing_chunk_refs:
            audit.error(experiment, role, "dimension", "ranking_chunk_refs", source, f"missing_top{top_k}_refs={missing_chunk_refs}")
        else:
            audit.pass_(experiment, role, "dimension", "ranking_chunk_refs", source, f"all top-{top_k} chunk refs resolve")


def validate_markdown_report(
    audit: Audit,
    *,
    experiment: str,
    role: str,
    path: Path,
) -> None:
    source = display_path(path)
    if not path.exists():
        audit.error(experiment, role, "display", "markdown_report", source, "missing file")
        return
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("#"):
        audit.warn(experiment, role, "display", "markdown_heading", source, "missing top-level heading")
    else:
        audit.pass_(experiment, role, "display", "markdown_heading", source, "top-level heading present")
    if "| ---" not in text and "|---" not in text:
        audit.warn(experiment, role, "display", "markdown_table", source, "no markdown table separator detected")
    else:
        audit.pass_(experiment, role, "display", "markdown_table", source, "table detected")
    if "token" not in text.lower():
        audit.warn(experiment, role, "display", "token_language", source, "token cost not mentioned")
    else:
        audit.pass_(experiment, role, "display", "token_language", source, "token language present")


def validate_experiment(
    audit: Audit,
    *,
    experiment: Mapping[str, Any],
    cache: ArtifactCache,
) -> None:
    experiment_id = str(experiment["id"])
    role = str(experiment.get("role", "unspecified"))

    json_payloads = []
    for raw_path in experiment.get("result_jsons", []):
        payload = validate_result_json(
            audit,
            experiment=experiment_id,
            role=role,
            path=resolve_path(raw_path),
        )
        if payload is not None:
            json_payloads.append(payload)

    expected_num_queries = extract_expected_num_queries(experiment, json_payloads)
    queries_path = None
    corpus_path = None
    dataset = experiment.get("dataset")
    if isinstance(dataset, Mapping):
        queries_path, corpus_path = validate_dataset(
            audit,
            experiment=experiment_id,
            role=role,
            dataset=dataset,
            cache=cache,
        )
    elif experiment.get("dataset_scope"):
        audit.pass_(
            experiment_id,
            role,
            "dimension",
            "dataset_scope",
            experiment_id,
            str(experiment["dataset_scope"]),
        )
    else:
        audit.warn(experiment_id, role, "dimension", "dataset", experiment_id, "no dataset block configured")

    for raw_path in experiment.get("summary_csvs", []):
        validate_summary_csv(
            audit,
            experiment=experiment_id,
            role=role,
            path=resolve_path(raw_path),
            expected_num_queries=expected_num_queries,
        )

    for raw_path in experiment.get("paired_csvs", []):
        validate_paired_csv(
            audit,
            experiment=experiment_id,
            role=role,
            path=resolve_path(raw_path),
            expected_num_queries=expected_num_queries,
        )

    for artifact_spec in experiment.get("artifact_csvs", []):
        if not isinstance(artifact_spec, Mapping) or not artifact_spec.get("path"):
            audit.error(experiment_id, role, "dimension", "artifact_csv", experiment_id, "invalid CSV spec")
            continue
        validate_artifact_csv(
            audit,
            experiment=experiment_id,
            role=role,
            spec=artifact_spec,
        )

    for jsonl_spec in experiment.get("jsonl_artifacts", []):
        if not isinstance(jsonl_spec, Mapping) or not jsonl_spec.get("path"):
            audit.error(experiment_id, role, "dimension", "jsonl_artifact", experiment_id, "invalid JSONL spec")
            continue
        validate_jsonl_artifact(
            audit,
            experiment=experiment_id,
            role=role,
            spec=jsonl_spec,
        )

    for ranking_spec in experiment.get("ranking_artifacts", []):
        if not isinstance(ranking_spec, Mapping):
            audit.error(experiment_id, role, "dimension", "ranking_artifact", experiment_id, "ranking spec is not an object")
            continue
        validate_ranking_artifact(
            audit,
            experiment=experiment_id,
            role=role,
            ranking_spec=ranking_spec,
            queries_path=queries_path,
            corpus_path=corpus_path,
            cache=cache,
        )

    for raw_path in experiment.get("markdown_reports", []):
        validate_markdown_report(
            audit,
            experiment=experiment_id,
            role=role,
            path=resolve_path(raw_path),
        )


def write_csv_report(path: Path, checks: Sequence[Check]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["experiment", "role", "category", "item", "status", "source", "detail"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for check in checks:
            writer.writerow(asdict(check))


def summarize_checks(checks: Sequence[Check]) -> dict[str, Any]:
    status_counts = Counter(check.status for check in checks)
    by_experiment: dict[str, Counter[str]] = defaultdict(Counter)
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    for check in checks:
        by_experiment[check.experiment][check.status] += 1
        by_category[check.category][check.status] += 1
    return {
        "status_counts": dict(sorted(status_counts.items())),
        "by_experiment": {key: dict(sorted(value.items())) for key, value in sorted(by_experiment.items())},
        "by_category": {key: dict(sorted(value.items())) for key, value in sorted(by_category.items())},
    }


def write_json_report(path: Path, manifest_path: Path, checks: Sequence[Check]) -> None:
    payload = {
        "manifest": display_path(manifest_path),
        "summary": summarize_checks(checks),
        "checks": [asdict(check) for check in checks],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def status_for_counts(counts: Mapping[str, int]) -> str:
    if counts.get("ERROR", 0):
        return "ERROR"
    if counts.get("WARN", 0):
        return "WARN"
    return "PASS"


def write_markdown_report(path: Path, manifest_path: Path, checks: Sequence[Check]) -> None:
    summary = summarize_checks(checks)
    by_experiment = summary["by_experiment"]
    by_category = summary["by_category"]
    lines = [
        "# Task51 Experiment Validation Audit",
        "",
        f"- Manifest: `{display_path(manifest_path)}`",
        f"- Total checks: {len(checks)}",
        f"- PASS: {summary['status_counts'].get('PASS', 0)}",
        f"- WARN: {summary['status_counts'].get('WARN', 0)}",
        f"- ERROR: {summary['status_counts'].get('ERROR', 0)}",
        "",
        "## Experiment Status",
        "",
        "| experiment | status | pass | warn | error |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for experiment, counts in by_experiment.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    experiment,
                    status_for_counts(counts),
                    str(counts.get("PASS", 0)),
                    str(counts.get("WARN", 0)),
                    str(counts.get("ERROR", 0)),
                ]
            )
            + " |"
        )

    lines.extend([
        "",
        "## Category Status",
        "",
        "| category | status | pass | warn | error |",
        "| --- | --- | ---: | ---: | ---: |",
    ])
    for category, counts in by_category.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    category,
                    status_for_counts(counts),
                    str(counts.get("PASS", 0)),
                    str(counts.get("WARN", 0)),
                    str(counts.get("ERROR", 0)),
                ]
            )
            + " |"
        )

    notable = [check for check in checks if check.status in {"ERROR", "WARN"}]
    lines.extend([
        "",
        "## Warnings And Errors",
        "",
    ])
    if notable:
        lines.append("| experiment | category | status | item | source | detail |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for check in notable:
            lines.append(
                "| "
                + " | ".join(
                    [
                        check.experiment,
                        check.category,
                        check.status,
                        check.item,
                        f"`{check.source}`",
                        check.detail.replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No warnings or errors.")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Dimension checks cover dataset/query shape, ranking variants, query coverage, and chunk-reference resolution where configured.",
        "- JSONL checks stream answer and judgment records while enforcing counts, schemas, and configured key cardinalities.",
        "- Statistics checks cover paired-result arithmetic, confidence interval ordering, p-value ranges, token-ratio consistency, and configured heterogeneous analysis tables.",
        "- Display checks cover paper-facing Markdown reports; they do not judge visual aesthetics.",
        "- Large corpus checks can skip full corpus-reference scans by manifest to keep this audit lightweight.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def filter_experiments(experiments: Iterable[Mapping[str, Any]], selected: set[str] | None) -> list[Mapping[str, Any]]:
    experiments = list(experiments)
    if selected is None:
        return experiments
    return [experiment for experiment in experiments if str(experiment.get("id")) in selected]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate paper experiment artifacts from a manifest")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--experiments",
        default="",
        help="Comma-separated experiment IDs to validate; default validates all manifest entries",
    )
    parser.add_argument("--list-experiments", action="store_true")
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit nonzero when warnings are present; by default only errors fail",
    )
    args = parser.parse_args(argv)

    manifest_path = resolve_path(args.manifest)
    manifest = load_json(manifest_path)
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a JSON object")
    experiments = manifest.get("experiments", [])
    if not isinstance(experiments, list):
        raise ValueError("manifest experiments must be a list")

    if args.list_experiments:
        for experiment in experiments:
            print(experiment.get("id"))
        return 0

    selected = {item.strip() for item in args.experiments.split(",") if item.strip()} or None
    selected_experiments = filter_experiments(experiments, selected)
    if not selected_experiments:
        raise ValueError("no experiments selected")

    audit = Audit()
    cache = ArtifactCache()
    for experiment in selected_experiments:
        if not isinstance(experiment, Mapping):
            raise ValueError("experiment entry must be an object")
        validate_experiment(audit, experiment=experiment, cache=cache)

    output_prefix = resolve_path(args.output_prefix)
    write_csv_report(output_prefix.with_suffix(".csv"), audit.checks)
    write_json_report(output_prefix.with_suffix(".json"), manifest_path, audit.checks)
    write_markdown_report(output_prefix.with_suffix(".md"), manifest_path, audit.checks)

    summary = summarize_checks(audit.checks)
    print(json.dumps(summary["status_counts"], sort_keys=True))
    errors = summary["status_counts"].get("ERROR", 0)
    warnings = summary["status_counts"].get("WARN", 0)
    if errors:
        return 1
    if args.fail_on_warn and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
