#!/usr/bin/env python3
"""Validate the five main tables and plotted data against experiment artifacts."""
from __future__ import annotations

import csv
import itertools
import json
import re
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
RESULTS_MD = ROOT / "paper" / "full_draft" / "06_results.md"
FIGURE_DATA = ROOT / "paper" / "full_draft" / "figures"
REPORT = RESULTS / "task67_paper_evidence_audit.json"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def table_rows(number: int) -> list[list[str]]:
    lines = RESULTS_MD.read_text(encoding="utf-8").splitlines()
    marker = re.compile(rf"^\*\*Table {number}\.")
    start = next(index for index, line in enumerate(lines) if marker.match(line))
    table = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif table:
            break
    if len(table) < 3:
        raise ValueError(f"Table {number} is missing or malformed")
    return table[2:]


def supplementary_table_rows(number: int) -> list[list[str]]:
    path = ROOT / "paper" / "full_draft" / "12_appendix.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    marker = re.compile(rf"^\*\*Supplementary Table S{number}\.")
    start = next(index for index, line in enumerate(lines) if marker.match(line))
    table = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif table:
            break
    if len(table) < 3:
        raise ValueError(f"Supplementary Table S{number} is missing or malformed")
    return table[2:]


def signed(value: float, digits: int = 2) -> str:
    return f"{value:+.{digits}f}"


def signed_ci(value: float, digits: int = 2) -> str:
    return f"{0.0:.{digits}f}" if abs(value) < 0.5 * 10 ** (-digits) else signed(value, digits)


def pct(value: float) -> str:
    return f"{value:.2f}%"


def avg(rows: list[dict[str, str]], column: str) -> float:
    return mean(float(row[column]) for row in rows)


def expected_table1() -> list[list[str]]:
    expected = []
    for scale in ("100k", "200k", "400k", "638k"):
        payload = json.loads((RESULTS / f"task38_{scale}_calibrated_context_budget.json").read_text())
        rows = csv_rows(RESULTS / f"task38_{scale}_calibrated_context_budget.test_paired.csv")
        method = [row for row in rows if row["method_label"] == "task38"]
        dense = next(row for row in rows if row["method_label"] == "dense_adaptive")
        eligible = bool(payload["selected_policy"]["eligible"])
        policy_match = re.fullmatch(r"token_budget_r(\d+\.\d+)_m(\d+)", payload["selected_policy"]["policy"])
        if not policy_match:
            raise ValueError(f"unexpected policy label for {scale}")
        ratio = int(round(float(policy_match.group(1)) * 100))
        minimum = int(policy_match.group(2))
        expected.append([
            scale,
            f"{ratio}% budget; minimum {minimum} chunks",
            "Eligible" if eligible else "Diagnostic only",
            f"{signed(100 * avg(method, 'hit_delta_mean'))} pp",
            f"{sum(row['noninferior_by_ci'] == 'True' for row in method)}/{len(method)}",
            pct(avg(method, "token_saving_percent")),
            f"{signed(100 * float(dense['hit_delta_mean']))} pp",
            pct(float(dense["token_saving_percent"])),
        ])
    return expected


def expected_table2() -> list[list[str]]:
    rows = csv_rows(RESULTS / "task53_embedding_backbone_generalization.csv")
    selected = [
        ("MiniLM calibrated", next(row for row in rows if row["backbone"] == "MiniLM")),
        ("BGE full multi-route", next(row for row in rows if row["backbone"] == "BGE-base" and row["route_mode"] == "full_multi_route")),
        ("E5 full multi-route", next(row for row in rows if row["backbone"] == "E5-base" and row["route_mode"] == "full_multi_route")),
    ]
    expected = [[
        label,
        f"{float(row['baseline_hit@10_mean']):.4f}",
        f"{float(row['method_hit@10_mean']):.4f}",
        f"{signed(100 * float(row['hit_delta_mean']))} pp",
        pct(float(row["token_saving_percent_mean"])),
    ] for label, row in selected]

    quality_rows = [
        row for row in csv_rows(RESULTS / "task54_bge_base_100k_positive_hit_context_budget.test_paired.csv")
        if row["method_label"] == "task38"
    ]
    expected.append([
        "BGE quality-first",
        f"{avg(quality_rows, 'baseline_hit@10'):.4f}",
        f"{avg(quality_rows, 'method_hit@10'):.4f}",
        f"{signed(100 * avg(quality_rows, 'hit_delta_mean'))} pp",
        pct(avg(quality_rows, "token_saving_percent")),
    ])
    return expected


def control_row(label: str, row: dict[str, str]) -> list[str]:
    return [
        label,
        f"{float(row['last_route_true_reward_mean']):.4f}",
        f"{float(row['selected_cluster_hit_rate_mean']):.4f}",
        f"{float(row['dense_query_rate_mean']):.4f}",
        f"{signed(float(row['test_hit_delta_pp_mean']))} pp",
        pct(float(row["test_token_saving_pct_mean"])),
    ]


def expected_table3() -> list[list[str]]:
    task58 = {row["setting"]: row for row in csv_rows(RESULTS / "task58_geometry_random_ablation_summary.csv")}
    task59 = {row["setting"]: row for row in csv_rows(RESULTS / "task59_feedback_control_summary.csv")}
    return [
        control_row("Static nearest geometry", task58["static_nearest"]),
        control_row("Uniform random arms", task58["uniform_random"]),
        control_row("Learned full multi-route", task59["learned_full_multi_route"]),
        control_row("Learned gated", task59["learned_gated_cost_aware"]),
        control_row("Static-nearest gated", task59["static_nearest_gated"]),
        control_row("No-feedback gated", task59["no_feedback_gated"]),
    ]


def expected_table4() -> list[list[str]]:
    payload = json.loads((RESULTS / "task69_cross_dataset_consistency.json").read_text())
    by_key = {(row["dataset"], row["scale"]): row for row in payload["current_results"]}
    specs = [
        ("LoTTE technology/search", "100k", "100k", "Full-stack scale"),
        ("LoTTE technology/search", "200k", "200k", "Full-stack scale"),
        ("LoTTE technology/search", "400k", "400k", "Split-sensitive scale"),
        ("LoTTE technology/search", "638k full", "638k", "Full-stack scale"),
        ("LoTTE science/search", "20k/q200", "20k/q200", "Legacy cross-domain diagnostic"),
        ("LoTTE science/search", "100k", "100k", "Cross-domain"),
        ("LoTTE science/search", "200k", "200k", "Cross-domain scale"),
        ("LoTTE science/search", "400k", "400k", "Scale boundary"),
        ("LoTTE recreation/search", "100k", "100k", "External-validity boundary"),
        ("LoTTE writing/search", "100k", "100k", "External-validity frontier"),
        ("PubMedQA", "native full", "Native full", "Dense-ceiling transfer"),
        ("CovidQA-RAG", "native full", "Native full", "Biomedical transfer"),
        ("eManual deduplicated", "native full", "Native full", "Corrected boundary"),
        ("Banking77", "native full", "Native full", "Intent-routing mechanism"),
        ("CUAD GT-anchored", "10k sample", "10k sample", "Sparse-GT boundary"),
    ]
    expected = []
    for dataset, source_scale, display_scale, role in specs:
        row = by_key[(dataset, source_scale)]
        saving = "--" if row["context_saving_percent"] == "--" else pct(float(row["context_saving_percent"]))
        delta = f"{signed(float(row['hit_delta_pp']))} pp"
        expected.append([
            dataset,
            display_scale,
            row["dense_hit@10"],
            row["intentroute_hit@10"],
            delta,
            saving,
            row["strict_ni_seeds"],
            role,
        ])
    return expected


def expected_table5() -> list[list[str]]:
    rows = csv_rows(RESULTS / "task65_7_multi_judge_analysis.paired.csv")
    labels = [
        ("BGE IntentRoute vs BGE dense", "BGE IntentRoute vs BGE dense"),
        ("E5 IntentRoute vs E5 dense", "E5 IntentRoute vs E5 dense"),
        ("IntentRoute+SentMMR vs Dense+SentMMR", "IntentRoute+MMR vs Dense+MMR"),
    ]
    expected = []
    for source_label, display_label in labels:
        group = {row["judge_model"]: row for row in rows if row["comparison"] == source_label}
        majority = group["three_judge_majority"]
        expected.append([
            display_label,
            f"{signed(float(group['deepseek-v4-flash']['correct_delta_pp']))} pp",
            f"{signed(float(group['glm-5.2']['correct_delta_pp']))} pp",
            f"{signed(float(group['minimax-m3']['correct_delta_pp']))} pp",
            f"{signed(float(majority['correct_delta_pp']))} pp "
            f"[{signed_ci(float(majority['correct_delta_ci_low_pp']))}, "
            f"{signed_ci(float(majority['correct_delta_ci_high_pp']))}]",
            f"{pct(float(majority['context_token_saving_percent']))} "
            f"[{pct(float(majority['context_token_saving_ci_low_percent']))}, "
            f"{pct(float(majority['context_token_saving_ci_high_percent']))}]",
        ])
    task79_rows = csv_rows(RESULTS / "task79_llmlingua2_multi_judge_analysis.paired.csv")
    task79_group = {
        row["judge_scope"]: row
        for row in task79_rows
        if row["comparison"] == "IntentRoute+LLMLingua-2 vs Dense+LLMLingua-2"
    }
    task79_majority = task79_group["three_judge_majority"]
    expected.append([
        "IntentRoute + LLMLingua-2 vs Dense + LLMLingua-2",
        f"{signed(float(task79_group['deepseek-v4-flash']['is_correct_delta_pp']))} pp",
        f"{signed(float(task79_group['glm-5.2']['is_correct_delta_pp']))} pp",
        f"{signed(float(task79_group['minimax-m3']['is_correct_delta_pp']))} pp",
        f"{signed(float(task79_majority['is_correct_delta_pp']))} pp "
        f"[{signed_ci(float(task79_majority['is_correct_delta_ci_low_pp']))}, "
        f"{signed_ci(float(task79_majority['is_correct_delta_ci_high_pp']))}]",
        f"{pct(float(task79_majority['context_token_saving_percent']))} "
        f"[{pct(float(task79_majority['context_token_saving_ci_low_percent']))}, "
        f"{pct(float(task79_majority['context_token_saving_ci_high_percent']))}]",
    ])
    return expected


def validate_figure_data(table1: list[list[str]]) -> list[str]:
    errors = []
    expected = {row[0]: row for row in table1}
    rows = csv_rows(FIGURE_DATA / "figure2_token_quality_frontier_data.csv")
    tech = [row for row in rows if row["domain"] == "technology/search"]
    for row in tech:
        source = expected[row["scale"]]
        checks = {
            "policy_hit_delta_pp": source[3].removesuffix(" pp"),
            "policy_saving_pct": source[5].removesuffix("%"),
        }
        for column, value in checks.items():
            if f"{float(row[column]):.2f}" != f"{float(value):.2f}":
                errors.append(f"figure2_token_quality_frontier_data.csv:{row['scale']}:{column} drift")

    figure3 = csv_rows(FIGURE_DATA / "figure3_geometry_to_control_data.csv")
    panel_a = [row for row in figure3 if row["panel"] == "A_geometry_profile"]
    source_a = []
    for domain, filename in (
        ("technology/search", "task30_lotte_geometry_scale_validation.csv"),
        ("science/search", "task43_lotte_science_geometry_diagnostics.csv"),
    ):
        for row in csv_rows(RESULTS / filename):
            source_a.append((domain, row))
    for domain, source in source_a:
        scale = source["scale"].replace("20k_q200", "20k/q200")
        row = next(item for item in panel_a if item["domain"] == domain and item["scale"] == scale)
        checks = {
            "corpus_chunks": str(int(source["num_corpus_chunks"])),
            "pca_var64": f"{float(source['pca_sample_var@64']):.4f}",
            "nearest_cluster_hit_at_3": f"{float(source['nearest_cluster_hit@3_mean']):.4f}",
            "context_retention_at_10": f"{float(source['context_recall_retention@10']):.4f}",
        }
        for column, value in checks.items():
            if row[column] != value:
                errors.append(f"figure3:panelA:{domain}:{scale}:{column} drift")

    task58 = {row["setting"]: row for row in csv_rows(RESULTS / "task58_geometry_random_ablation_summary.csv")}
    for setting, source_key in (("Static-nearest geometry", "static_nearest"), ("Uniform-random arms", "uniform_random")):
        row = next(item for item in figure3 if item["panel"] == "B_geometry_random" and item["setting"] == setting)
        source = task58[source_key]
        checks = {
            "route_reward": f"{float(source['last_route_true_reward_mean']):.4f}",
            "selected_cluster_hit": f"{float(source['selected_cluster_hit_rate_mean']):.4f}",
            "final_fused_hit_at_10": f"{float(source['full_top10_hit@10_mean']):.4f}",
        }
        for column, value in checks.items():
            if row[column] != value:
                errors.append(f"figure3:panelB:{setting}:{column} drift")

    task60 = csv_rows(RESULTS / "task60_arm_count_sensitivity_summary.csv")
    by_key = {(row["arm_count"], row["short_mode"]): row for row in task60}
    for arm_count in (8, 16, 32, 64, 128):
        row = next(item for item in figure3 if item["panel"] == "C_arm_fallback" and item["arm_count"] == str(arm_count))
        checks = {
            "static_route_reward": f"{float(by_key[(str(arm_count), 'static')]['last_route_true_reward_mean']):.4f}",
            "gated_dense_rate": f"{float(by_key[(str(arm_count), 'gated')]['dense_query_rate_mean']):.4f}",
            "gated_hit_delta_pp": f"{float(by_key[(str(arm_count), 'gated')]['test_hit_delta_pp_mean']):.2f}",
        }
        for column, value in checks.items():
            if row[column] != value:
                errors.append(f"figure3:panelC:K{arm_count}:{column} drift")
    return errors


NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9.])[-+]?\d[\d,]*(?:\.\d+)?")


def add_numeric_tokens(value: object, target: list[float]) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        target.append(float(value))
    elif isinstance(value, str):
        for token in NUMERIC_TOKEN_RE.findall(value):
            target.append(float(token.replace(",", "")))
    elif isinstance(value, dict):
        for key, item in value.items():
            add_numeric_tokens(key, target)
            add_numeric_tokens(item, target)
    elif isinstance(value, list):
        for item in value:
            add_numeric_tokens(item, target)


def source_numeric_pool(paths: list[Path]) -> list[float]:
    values: list[float] = []
    for path in paths:
        if path.suffix == ".json":
            add_numeric_tokens(json.loads(path.read_text(encoding="utf-8")), values)
            continue
        rows = csv_rows(path)
        add_numeric_tokens(rows, values)
        if not rows:
            continue
        numeric_columns = [
            column for column in rows[0]
            if all(row[column].strip() == "" or re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", row[column].strip()) for row in rows)
        ]
        categorical_columns = [column for column in rows[0] if column not in numeric_columns]
        groupings = [()] + [(column,) for column in categorical_columns]
        groupings += list(itertools.combinations(categorical_columns, 2))
        groupings += list(itertools.combinations(categorical_columns, 3))
        for grouping in groupings:
            groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
            for row in rows:
                groups.setdefault(tuple(row[column] for column in grouping), []).append(row)
            for grouped_rows in groups.values():
                values.append(float(len(grouped_rows)))
                for column in numeric_columns:
                    column_values = [float(row[column]) for row in grouped_rows if row[column].strip()]
                    if column_values:
                        values.extend((mean(column_values), min(column_values), max(column_values), sum(column_values)))
    return values


def token_matches_source(token: str, source_values: list[float]) -> bool:
    display = float(token.replace(",", ""))
    decimals = len(token.rsplit(".", 1)[1]) if "." in token else 0
    tolerance = 0.51 * (10 ** -decimals) if decimals else 0.51
    for value in source_values:
        for candidate in (value, value * 100.0, value / 100.0):
            if abs(display - candidate) <= tolerance:
                return True
    return False


def validate_supplementary_numeric_provenance() -> tuple[list[str], int]:
    source_map = {
        5: [RESULTS / "task63_downstream_llm_evaluation/summary.csv"],
        6: [RESULTS / "task63_downstream_llm_evaluation/paired_comparisons.csv"],
        7: [RESULTS / "task65_7_multi_judge_analysis.json", RESULTS / "task65_7_multi_judge_analysis.judges.csv"],
        8: [RESULTS / "task65_7_multi_judge_analysis.agreement.csv", RESULTS / "task65_7_multi_judge_analysis.consensus.csv"],
        9: [RESULTS / "task65_7_multi_judge_analysis.paired.csv"],
        10: [RESULTS / "task65_4_matched_frontier.quality_matched.csv", RESULTS / "task65_4_matched_frontier.interpolated.csv"],
        11: [RESULTS / "task65_5_calibration_split_sensitivity.summary.csv"],
        12: [RESULTS / "task65_6_cross_scale_cross_fitted_calibration.json", RESULTS / "task65_6_cross_scale_cross_fitted_calibration.folds.csv"],
        17: [RESULTS / "task46_100k_sent_mmr_same_budget.csv"],
        18: [RESULTS / "task48_100k_compressor_normalized.csv"],
        19: [RESULTS / "task47_100k_cross_encoder_reranker.csv"],
        20: [RESULTS / "task60_arm_count_sensitivity_summary.csv"],
        21: [RESULTS / "task65_3_dynamic_route_mediation.json", RESULTS / "task65_3_dynamic_route_mediation.fixed_action.csv"],
        23: [RESULTS / "task73_lotte_domain_expansion.json", RESULTS / "task73_lotte_domain_expansion.csv"],
    }
    errors = []
    checked = 0
    for number, paths in source_map.items():
        missing = [path for path in paths if not path.exists()]
        if missing:
            errors.append(f"Supplementary Table S{number} source missing: {missing}")
            continue
        source_values = source_numeric_pool(paths)
        if number == 7:
            coverage = json.loads((RESULTS / "task65_7_multi_judge_analysis.json").read_text())["coverage"]
            denominator = max(float(value) for value in coverage.values())
            source_values.extend(100.0 * float(value) / denominator for value in coverage.values())
        for row_index, row in enumerate(supplementary_table_rows(number), start=1):
            for cell in row:
                for token in NUMERIC_TOKEN_RE.findall(cell):
                    checked += 1
                    if not token_matches_source(token, source_values):
                        errors.append(f"Supplementary Table S{number} row {row_index}: {token} lacks source provenance")
    return errors, checked


def main() -> int:
    expected = {
        1: expected_table1(),
        2: expected_table2(),
        3: expected_table3(),
        4: expected_table4(),
        5: expected_table5(),
    }
    errors = []
    checks = []
    for number, expected_rows in expected.items():
        actual_rows = table_rows(number)
        status = "PASS" if actual_rows == expected_rows else "ERROR"
        checks.append({"item": f"main_table_{number}", "status": status, "rows": len(actual_rows)})
        if status == "ERROR":
            errors.append(f"Table {number} differs from source-derived display values")
    figure_errors = validate_figure_data(expected[1])
    checks.append({"item": "figure_data", "status": "PASS" if not figure_errors else "ERROR", "files": 2})
    errors.extend(figure_errors)
    supplement_errors, supplement_values = validate_supplementary_numeric_provenance()
    checks.append({
        "item": "supplementary_numeric_provenance",
        "status": "PASS" if not supplement_errors else "ERROR",
        "tables": 15,
        "numeric_values": supplement_values,
    })
    errors.extend(supplement_errors)
    payload = {"status": "PASS" if not errors else "ERROR", "checks": checks, "errors": errors}
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"main_tables={len(expected)}")
    print("figure_data_files=2")
    print(f"supplementary_numeric_values={supplement_values}")
    print(f"validation={payload['status'].lower()}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
