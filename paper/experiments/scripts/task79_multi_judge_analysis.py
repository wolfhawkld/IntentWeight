#!/usr/bin/env python3
"""Offline Task79 four-endpoint, three-judge statistical analysis.

No model endpoint is called. Raw judge scores are kept model-specific; only
within-judge paired effects and a three-judge majority on complete intersections
are reported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "paper" / "experiments" / "results"
DEFAULT_INPUT_DIR = RESULTS_DIR / "task79_llmlingua2_downstream_evaluation"
DEFAULT_COMPRESSOR_DIR = RESULTS_DIR / "task79_llmlingua2_matched_compressor"
DEFAULT_OUTPUT_PREFIX = RESULTS_DIR / "task79_llmlingua2_multi_judge_analysis"

JUDGES = ("deepseek-v4-flash", "glm-5.2", "minimax-m3")
DENSE_REFERENCE = "dense_sent_mmr_r0.85_l0.70"
INTENT_REFERENCE = "intentweight_sent_mmr_r0.85_l0.70_seed19"
DENSE_LLMLINGUA = "dense_llmlingua2_matched_sent_mmr"
INTENT_LLMLINGUA = "intentroute_llmlingua2_matched_sent_mmr_seed19"
METHODS = (DENSE_REFERENCE, INTENT_REFERENCE, DENSE_LLMLINGUA, INTENT_LLMLINGUA)
COMPARISONS = (
    (
        "IntentRoute+LLMLingua-2 vs Dense+LLMLingua-2",
        DENSE_LLMLINGUA,
        INTENT_LLMLINGUA,
    ),
    ("Dense: LLMLingua-2 vs Sentence-MMR", DENSE_REFERENCE, DENSE_LLMLINGUA),
    (
        "IntentRoute: LLMLingua-2 vs Sentence-MMR",
        INTENT_REFERENCE,
        INTENT_LLMLINGUA,
    ),
    ("IntentRoute+Sentence-MMR vs Dense+Sentence-MMR", DENSE_REFERENCE, INTENT_REFERENCE),
)
SCORE_FIELDS = (
    "correctness_score",
    "faithfulness_score",
    "relevance_score",
    "citation_support_score",
)
BOOLEAN_FIELDS = ("is_correct", "is_faithful", "citations_supported", "unsupported_claims")
REQUIRED_FIELDS = set(SCORE_FIELDS) | set(BOOLEAN_FIELDS) | {
    "insufficient_context_appropriate",
    "rationale",
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def answer_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("query_id")), str(row.get("method_label"))


def judgment_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("query_id")),
        str(row.get("method_label")),
        str(row.get("judge_model")),
    )


def valid_judgment(row: Mapping[str, Any]) -> bool:
    parsed = row.get("judge_json")
    if not isinstance(parsed, Mapping) or not REQUIRED_FIELDS.issubset(parsed):
        return False
    try:
        scores_ok = all(1 <= int(parsed[field]) <= 5 for field in SCORE_FIELDS)
    except (TypeError, ValueError):
        return False
    booleans_ok = all(isinstance(parsed[field], bool) for field in BOOLEAN_FIELDS)
    return scores_ok and booleans_ok and isinstance(parsed["insufficient_context_appropriate"], bool)


def failure_code(row: Mapping[str, Any]) -> str:
    if row.get("provider_error") or row.get("error"):
        return "provider_rejection"
    message = str(row.get("error_message") or "")
    for code in ("SensitiveContentDetected", "AuthenticationError", "RateLimitError"):
        if code in message:
            return code
    if row.get("import_failure"):
        return str(row["import_failure"])
    if not isinstance(row.get("judge_json"), Mapping):
        return "invalid_or_empty_judge_output"
    return str(row.get("error_type") or "unknown_failure")


def exact_mcnemar_p(baseline_only: int, challenger_only: int) -> float:
    discordant = baseline_only + challenger_only
    if discordant == 0:
        return 1.0
    tail = min(baseline_only, challenger_only)
    probability = sum(math.comb(discordant, value) for value in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def bootstrap_mean_ci(
    delta: np.ndarray,
    *,
    samples: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(delta), size=(samples, len(delta)))
    values = np.mean(delta[indices], axis=1)
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def bootstrap_saving_ci(
    baseline: np.ndarray,
    challenger: np.ndarray,
    *,
    samples: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(baseline), size=(samples, len(baseline)))
    baseline_means = np.mean(baseline[indices], axis=1)
    challenger_means = np.mean(challenger[indices], axis=1)
    savings = 100.0 * (baseline_means - challenger_means) / baseline_means
    low, high = np.quantile(savings, [0.025, 0.975])
    return float(low), float(high)


def cohen_kappa(left: Sequence[bool], right: Sequence[bool]) -> tuple[float, float]:
    if len(left) != len(right) or not left:
        raise ValueError("Cohen kappa requires aligned non-empty inputs")
    a = np.asarray(left, dtype=bool)
    b = np.asarray(right, dtype=bool)
    observed = float(np.mean(a == b))
    p_a = float(np.mean(a))
    p_b = float(np.mean(b))
    expected = p_a * p_b + (1.0 - p_a) * (1.0 - p_b)
    if math.isclose(expected, 1.0):
        return observed, 1.0 if math.isclose(observed, 1.0) else 0.0
    return observed, float((observed - expected) / (1.0 - expected))


def method_lookup(sample_records: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    lookup: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in sample_records:
        labels = tuple(str(method["method_label"]) for method in record["methods"])
        if labels != METHODS:
            raise ValueError(f"Unexpected method order for {record['query_id']}: {labels}")
        for method in record["methods"]:
            key = (str(record["query_id"]), str(method["method_label"]))
            if key in lookup:
                raise ValueError(f"Duplicate sample-record method key: {key}")
            lookup[key] = method
    return lookup


def judge_method_rows(
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for judge in JUDGES:
        for method in METHODS:
            judgments = [
                row
                for (query_id, method_label, judge_model), row in judgments_by_key.items()
                if method_label == method and judge_model == judge
            ]
            if not judgments:
                continue
            output: dict[str, Any] = {
                "judge_model": judge,
                "method_label": method,
                "valid_judgments": len(judgments),
            }
            for field in SCORE_FIELDS:
                output[f"mean_{field}"] = float(
                    np.mean([int(row["judge_json"][field]) for row in judgments])
                )
            for field in BOOLEAN_FIELDS:
                output[f"{field}_rate"] = float(
                    np.mean([bool(row["judge_json"][field]) for row in judgments])
                )
            rows.append(output)
    return rows


def paired_effect(
    query_ids: Sequence[str],
    baseline: str,
    challenger: str,
    answer_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    boolean_values: Mapping[tuple[str, str], Mapping[str, bool]],
    score_values: Mapping[tuple[str, str], Mapping[str, float]],
    *,
    scope: str,
    comparison: str,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    baseline_tokens = np.asarray(
        [float(answer_by_key[(query_id, baseline)]["context_tokens"]) for query_id in query_ids]
    )
    challenger_tokens = np.asarray(
        [float(answer_by_key[(query_id, challenger)]["context_tokens"]) for query_id in query_ids]
    )
    token_low, token_high = bootstrap_saving_ci(
        baseline_tokens,
        challenger_tokens,
        samples=bootstrap_samples,
        seed=seed + 1,
    )
    row: dict[str, Any] = {
        "judge_scope": scope,
        "comparison": comparison,
        "baseline": baseline,
        "challenger": challenger,
        "paired_queries": len(query_ids),
        "baseline_context_tokens_mean": float(np.mean(baseline_tokens)),
        "challenger_context_tokens_mean": float(np.mean(challenger_tokens)),
        "context_token_saving_percent": 100.0
        * float((np.mean(baseline_tokens) - np.mean(challenger_tokens)) / np.mean(baseline_tokens)),
        "context_token_saving_ci_low_percent": token_low,
        "context_token_saving_ci_high_percent": token_high,
    }
    baseline_prompt_tokens = np.asarray(
        [float(usage_input_tokens(answer_by_key[(query_id, baseline)])) for query_id in query_ids]
    )
    challenger_prompt_tokens = np.asarray(
        [float(usage_input_tokens(answer_by_key[(query_id, challenger)])) for query_id in query_ids]
    )
    if np.all(baseline_prompt_tokens > 0) and np.all(challenger_prompt_tokens > 0):
        prompt_low, prompt_high = bootstrap_saving_ci(
            baseline_prompt_tokens,
            challenger_prompt_tokens,
            samples=bootstrap_samples,
            seed=seed + 2,
        )
        row.update(
            {
                "baseline_prompt_tokens_mean": float(np.mean(baseline_prompt_tokens)),
                "challenger_prompt_tokens_mean": float(np.mean(challenger_prompt_tokens)),
                "prompt_token_saving_percent": 100.0
                * float(
                    (np.mean(baseline_prompt_tokens) - np.mean(challenger_prompt_tokens))
                    / np.mean(baseline_prompt_tokens)
                ),
                "prompt_token_saving_ci_low_percent": prompt_low,
                "prompt_token_saving_ci_high_percent": prompt_high,
            }
        )

    for index, field in enumerate(("is_correct", "is_faithful", "citations_supported")):
        baseline_values = np.asarray(
            [float(boolean_values[(query_id, baseline)][field]) for query_id in query_ids]
        )
        challenger_values = np.asarray(
            [float(boolean_values[(query_id, challenger)][field]) for query_id in query_ids]
        )
        delta = challenger_values - baseline_values
        low, high = bootstrap_mean_ci(
            delta,
            samples=bootstrap_samples,
            seed=seed + 10 + index,
        )
        baseline_only = int(np.sum((baseline_values == 1) & (challenger_values == 0)))
        challenger_only = int(np.sum((baseline_values == 0) & (challenger_values == 1)))
        row[f"baseline_{field}_rate"] = float(np.mean(baseline_values))
        row[f"challenger_{field}_rate"] = float(np.mean(challenger_values))
        row[f"{field}_delta_pp"] = 100.0 * float(np.mean(delta))
        row[f"{field}_delta_ci_low_pp"] = 100.0 * low
        row[f"{field}_delta_ci_high_pp"] = 100.0 * high
        row[f"{field}_mcnemar_exact_p"] = exact_mcnemar_p(baseline_only, challenger_only)
        row[f"{field}_baseline_only"] = baseline_only
        row[f"{field}_challenger_only"] = challenger_only

    for index, field in enumerate(SCORE_FIELDS):
        baseline_values = np.asarray(
            [float(score_values[(query_id, baseline)][field]) for query_id in query_ids]
        )
        challenger_values = np.asarray(
            [float(score_values[(query_id, challenger)][field]) for query_id in query_ids]
        )
        delta = challenger_values - baseline_values
        low, high = bootstrap_mean_ci(
            delta,
            samples=bootstrap_samples,
            seed=seed + 20 + index,
        )
        row[f"{field}_delta"] = float(np.mean(delta))
        row[f"{field}_delta_ci_low"] = low
        row[f"{field}_delta_ci_high"] = high
    return row


def paired_rows(
    answer_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for judge_index, judge in enumerate(JUDGES):
        for comparison_index, (label, baseline, challenger) in enumerate(COMPARISONS):
            query_ids = sorted(
                query_id
                for query_id, method in answer_by_key
                if method == baseline
                and (query_id, challenger) in answer_by_key
                and (query_id, baseline, judge) in judgments_by_key
                and (query_id, challenger, judge) in judgments_by_key
            )
            if not query_ids:
                continue
            booleans = {
                (query_id, method): {
                    field: bool(judgments_by_key[(query_id, method, judge)]["judge_json"][field])
                    for field in BOOLEAN_FIELDS
                }
                for query_id in query_ids
                for method in (baseline, challenger)
            }
            scores = {
                (query_id, method): {
                    field: float(judgments_by_key[(query_id, method, judge)]["judge_json"][field])
                    for field in SCORE_FIELDS
                }
                for query_id in query_ids
                for method in (baseline, challenger)
            }
            rows.append(
                paired_effect(
                    query_ids,
                    baseline,
                    challenger,
                    answer_by_key,
                    booleans,
                    scores,
                    scope=judge,
                    comparison=label,
                    bootstrap_samples=bootstrap_samples,
                    seed=790_000 + judge_index * 100 + comparison_index * 30,
                )
            )

    for comparison_index, (label, baseline, challenger) in enumerate(COMPARISONS):
        query_ids = sorted(
            query_id
            for query_id, method in answer_by_key
            if method == baseline
            and (query_id, challenger) in answer_by_key
            and all((query_id, baseline, judge) in judgments_by_key for judge in JUDGES)
            and all((query_id, challenger, judge) in judgments_by_key for judge in JUDGES)
        )
        if not query_ids:
            continue
        booleans: dict[tuple[str, str], dict[str, bool]] = {}
        scores: dict[tuple[str, str], dict[str, float]] = {}
        for query_id in query_ids:
            for method in (baseline, challenger):
                booleans[(query_id, method)] = {
                    field: sum(
                        bool(judgments_by_key[(query_id, method, judge)]["judge_json"][field])
                        for judge in JUDGES
                    )
                    >= 2
                    for field in BOOLEAN_FIELDS
                }
                scores[(query_id, method)] = {
                    field: float(
                        np.median(
                            [
                                int(judgments_by_key[(query_id, method, judge)]["judge_json"][field])
                                for judge in JUDGES
                            ]
                        )
                    )
                    for field in SCORE_FIELDS
                }
        rows.append(
            paired_effect(
                query_ids,
                baseline,
                challenger,
                answer_by_key,
                booleans,
                scores,
                scope="three_judge_majority",
                comparison=label,
                bootstrap_samples=bootstrap_samples,
                seed=799_000 + comparison_index * 30,
            )
        )
    return rows


def agreement_rows(
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in ("all_methods", *METHODS):
        shared = sorted(
            {
                (query_id, method_label)
                for query_id, method_label, judge in judgments_by_key
                if (method == "all_methods" or method_label == method)
                and all((query_id, method_label, model) in judgments_by_key for model in JUDGES)
            }
        )
        if not shared:
            continue
        for field in ("is_correct", "is_faithful", "citations_supported"):
            for left_index, left in enumerate(JUDGES):
                for right in JUDGES[left_index + 1 :]:
                    left_values = [
                        bool(judgments_by_key[(*key, left)]["judge_json"][field])
                        for key in shared
                    ]
                    right_values = [
                        bool(judgments_by_key[(*key, right)]["judge_json"][field])
                        for key in shared
                    ]
                    agreement, kappa = cohen_kappa(left_values, right_values)
                    rows.append(
                        {
                            "method_scope": method,
                            "field": field,
                            "judge_left": left,
                            "judge_right": right,
                            "n": len(shared),
                            "raw_agreement": agreement,
                            "cohen_kappa": kappa,
                            "left_positive_rate": float(np.mean(left_values)),
                            "right_positive_rate": float(np.mean(right_values)),
                        }
                    )
    return rows


def majority_method_rows(
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in METHODS:
        query_ids = sorted(
            query_id
            for query_id in {key[0] for key in judgments_by_key if key[1] == method}
            if all((query_id, method, judge) in judgments_by_key for judge in JUDGES)
        )
        if not query_ids:
            continue
        row: dict[str, Any] = {"method_label": method, "shared_queries": len(query_ids)}
        for field in ("is_correct", "is_faithful", "citations_supported"):
            votes = np.asarray(
                [
                    [
                        bool(judgments_by_key[(query_id, method, judge)]["judge_json"][field])
                        for judge in JUDGES
                    ]
                    for query_id in query_ids
                ],
                dtype=bool,
            )
            row[f"majority_{field}_rate"] = float(np.mean(np.sum(votes, axis=1) >= 2))
            row[f"unanimous_{field}_rate"] = float(np.mean(np.all(votes == votes[:, [0]], axis=1)))
        rows.append(row)
    return rows


def answer_text(row: Mapping[str, Any]) -> str:
    parsed = row.get("answer_json")
    if isinstance(parsed, Mapping) and parsed.get("answer"):
        return str(parsed["answer"])
    return str(row.get("answer_text") or "")


def usage_input_tokens(row: Mapping[str, Any]) -> int:
    usage = row.get("generation_usage")
    if not isinstance(usage, Mapping):
        return 0
    for key in ("prompt_tokens", "input_tokens"):
        value = usage.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return 0


def numeric_tokens(text: str) -> set[str]:
    return set(re.findall(r"(?<!\w)[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:%|\w+)?", text.lower()))


def qualitative_candidates(
    sample_records: Sequence[Mapping[str, Any]],
    answer_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sample_by_query = {str(row["query_id"]): row for row in sample_records}
    candidates: list[dict[str, Any]] = []
    for comparison, baseline, challenger in COMPARISONS:
        for query_id in sorted(sample_by_query):
            if (query_id, baseline) not in answer_by_key or (query_id, challenger) not in answer_by_key:
                continue
            categories: list[str] = []
            complete = all(
                (query_id, method, judge) in judgments_by_key
                for method in (baseline, challenger)
                for judge in JUDGES
            )
            baseline_majority: dict[str, bool] = {}
            challenger_majority: dict[str, bool] = {}
            disagreement = False
            if complete:
                for field in ("is_correct", "is_faithful", "citations_supported"):
                    baseline_votes = [
                        bool(judgments_by_key[(query_id, baseline, judge)]["judge_json"][field])
                        for judge in JUDGES
                    ]
                    challenger_votes = [
                        bool(judgments_by_key[(query_id, challenger, judge)]["judge_json"][field])
                        for judge in JUDGES
                    ]
                    baseline_majority[field] = sum(baseline_votes) >= 2
                    challenger_majority[field] = sum(challenger_votes) >= 2
                    disagreement = disagreement or len(set(baseline_votes)) > 1 or len(set(challenger_votes)) > 1
                if baseline_majority["is_correct"] and not challenger_majority["is_correct"]:
                    categories.append("answer_bearing_evidence_deletion_candidate")
                if not baseline_majority["is_correct"] and challenger_majority["is_correct"]:
                    categories.append("answer_quality_recovery_candidate")
                if baseline_majority["citations_supported"] and not challenger_majority["citations_supported"]:
                    categories.append("citation_loss_candidate")
                if disagreement:
                    categories.append("judge_disagreement")

            baseline_numbers = numeric_tokens(answer_text(answer_by_key[(query_id, baseline)]))
            challenger_numbers = numeric_tokens(answer_text(answer_by_key[(query_id, challenger)]))
            if baseline_numbers != challenger_numbers and (
                "answer_bearing_evidence_deletion_candidate" in categories
                or "citation_loss_candidate" in categories
            ):
                categories.append("semantic_or_numeric_drift_candidate")

            method = next(
                item
                for item in sample_by_query[query_id]["methods"]
                if str(item["method_label"]) == challenger
            )
            if not bool(method["hit_at_10"]) and (
                not complete or not challenger_majority.get("is_correct", False)
            ):
                categories.append("upstream_source_pool_insufficiency_candidate")
            if challenger in (DENSE_LLMLINGUA, INTENT_LLMLINGUA):
                context = method["context"]
                has_empty_context = any(
                    not str(item.get("text") or "").strip() for item in context
                )
                if int(method["context_tokens"]) == 0 or has_empty_context:
                    categories.append("compressor_empty_output")

            if not categories:
                continue
            candidates.append(
                {
                    "query_id": query_id,
                    "comparison": comparison,
                    "baseline": baseline,
                    "challenger": challenger,
                    "categories": sorted(set(categories)),
                    "three_judge_complete": complete,
                    "baseline_context_tokens": int(answer_by_key[(query_id, baseline)]["context_tokens"]),
                    "challenger_context_tokens": int(answer_by_key[(query_id, challenger)]["context_tokens"]),
                    "baseline_answer": answer_text(answer_by_key[(query_id, baseline)]),
                    "challenger_answer": answer_text(answer_by_key[(query_id, challenger)]),
                    "baseline_numbers": sorted(baseline_numbers),
                    "challenger_numbers": sorted(challenger_numbers),
                }
            )
    return candidates


def markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> list[str]:
    def render(value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    output = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    output.extend(
        "| " + " | ".join(render(row.get(column, "")) for column in columns) + " |"
        for row in rows
    )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--compressor-dir", type=Path, default=DEFAULT_COMPRESSOR_DIR)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    sample_path = args.input_dir / "sample_records.jsonl"
    answer_path = args.input_dir / "answers.jsonl"
    judgment_path = args.input_dir / "judgments.jsonl"
    judgment_failure_path = args.input_dir / "judgment_failures.jsonl"
    external_failure_path = args.input_dir / "external_judgment_failures.jsonl"
    sample_records = read_jsonl(sample_path)
    answers = read_jsonl(answer_path)
    judgments = read_jsonl(judgment_path)
    failure_attempts = [
        *read_jsonl(judgment_failure_path),
        *read_jsonl(external_failure_path),
    ]
    compressor_summary = read_json(args.compressor_dir / "compression_summary.json")

    if len(sample_records) != 300:
        raise ValueError(f"Expected 300 fixed sample records, got {len(sample_records)}")
    methods_by_key = method_lookup(sample_records)
    answer_by_key = {answer_key(row): row for row in answers}
    if len(answer_by_key) != len(answers):
        raise ValueError("Duplicate query-method keys in answers.jsonl")
    expected_answer_keys = set(methods_by_key)
    if set(answer_by_key) != expected_answer_keys:
        missing = expected_answer_keys - set(answer_by_key)
        extra = set(answer_by_key) - expected_answer_keys
        raise ValueError(f"Expected 1,200 answers; missing={len(missing)}, extra={len(extra)}")
    for key, answer in answer_by_key.items():
        method = methods_by_key[key]
        if int(answer["context_tokens"]) != int(method["context_tokens"]):
            raise ValueError(f"Answer/sample context-token mismatch: {key}")
        if list(answer["context_chunk_ids"]) != list(method["context_chunk_ids"]):
            raise ValueError(f"Answer/sample context-ID mismatch: {key}")

    valid = [row for row in judgments if valid_judgment(row)]
    judgments_by_key = {judgment_key(row): row for row in valid}
    if len(judgments_by_key) != len(valid):
        raise ValueError("Duplicate valid judgment keys")
    if any(key[:2] not in answer_by_key for key in judgments_by_key):
        raise ValueError("Judgment references a non-Task79 answer")

    expected_judgment_keys = {
        (query_id, method, judge)
        for query_id, method in expected_answer_keys
        for judge in JUDGES
    }
    missing_judgments = sorted(expected_judgment_keys - set(judgments_by_key))
    failures_by_key: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for failure in failure_attempts:
        key = judgment_key(failure)
        failures_by_key.setdefault(key, []).append(failure)
    missingness_rows = []
    for key in missing_judgments:
        attempts = failures_by_key.get(key, [])
        missingness_rows.append(
            {
                "query_id": key[0],
                "method_label": key[1],
                "judge_model": key[2],
                "failure_attempts": len(attempts),
                "failure_codes": ",".join(
                    sorted({failure_code(row) for row in attempts})
                )
                if attempts
                else "unrecorded",
            }
        )
    recovered_failure_keys = sorted(set(failures_by_key).intersection(judgments_by_key))
    judge_rows = judge_method_rows(judgments_by_key)
    comparisons = paired_rows(
        answer_by_key,
        judgments_by_key,
        bootstrap_samples=args.bootstrap_samples,
    )
    agreements = agreement_rows(judgments_by_key)
    majority_rows = majority_method_rows(judgments_by_key)
    candidates = qualitative_candidates(
        sample_records,
        answer_by_key,
        judgments_by_key,
    )

    context_rows: list[dict[str, Any]] = []
    for method in METHODS:
        method_query_ids = sorted({key[0] for key in methods_by_key if key[1] == method})
        values = [methods_by_key[(query_id, method)] for query_id in method_query_ids]
        prompt_tokens = [usage_input_tokens(answer_by_key[(query_id, method)]) for query_id in method_query_ids]
        output: dict[str, Any] = {
            "method_label": method,
            "queries": len(values),
            "mean_context_tokens": mean(int(value["context_tokens"]) for value in values),
            "total_context_tokens": sum(int(value["context_tokens"]) for value in values),
            "mean_prompt_tokens": mean(prompt_tokens) if all(value > 0 for value in prompt_tokens) else None,
            "total_prompt_tokens": sum(prompt_tokens) if all(value > 0 for value in prompt_tokens) else None,
            "hit_at_10": mean(bool(value["hit_at_10"]) for value in values),
            "evidence_recall_at_10": mean(float(value["evidence_recall_at_10"]) for value in values),
        }
        if method in (DENSE_LLMLINGUA, INTENT_LLMLINGUA):
            output["mean_target_error_tokens"] = mean(int(value["target_error_tokens"]) for value in values)
            output["mean_compression_seconds"] = mean(float(value["compression_seconds"]) for value in values)
        context_rows.append(output)

    missing_new_endpoint_judgments = [
        key for key in missing_judgments if key[1] in (DENSE_LLMLINGUA, INTENT_LLMLINGUA)
    ]
    status = (
        "COMPLETE_THREE_JUDGE_ANALYSIS"
        if not missing_judgments
        else "COMPLETE_PRIMARY_THREE_JUDGE_WITH_RECORDED_LEGACY_MISSINGNESS"
        if not missing_new_endpoint_judgments
        else "COMPLETE_ANSWERS_PARTIAL_JUDGE_COVERAGE"
    )
    result = {
        "status": status,
        "answer_count": len(answers),
        "valid_judgment_count": len(valid),
        "expected_judgment_count": len(expected_judgment_keys),
        "missing_judgment_count": len(missing_judgments),
        "missing_new_endpoint_judgment_count": len(missing_new_endpoint_judgments),
        "primary_comparison_complete": not missing_new_endpoint_judgments,
        "coverage_by_judge": {
            judge: sum(key[2] == judge for key in judgments_by_key)
            for judge in JUDGES
        },
        "missing_by_judge": dict(Counter(key[2] for key in missing_judgments)),
        "bootstrap_samples": args.bootstrap_samples,
        "source_sha256": {
            "sample_records.jsonl": sha256_file(sample_path),
            "answers.jsonl": sha256_file(answer_path),
            "judgments.jsonl": sha256_file(judgment_path),
            **(
                {"judgment_failures.jsonl": sha256_file(judgment_failure_path)}
                if judgment_failure_path.exists()
                else {}
            ),
            **(
                {"external_judgment_failures.jsonl": sha256_file(external_failure_path)}
                if external_failure_path.exists()
                else {}
            ),
        },
        "compressor_provenance": {
            "protocol_signature": compressor_summary["protocol_signature"],
            "device": compressor_summary["environment"]["device_name"],
            "peak_allocated_vram_bytes": compressor_summary["environment"]["peak_allocated_vram_bytes"],
            "peak_reserved_vram_bytes": compressor_summary["environment"]["peak_reserved_vram_bytes"],
            "endpoints": compressor_summary["endpoints"],
        },
        "context_summary": context_rows,
        "judge_method_summary": judge_rows,
        "paired_comparisons": comparisons,
        "pairwise_agreement": agreements,
        "majority_method_summary": majority_rows,
        "judgment_failure_attempt_count": len(failure_attempts),
        "recovered_failure_key_count": len(recovered_failure_keys),
        "recovered_failure_keys": [
            {"query_id": key[0], "method_label": key[1], "judge_model": key[2]}
            for key in recovered_failure_keys
        ],
        "missing_judgments": missingness_rows,
        "qualitative_candidate_count": len(candidates),
        "qualitative_category_counts": dict(
            Counter(category for row in candidates for category in row["categories"])
        ),
        "interpretation_boundaries": [
            "Raw score scales are not pooled across judge models.",
            "Three-judge majority uses only query-method keys valid for all three judges.",
            "Missing provider judgments are reported and never imputed.",
            "Automated failure categories are review candidates, not adjudicated causal labels.",
            "LLMLingua-2 evidence is a compressor-complementarity test and does not validate route geometry.",
            "Cross-compressor prompt-token deltas include per-unit serialization overhead because "
            "Sentence-MMR emits sentence units while LLMLingua-2 retains chunk units; matched "
            "context_tokens are the primary compressor-cost measure.",
        ],
    }

    prefix = args.output_prefix
    write_json(prefix.with_suffix(".json"), result)
    write_csv(prefix.with_suffix(".contexts.csv"), context_rows)
    write_csv(prefix.with_suffix(".judges.csv"), judge_rows)
    write_csv(prefix.with_suffix(".paired.csv"), comparisons)
    write_csv(prefix.with_suffix(".agreement.csv"), agreements)
    write_csv(prefix.with_suffix(".majority.csv"), majority_rows)
    write_jsonl(prefix.with_suffix(".qualitative_candidates.jsonl"), candidates)
    write_csv(
        prefix.with_suffix(".missingness.csv"),
        result["missing_judgments"],
    )

    primary_rows = [
        row
        for row in comparisons
        if row["comparison"] == "IntentRoute+LLMLingua-2 vs Dense+LLMLingua-2"
    ]
    lines = [
        "# Task79 LLMLingua-2 Multi-Judge Analysis",
        "",
        f"Status: **{status}**",
        "",
        f"- Answers: `{len(answers)}/1200`",
        f"- Valid judgments: `{len(valid)}/{len(expected_judgment_keys)}`",
        f"- Missing judgments (not imputed): `{len(missing_judgments)}`",
        f"- Logged failure attempts: `{len(failure_attempts)}`; recovered keys: "
        f"`{len(recovered_failure_keys)}`",
        "- Compressor peak allocated VRAM: "
        f"`{compressor_summary['environment']['peak_allocated_vram_bytes'] / 2**30:.3f} GiB`",
        "",
        "## Context Endpoints",
        "",
        *markdown_table(
            context_rows,
            (
                "method_label",
                "queries",
                "mean_context_tokens",
                "mean_prompt_tokens",
                "hit_at_10",
                "mean_target_error_tokens",
            ),
        ),
        "",
        "## Primary Paired Comparison",
        "",
        *markdown_table(
            primary_rows,
            (
                "judge_scope",
                "paired_queries",
                "is_correct_delta_pp",
                "is_correct_delta_ci_low_pp",
                "is_correct_delta_ci_high_pp",
                "is_correct_mcnemar_exact_p",
                "is_faithful_delta_pp",
                "citations_supported_delta_pp",
                "context_token_saving_percent",
                "prompt_token_saving_percent",
            ),
        ),
        "",
        "## Boundaries",
        "",
        "- Judge scores are reported separately; raw score scales are not pooled.",
        "- Majority results use only complete three-judge pairs; missing outputs are not imputed.",
        "- Qualitative categories are candidates for manual review, not automatic causal findings.",
        "- This tests route/compressor complementarity, not a geometry-to-compression causal path.",
        "- Cross-compressor prompt-token deltas include sentence-versus-chunk header overhead; "
        "the matched context-token measure remains primary.",
        "",
    ]
    prefix.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "answers": len(answers),
                "valid_judgments": len(valid),
                "missing_judgments": len(missing_judgments),
                "output_prefix": str(prefix),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
