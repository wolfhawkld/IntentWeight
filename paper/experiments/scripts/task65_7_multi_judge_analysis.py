#!/usr/bin/env python3
"""Analyze Task63 answers with multiple independent LLM judges.

The script is offline: it reads existing answer/judgment artifacts and never
calls an LLM endpoint. Cross-judge statistics use only the intersection of
valid query-method keys. Model-specific summaries retain each judge's full
valid coverage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


DEFAULT_INPUT_DIR = Path("paper/experiments/results/task63_downstream_llm_evaluation")
DEFAULT_OUTPUT_PREFIX = Path("paper/experiments/results/task65_7_multi_judge_analysis")
JUDGES = ("deepseek-v4-flash", "glm-5.2", "minimax-m3")
SCORE_FIELDS = (
    "correctness_score",
    "faithfulness_score",
    "relevance_score",
    "citation_support_score",
)
PRIMARY_BOOLEAN_FIELDS = ("is_correct", "is_faithful", "citations_supported", "unsupported_claims")
REQUIRED_FIELDS = set(SCORE_FIELDS) | set(PRIMARY_BOOLEAN_FIELDS) | {
    "insufficient_context_appropriate",
    "rationale",
}
PAIRED_COMPARISONS = (
    ("BGE IntentRoute vs BGE dense", "bge_dense_top10", "bge_intentweight_positive_seed19"),
    ("E5 IntentRoute vs E5 dense", "e5_dense_top10", "e5_intentweight_full_seed19"),
    (
        "IntentRoute+SentMMR vs Dense+SentMMR",
        "dense_sent_mmr_r0.85_l0.70",
        "intentweight_sent_mmr_r0.85_l0.70_seed19",
    ),
)


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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def judgment_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return str(row.get("query_id")), str(row.get("method_label")), str(row.get("judge_model"))


def answer_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("query_id")), str(row.get("method_label"))


def is_valid_judgment(row: Mapping[str, Any]) -> bool:
    parsed = row.get("judge_json")
    if not isinstance(parsed, Mapping) or not REQUIRED_FIELDS.issubset(parsed):
        return False
    try:
        scores_valid = all(1 <= int(parsed[field]) <= 5 for field in SCORE_FIELDS)
    except (TypeError, ValueError):
        return False
    booleans_valid = all(isinstance(parsed[field], bool) for field in PRIMARY_BOOLEAN_FIELDS)
    return scores_valid and booleans_valid and isinstance(parsed["insufficient_context_appropriate"], bool)


def exact_mcnemar_p(baseline_only: int, challenger_only: int) -> float:
    discordant = baseline_only + challenger_only
    if discordant == 0:
        return 1.0
    tail = min(baseline_only, challenger_only)
    probability = sum(math.comb(discordant, value) for value in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def bootstrap_mean_ci(delta: np.ndarray, rng: np.random.Generator, samples: int) -> tuple[float, float]:
    indices = rng.integers(0, len(delta), size=(samples, len(delta)))
    values = np.mean(delta[indices], axis=1)
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def bootstrap_saving_ci(
    baseline: np.ndarray,
    challenger: np.ndarray,
    rng: np.random.Generator,
    samples: int,
) -> tuple[float, float]:
    indices = rng.integers(0, len(baseline), size=(samples, len(baseline)))
    baseline_means = np.mean(baseline[indices], axis=1)
    challenger_means = np.mean(challenger[indices], axis=1)
    saving = 100.0 * (baseline_means - challenger_means) / baseline_means
    low, high = np.quantile(saving, [0.025, 0.975])
    return float(low), float(high)


def cohen_kappa(left: Sequence[bool], right: Sequence[bool]) -> tuple[float, float]:
    if len(left) != len(right) or not left:
        raise ValueError("Cohen kappa requires two non-empty aligned sequences")
    a = np.asarray(left, dtype=bool)
    b = np.asarray(right, dtype=bool)
    observed = float(np.mean(a == b))
    p_a = float(np.mean(a))
    p_b = float(np.mean(b))
    expected = p_a * p_b + (1.0 - p_a) * (1.0 - p_b)
    if math.isclose(expected, 1.0):
        kappa = 1.0 if math.isclose(observed, 1.0) else 0.0
    else:
        kappa = (observed - expected) / (1.0 - expected)
    return observed, float(kappa)


def score_and_boolean_summary(rows: Sequence[Mapping[str, Any]], *, scope: str) -> dict[str, Any]:
    result: dict[str, Any] = {"scope": scope, "n": len(rows), "scores": {}, "booleans": {}}
    for field in SCORE_FIELDS:
        values = [int(row["judge_json"][field]) for row in rows]
        counts = Counter(values)
        result["scores"][field] = {
            "mean": float(np.mean(values)),
            "distribution": {str(score): counts[score] for score in range(1, 6)},
            "percent": {str(score): 100.0 * counts[score] / len(values) for score in range(1, 6)},
        }
    for field in (*PRIMARY_BOOLEAN_FIELDS, "insufficient_context_appropriate"):
        values = [bool(row["judge_json"][field]) for row in rows]
        true_count = sum(values)
        result["booleans"][field] = {
            "true": true_count,
            "false": len(values) - true_count,
            "true_rate": true_count / len(values),
        }
    return result


def flatten_judge_summary(model: str, summary: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {"judge_model": model, "scope": summary["scope"], "n": summary["n"]}
    for field in SCORE_FIELDS:
        row[f"{field}_mean"] = summary["scores"][field]["mean"]
        for score in range(1, 6):
            row[f"{field}_score{score}_percent"] = summary["scores"][field]["percent"][str(score)]
    for field in (*PRIMARY_BOOLEAN_FIELDS, "insufficient_context_appropriate"):
        row[f"{field}_rate"] = summary["booleans"][field]["true_rate"]
    return row


def paired_rows(
    answers_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for judge_index, judge in enumerate(JUDGES):
        for comparison_index, (label, baseline, challenger) in enumerate(PAIRED_COMPARISONS):
            qids = sorted(
                qid
                for qid, method in answers_by_key
                if method == baseline
                and (qid, challenger) in answers_by_key
                and (qid, baseline, judge) in judgments_by_key
                and (qid, challenger, judge) in judgments_by_key
            )
            baseline_correct = np.asarray(
                [float(judgments_by_key[(qid, baseline, judge)]["judge_json"]["is_correct"]) for qid in qids]
            )
            challenger_correct = np.asarray(
                [float(judgments_by_key[(qid, challenger, judge)]["judge_json"]["is_correct"]) for qid in qids]
            )
            baseline_faithful = np.asarray(
                [float(judgments_by_key[(qid, baseline, judge)]["judge_json"]["is_faithful"]) for qid in qids]
            )
            challenger_faithful = np.asarray(
                [float(judgments_by_key[(qid, challenger, judge)]["judge_json"]["is_faithful"]) for qid in qids]
            )
            baseline_tokens = np.asarray([float(answers_by_key[(qid, baseline)]["context_tokens"]) for qid in qids])
            challenger_tokens = np.asarray([float(answers_by_key[(qid, challenger)]["context_tokens"]) for qid in qids])
            rng = np.random.default_rng(657_000 + judge_index * 100 + comparison_index)
            correct_low, correct_high = bootstrap_mean_ci(
                challenger_correct - baseline_correct, rng, bootstrap_samples
            )
            faithful_low, faithful_high = bootstrap_mean_ci(
                challenger_faithful - baseline_faithful, rng, bootstrap_samples
            )
            token_low, token_high = bootstrap_saving_ci(
                baseline_tokens,
                challenger_tokens,
                np.random.default_rng(657_050 + judge_index * 100 + comparison_index),
                bootstrap_samples,
            )
            baseline_only = int(np.sum((baseline_correct == 1) & (challenger_correct == 0)))
            challenger_only = int(np.sum((baseline_correct == 0) & (challenger_correct == 1)))
            baseline_only_faithful = int(np.sum((baseline_faithful == 1) & (challenger_faithful == 0)))
            challenger_only_faithful = int(np.sum((baseline_faithful == 0) & (challenger_faithful == 1)))
            rows.append(
                {
                    "judge_model": judge,
                    "comparison": label,
                    "baseline": baseline,
                    "challenger": challenger,
                    "paired_queries": len(qids),
                    "baseline_correct_rate": float(np.mean(baseline_correct)),
                    "challenger_correct_rate": float(np.mean(challenger_correct)),
                    "correct_delta_pp": 100.0 * float(np.mean(challenger_correct - baseline_correct)),
                    "correct_delta_ci_low_pp": 100.0 * correct_low,
                    "correct_delta_ci_high_pp": 100.0 * correct_high,
                    "mcnemar_exact_p": exact_mcnemar_p(baseline_only, challenger_only),
                    "baseline_only_correct": baseline_only,
                    "challenger_only_correct": challenger_only,
                    "faithful_delta_pp": 100.0 * float(np.mean(challenger_faithful - baseline_faithful)),
                    "faithful_delta_ci_low_pp": 100.0 * faithful_low,
                    "faithful_delta_ci_high_pp": 100.0 * faithful_high,
                    "faithful_mcnemar_exact_p": exact_mcnemar_p(
                        baseline_only_faithful, challenger_only_faithful
                    ),
                    "baseline_only_faithful": baseline_only_faithful,
                    "challenger_only_faithful": challenger_only_faithful,
                    "context_token_saving_percent": 100.0
                    * float((np.mean(baseline_tokens) - np.mean(challenger_tokens)) / np.mean(baseline_tokens)),
                    "context_token_saving_ci_low_percent": token_low,
                    "context_token_saving_ci_high_percent": token_high,
                }
            )

    for comparison_index, (label, baseline, challenger) in enumerate(PAIRED_COMPARISONS):
        qids = sorted(
            qid
            for qid, method in answers_by_key
            if method == baseline
            and (qid, challenger) in answers_by_key
            and all((qid, baseline, judge) in judgments_by_key for judge in JUDGES)
            and all((qid, challenger, judge) in judgments_by_key for judge in JUDGES)
        )

        def majority(field: str, method: str) -> np.ndarray:
            return np.asarray(
                [
                    float(
                        sum(bool(judgments_by_key[(qid, method, judge)]["judge_json"][field]) for judge in JUDGES)
                        >= 2
                    )
                    for qid in qids
                ]
            )

        baseline_correct = majority("is_correct", baseline)
        challenger_correct = majority("is_correct", challenger)
        baseline_faithful = majority("is_faithful", baseline)
        challenger_faithful = majority("is_faithful", challenger)
        baseline_tokens = np.asarray([float(answers_by_key[(qid, baseline)]["context_tokens"]) for qid in qids])
        challenger_tokens = np.asarray([float(answers_by_key[(qid, challenger)]["context_tokens"]) for qid in qids])
        rng = np.random.default_rng(657_900 + comparison_index)
        correct_low, correct_high = bootstrap_mean_ci(
            challenger_correct - baseline_correct, rng, bootstrap_samples
        )
        faithful_low, faithful_high = bootstrap_mean_ci(
            challenger_faithful - baseline_faithful, rng, bootstrap_samples
        )
        token_low, token_high = bootstrap_saving_ci(
            baseline_tokens,
            challenger_tokens,
            np.random.default_rng(657_950 + comparison_index),
            bootstrap_samples,
        )
        baseline_only = int(np.sum((baseline_correct == 1) & (challenger_correct == 0)))
        challenger_only = int(np.sum((baseline_correct == 0) & (challenger_correct == 1)))
        baseline_only_faithful = int(np.sum((baseline_faithful == 1) & (challenger_faithful == 0)))
        challenger_only_faithful = int(np.sum((baseline_faithful == 0) & (challenger_faithful == 1)))
        rows.append(
            {
                "judge_model": "three_judge_majority",
                "comparison": label,
                "baseline": baseline,
                "challenger": challenger,
                "paired_queries": len(qids),
                "baseline_correct_rate": float(np.mean(baseline_correct)),
                "challenger_correct_rate": float(np.mean(challenger_correct)),
                "correct_delta_pp": 100.0 * float(np.mean(challenger_correct - baseline_correct)),
                "correct_delta_ci_low_pp": 100.0 * correct_low,
                "correct_delta_ci_high_pp": 100.0 * correct_high,
                "mcnemar_exact_p": exact_mcnemar_p(baseline_only, challenger_only),
                "baseline_only_correct": baseline_only,
                "challenger_only_correct": challenger_only,
                "faithful_delta_pp": 100.0 * float(np.mean(challenger_faithful - baseline_faithful)),
                "faithful_delta_ci_low_pp": 100.0 * faithful_low,
                "faithful_delta_ci_high_pp": 100.0 * faithful_high,
                "faithful_mcnemar_exact_p": exact_mcnemar_p(
                    baseline_only_faithful, challenger_only_faithful
                ),
                "baseline_only_faithful": baseline_only_faithful,
                "challenger_only_faithful": challenger_only_faithful,
                "context_token_saving_percent": 100.0
                * float((np.mean(baseline_tokens) - np.mean(challenger_tokens)) / np.mean(baseline_tokens)),
                "context_token_saving_ci_low_percent": token_low,
                "context_token_saving_ci_high_percent": token_high,
            }
        )
    return rows


def agreement_rows(
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
    shared_keys: Sequence[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairwise: list[dict[str, Any]] = []
    consensus: list[dict[str, Any]] = []
    for field in ("is_correct", "is_faithful"):
        for left_index, left in enumerate(JUDGES):
            for right in JUDGES[left_index + 1 :]:
                left_values = [bool(judgments_by_key[(*key, left)]["judge_json"][field]) for key in shared_keys]
                right_values = [bool(judgments_by_key[(*key, right)]["judge_json"][field]) for key in shared_keys]
                agreement, kappa = cohen_kappa(left_values, right_values)
                pairwise.append(
                    {
                        "field": field,
                        "judge_left": left,
                        "judge_right": right,
                        "n": len(shared_keys),
                        "raw_agreement": agreement,
                        "cohen_kappa": kappa,
                        "left_positive_rate": float(np.mean(left_values)),
                        "right_positive_rate": float(np.mean(right_values)),
                    }
                )
        votes = np.asarray(
            [
                [bool(judgments_by_key[(*key, judge)]["judge_json"][field]) for judge in JUDGES]
                for key in shared_keys
            ],
            dtype=bool,
        )
        consensus.append(
            {
                "field": field,
                "n": len(shared_keys),
                "unanimous_rate": float(np.mean(np.all(votes == votes[:, [0]], axis=1))),
                "majority_positive_rate": float(np.mean(np.sum(votes, axis=1) >= 2)),
                "all_positive_rate": float(np.mean(np.all(votes, axis=1))),
                "all_negative_rate": float(np.mean(np.all(~votes, axis=1))),
            }
        )
    return pairwise, consensus


def majority_method_rows(
    judgments_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
    shared_keys: Sequence[tuple[str, str]],
) -> list[dict[str, Any]]:
    by_method: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in shared_keys:
        by_method[key[1]].append(key)
    rows: list[dict[str, Any]] = []
    for method, keys in sorted(by_method.items()):
        row: dict[str, Any] = {"method_label": method, "shared_judgments": len(keys)}
        for field in ("is_correct", "is_faithful"):
            majority = []
            unanimous = []
            for key in keys:
                values = [bool(judgments_by_key[(*key, judge)]["judge_json"][field]) for judge in JUDGES]
                majority.append(sum(values) >= 2)
                unanimous.append(values.count(values[0]) == len(values))
            row[f"majority_{field}_rate"] = float(np.mean(majority))
            row[f"unanimous_{field}_rate"] = float(np.mean(unanimous))
        rows.append(row)
    return rows


def failure_code(row: Mapping[str, Any]) -> str:
    message = str(row.get("error_message") or "")
    for code in ("SensitiveContentDetected", "AuthenticationError", "RateLimitError"):
        if code in message:
            return code
    return str(row.get("error_type") or "invalid_judgment")


def markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> list[str]:
    def render(value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    output.extend("| " + " | ".join(render(row.get(column, "")) for column in columns) + " |" for row in rows)
    return output


def run(args: argparse.Namespace) -> int:
    answer_path = args.input_dir / "answers.jsonl"
    judgment_path = args.input_dir / "judgments.jsonl"
    failure_path = args.input_dir / "judgment_failures.jsonl"
    answers = read_jsonl(answer_path)
    judgments = read_jsonl(judgment_path)
    failures = read_jsonl(failure_path)

    answers_by_key = {answer_key(row): row for row in answers}
    if len(answers_by_key) != len(answers):
        raise ValueError("Duplicate query-method keys in answers.jsonl")
    if len(answers_by_key) != 2100:
        raise ValueError(f"Expected 2100 answers, found {len(answers_by_key)}")

    valid = [row for row in judgments if is_valid_judgment(row)]
    judgments_by_key = {judgment_key(row): row for row in valid}
    if len(judgments_by_key) != len(valid):
        raise ValueError("Duplicate query-method-judge keys in judgments.jsonl")
    if any(key[:2] not in answers_by_key for key in judgments_by_key):
        raise ValueError("Judgment key not found in answers.jsonl")

    keys_by_judge = {
        judge: {key[:2] for key in judgments_by_key if key[2] == judge}
        for judge in JUDGES
    }
    shared_keys = sorted(set.intersection(*(keys_by_judge[judge] for judge in JUDGES)))
    expected_keys = {(*key, judge) for key in answers_by_key for judge in JUDGES}
    missing_keys = sorted(expected_keys - set(judgments_by_key))

    judge_summaries: dict[str, dict[str, Any]] = {}
    judge_summary_rows: list[dict[str, Any]] = []
    for judge in JUDGES:
        available_rows = [row for key, row in judgments_by_key.items() if key[2] == judge]
        shared_rows = [judgments_by_key[(*key, judge)] for key in shared_keys]
        judge_summaries[judge] = {
            "all_available": score_and_boolean_summary(available_rows, scope="all_available"),
            "shared_only": score_and_boolean_summary(shared_rows, scope="shared_only"),
        }
        judge_summary_rows.extend(
            [
                flatten_judge_summary(judge, judge_summaries[judge]["all_available"]),
                flatten_judge_summary(judge, judge_summaries[judge]["shared_only"]),
            ]
        )

    pairwise_agreement, consensus = agreement_rows(judgments_by_key, shared_keys)
    majority_rows = majority_method_rows(judgments_by_key, shared_keys)
    comparisons = paired_rows(
        answers_by_key,
        judgments_by_key,
        bootstrap_samples=args.bootstrap_samples,
    )

    failure_by_key: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in failures:
        failure_by_key[judgment_key(row)].append(row)
    missingness_rows: list[dict[str, Any]] = []
    for qid, method, judge in missing_keys:
        attempts = failure_by_key.get((qid, method, judge), [])
        codes = sorted({failure_code(row) for row in attempts})
        missingness_rows.append(
            {
                "query_id": qid,
                "method_label": method,
                "judge_model": judge,
                "failure_attempts": len(attempts),
                "failure_codes": ",".join(codes) if codes else "unrecorded",
            }
        )

    result = {
        "status": "complete_multi_judge_offline_analysis",
        "input_dir": str(args.input_dir),
        "bootstrap_samples": args.bootstrap_samples,
        "answer_count": len(answers),
        "valid_judgment_count": len(valid),
        "coverage": {judge: len(keys_by_judge[judge]) for judge in JUDGES},
        "shared_valid_count": len(shared_keys),
        "missing_count": len(missing_keys),
        "missing_by_judge": dict(Counter(key[2] for key in missing_keys)),
        "source_sha256": {
            "answers.jsonl": sha256(answer_path),
            "judgments.jsonl": sha256(judgment_path),
            "judgment_failures.jsonl": sha256(failure_path),
        },
        "judge_summaries": judge_summaries,
        "pairwise_agreement": pairwise_agreement,
        "consensus": consensus,
        "majority_method_summary": majority_rows,
        "paired_comparisons": comparisons,
        "missingness": missingness_rows,
        "excluded_headline_field": {
            "field": "insufficient_context_appropriate",
            "reason": "The prompt did not operationally define this boolean, and judge calibration diverged materially.",
        },
    }

    prefix = args.output_prefix
    write_json(prefix.with_suffix(".json"), result)
    write_csv(prefix.with_suffix(".judges.csv"), judge_summary_rows)
    write_csv(prefix.with_suffix(".agreement.csv"), pairwise_agreement)
    write_csv(prefix.with_suffix(".consensus.csv"), consensus)
    write_csv(prefix.with_suffix(".majority.csv"), majority_rows)
    write_csv(prefix.with_suffix(".paired.csv"), comparisons)
    write_csv(prefix.with_suffix(".missingness.csv"), missingness_rows)

    coverage_rows = [
        {
            "judge": judge,
            "valid": len(keys_by_judge[judge]),
            "coverage_percent": 100.0 * len(keys_by_judge[judge]) / len(answers),
            "missing": len(answers) - len(keys_by_judge[judge]),
        }
        for judge in JUDGES
    ]
    headline_rows = []
    for judge in JUDGES:
        summary = judge_summaries[judge]["all_available"]
        headline_rows.append(
            {
                "judge": judge,
                "correctness_mean": summary["scores"]["correctness_score"]["mean"],
                "is_correct": summary["booleans"]["is_correct"]["true_rate"],
                "faithfulness_mean": summary["scores"]["faithfulness_score"]["mean"],
                "is_faithful": summary["booleans"]["is_faithful"]["true_rate"],
                "citations_supported": summary["booleans"]["citations_supported"]["true_rate"],
            }
        )

    lines = [
        "# Task65.7 Multi-Judge Analysis",
        "",
        "This is an offline analysis of the fixed 2,100 Task63 answers; no answers were regenerated.",
        "",
        "## Coverage",
        "",
        *markdown_table(coverage_rows, ("judge", "valid", "coverage_percent", "missing")),
        "",
        f"Cross-judge analyses use the `{len(shared_keys)}` query-method keys valid for all three judges.",
        "MiniMax missing judgments are not imputed.",
        "",
        "## Judge-Level Distribution",
        "",
        *markdown_table(
            headline_rows,
            ("judge", "correctness_mean", "is_correct", "faithfulness_mean", "is_faithful", "citations_supported"),
        ),
        "",
        "Absolute score calibration differs by judge, so raw scores are not pooled across models.",
        "",
        "## Pairwise Agreement On Shared Keys",
        "",
        *markdown_table(
            pairwise_agreement,
            ("field", "judge_left", "judge_right", "n", "raw_agreement", "cohen_kappa"),
        ),
        "",
        "## Three-Judge Consensus",
        "",
        *markdown_table(
            consensus,
            ("field", "n", "unanimous_rate", "majority_positive_rate", "all_positive_rate", "all_negative_rate"),
        ),
        "",
        "## Within-Judge Paired Comparisons",
        "",
        *markdown_table(
            comparisons,
            (
                "judge_model",
                "comparison",
                "paired_queries",
                "correct_delta_pp",
                "correct_delta_ci_low_pp",
                "correct_delta_ci_high_pp",
                "mcnemar_exact_p",
                "faithful_delta_pp",
                "faithful_mcnemar_exact_p",
                "context_token_saving_percent",
            ),
        ),
        "",
        "## Interpretation Boundary",
        "",
        "- Report each judge separately and use within-judge paired comparisons; do not pool raw scores.",
        "- Use `is_correct` and `is_faithful` for primary agreement analysis.",
        "- Correctness differences are non-significant, but majority-vote faithfulness decreases for BGE and increases for the SentMMR composition.",
        "- Exclude `insufficient_context_appropriate` from headline evidence because its rubric was under-specified.",
        "- Multi-judge agreement is robustness evidence for answer-level evaluation, not human evaluation.",
    ]
    prefix.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(prefix), "valid": len(valid), "shared": len(shared_keys), "missing": len(missing_keys)}))
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
