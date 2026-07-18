#!/usr/bin/env python3
"""Audit reconstructed external-dataset checkpoints against tracked evidence."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DATA_DIR = EXPERIMENT_DIR / "data" / "processed"
LOCAL_ROOT = EXPERIMENT_DIR / "data" / "task78_handoff" / "external_dense_results"
RESULTS_DIR = EXPERIMENT_DIR / "results"
OUTPUT_PREFIX = RESULTS_DIR / "task78_gpu_revalidation" / "task78_external_checkpoints"

METRIC_PREFIXES = ("hit@", "recall@", "evidence_recall@", "mrr@", "ndcg@")


@dataclass(frozen=True)
class Case:
    dataset: str
    candidate_dir: str
    reference_dir: str


CASES = (
    Case("pubmedqa", "pubmedqa_cpu", "task69_4_pubmedqa_dense"),
    Case("emanual_deduplicated", "emanual_cpu", "task69_4_emanual_dedup_dense"),
    Case("covidqa", "covidqa_cpu64", "task69_5_covidqa_dense"),
)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def metric_values(payload: Mapping[str, object]) -> dict[str, float]:
    return {
        key: float(value)
        for key, value in payload.items()
        if key.startswith(METRIC_PREFIXES) and isinstance(value, (int, float))
    }


def embedding_score_diagnostics(
    dataset: str,
    candidate_metrics: Mapping[str, object],
    changed_query_ids: Sequence[str],
    candidate_rankings: Mapping[str, Sequence[str]],
    reference_rankings: Mapping[str, Sequence[str]],
) -> list[dict[str, object]]:
    if not changed_query_ids:
        return []
    corpus = load_json(DATA_DIR / f"{dataset}_corpus.json")
    queries = load_json(DATA_DIR / f"{dataset}_queries.json")
    corpus_rows = {str(item["chunk_id"]): index for index, item in enumerate(corpus)}
    query_rows = {str(item["query_id"]): index for index, item in enumerate(queries)}
    query_by_id = {str(item["query_id"]): item for item in queries}
    corpus_embeddings = np.load(
        Path(str(candidate_metrics["corpus_embedding_cache_path"])),
        mmap_mode="r",
        allow_pickle=False,
    )
    query_embeddings = np.load(
        Path(str(candidate_metrics["query_embedding_cache_path"])),
        mmap_mode="r",
        allow_pickle=False,
    )

    diagnostics = []
    for query_id in changed_query_ids:
        current = list(candidate_rankings[query_id])
        historical = list(reference_rankings[query_id])
        changed_ids = sorted(set(current).symmetric_difference(historical))
        query_embedding = np.asarray(query_embeddings[query_rows[query_id]])
        scores = {
            chunk_id: float(query_embedding @ np.asarray(corpus_embeddings[corpus_rows[chunk_id]]))
            for chunk_id in changed_ids
        }
        gt_ids = {str(value) for value in query_by_id[query_id].get("ground_truth_chunk_ids", [])}
        diagnostics.append({
            "query_id": query_id,
            "query": str(query_by_id[query_id].get("text", "")),
            "candidate_only": sorted(set(current) - set(historical)),
            "reference_only": sorted(set(historical) - set(current)),
            "changed_scores_under_candidate_embeddings": scores,
            "changed_score_span": max(scores.values()) - min(scores.values()) if scores else 0.0,
            "changed_ground_truth_ids": sorted(set(changed_ids).intersection(gt_ids)),
            "candidate_hit": bool(set(current).intersection(gt_ids)),
            "reference_hit": bool(set(historical).intersection(gt_ids)),
        })
    return diagnostics


def audit_case(case: Case) -> dict[str, object]:
    candidate_root = LOCAL_ROOT / case.candidate_dir
    reference_root = RESULTS_DIR / case.reference_dir
    candidate_metrics_path = candidate_root / f"dense_{case.dataset}_metrics.json"
    candidate_rankings_path = candidate_root / f"dense_{case.dataset}_rankings.json"
    reference_metrics_path = reference_root / f"dense_{case.dataset}_metrics.json"
    reference_rankings_path = reference_root / f"dense_{case.dataset}_rankings.json"
    paths = (
        candidate_metrics_path,
        candidate_rankings_path,
        reference_metrics_path,
        reference_rankings_path,
    )
    missing = [repo_relative(path) for path in paths if not path.is_file()]
    if missing:
        return {"dataset": case.dataset, "status": "MISSING", "missing": missing}

    candidate_metrics = load_json(candidate_metrics_path)
    reference_metrics = load_json(reference_metrics_path)
    candidate_rankings = load_json(candidate_rankings_path)
    reference_rankings = load_json(reference_rankings_path)
    shared_queries = sorted(set(candidate_rankings).intersection(reference_rankings))
    ordered_matches = sum(candidate_rankings[qid] == reference_rankings[qid] for qid in shared_queries)
    member_matches = sum(
        set(candidate_rankings[qid]) == set(reference_rankings[qid]) for qid in shared_queries
    )
    changed_members = [
        qid for qid in shared_queries
        if set(candidate_rankings[qid]) != set(reference_rankings[qid])
    ]
    candidate_values = metric_values(candidate_metrics)
    reference_values = metric_values(reference_metrics)
    metric_deltas = {
        key: candidate_values[key] - reference_values[key]
        for key in sorted(set(candidate_values).intersection(reference_values))
    }
    metrics_exact = all(delta == 0.0 for delta in metric_deltas.values())
    rankings_exact = (
        len(shared_queries) == len(candidate_rankings) == len(reference_rankings)
        and ordered_matches == len(shared_queries)
    )
    status = "EXACT" if metrics_exact and rankings_exact else "HISTORICAL_RANKINGS_REQUIRED"
    return {
        "dataset": case.dataset,
        "status": status,
        "candidate_metrics": repo_relative(candidate_metrics_path),
        "reference_metrics": repo_relative(reference_metrics_path),
        "candidate_rankings": repo_relative(candidate_rankings_path),
        "reference_rankings": repo_relative(reference_rankings_path),
        "candidate_rankings_sha256": sha256_file(candidate_rankings_path),
        "reference_rankings_sha256": sha256_file(reference_rankings_path),
        "query_count": len(shared_queries),
        "top10_member_matches": member_matches,
        "top10_ordered_matches": ordered_matches,
        "metrics_exact": metrics_exact,
        "metric_deltas": metric_deltas,
        "changed_member_query_count": len(changed_members),
        "changed_member_diagnostics": embedding_score_diagnostics(
            case.dataset,
            candidate_metrics,
            changed_members,
            candidate_rankings,
            reference_rankings,
        ),
        "checkpoint_embedding_paths": {
            "corpus": repo_relative(Path(str(candidate_metrics["corpus_embedding_cache_path"]))),
            "queries": repo_relative(Path(str(candidate_metrics["query_embedding_cache_path"]))),
        },
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    lines = [
        "# Task78 External Checkpoint Audit",
        "",
        "The tracked Task69 rankings remain the authoritative paper evidence. Rebuilt",
        "embeddings are accepted as exact checkpoints only when both rankings and all",
        "published metrics are identical.",
        "",
        "| Dataset | Status | Top-10 members | Top-10 order | Metrics exact |",
        "|---|---|---:|---:|---:|",
    ]
    for case in payload["cases"]:
        if case["status"] == "MISSING":
            lines.append(f"| {case['dataset']} | MISSING | - | - | - |")
            continue
        count = int(case["query_count"])
        lines.append(
            f"| {case['dataset']} | {case['status']} | "
            f"{int(case['top10_member_matches'])}/{count} | "
            f"{int(case['top10_ordered_matches'])}/{count} | "
            f"{'yes' if case['metrics_exact'] else 'no'} |"
        )
    lines.extend([
        "",
        "A `HISTORICAL_RANKINGS_REQUIRED` row is not substituted into the manuscript.",
        "Its rebuilt embeddings are useful for numerical reruns, while the tracked",
        "historical rankings and downstream route outputs must be transferred for exact",
        "paper-result regeneration.",
    ])
    for case in payload["cases"]:
        if case.get("status") != "HISTORICAL_RANKINGS_REQUIRED":
            continue
        diagnostics = case.get("changed_member_diagnostics", [])
        spans = [float(item["changed_score_span"]) for item in diagnostics]
        hit_changes = sum(
            bool(item["candidate_hit"]) != bool(item["reference_hit"])
            for item in diagnostics
        )
        lines.extend([
            "",
            f"For `{case['dataset']}`, {len(diagnostics)} query top-10 member sets",
            f"change; the largest changed-candidate score span under the rebuilt",
            f"embeddings is {max(spans, default=0.0):.3g}, and {hit_changes} query",
            "changes Hit@10. This is a numerical tie boundary, but it is not exact",
            "paper-result equivalence.",
        ])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    cases = [audit_case(case) for case in CASES]
    payload = {
        "status": "PASS_WITH_HISTORICAL_BOUNDARY" if all(
            case["status"] != "MISSING" for case in cases
        ) else "MISSING",
        "cases": cases,
    }
    OUTPUT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_PREFIX.with_suffix(".json")
    markdown_path = OUTPUT_PREFIX.with_suffix(".md")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "json": str(json_path),
        "markdown": str(markdown_path),
    }, indent=2))
    return 0 if payload["status"] != "MISSING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
