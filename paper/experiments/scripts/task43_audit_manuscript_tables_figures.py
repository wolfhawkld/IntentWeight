#!/usr/bin/env python3
"""Audit manuscript table and figure numbers against experiment artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "paper" / "experiments" / "results"
FULL_DRAFT = ROOT / "paper" / "full_draft"
FIGURES = FULL_DRAFT / "figures"
LATEX = ROOT / "paper" / "latex"
REPORT = RESULTS / "task43_table_figure_data_audit.md"


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def read_csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def f4(value: Any) -> str:
    return f"{float(value):.4f}"


def f2(value: Any) -> str:
    return f"{float(value):.2f}"


def pp_from_fraction(value: Any) -> str:
    return f"{float(value) * 100:+.2f} pp"


def pp_from_points(value: Any) -> str:
    return f"{float(value):+.2f} pp"


def pct(value: Any) -> str:
    return f"{float(value):.2f}%"


def ratio(value: Any) -> str:
    return f"{float(value):.4f}x"


def int_comma(value: Any) -> str:
    return f"{int(float(value)):,}"


def find_one(rows: list[dict[str, str]], **conditions: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(key) == expected for key, expected in conditions.items())
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one row for {conditions}, found {len(matches)}")
    return matches[0]


def rows_where(rows: list[dict[str, str]], **conditions: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if all(row.get(key) == expected for key, expected in conditions.items())
    ]


def mean_float(rows: list[dict[str, str]], column: str) -> float:
    return mean(float(row[column]) for row in rows)


def weighted_mean(rows: list[dict[str, str]], value_col: str, weight_col: str) -> float:
    total_weight = sum(float(row[weight_col]) for row in rows)
    return sum(float(row[value_col]) * float(row[weight_col]) for row in rows) / total_weight


class Audit:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def check(self, item: str, source: str, expected: str, ok: bool, detail: str = "") -> None:
        self.rows.append(
            {
                "item": item,
                "source": source,
                "expected": expected,
                "status": "PASS" if ok else "FAIL",
                "detail": detail,
            }
        )

    def contains(self, item: str, source: str, expected: str, text: str) -> None:
        self.check(item, source, expected, expected in text)

    def eq(self, item: str, source: str, expected: Any, actual: Any, detail: str = "") -> None:
        self.check(item, source, str(expected), str(expected) == str(actual), detail or f"actual={actual}")

    def close(
        self,
        item: str,
        source: str,
        expected: float,
        actual: float,
        tol: float = 0.0051,
        detail: str = "",
    ) -> None:
        self.check(
            item,
            source,
            f"{expected:.6f}",
            abs(expected - actual) <= tol,
            detail or f"actual={actual:.6f}, tol={tol}",
        )


def selected_policy_name(run_id: str) -> str:
    return run_id.rsplit(":", 1)[-1]


def selected_policy_rows(rel: str) -> tuple[str, list[dict[str, str]], dict[str, str]]:
    rows = read_csv(rel)
    policy_rows = [row for row in rows if row["method_label"] == "task38"]
    if not policy_rows:
        raise AssertionError(f"no selected-policy rows in {rel}")
    policy = selected_policy_name(policy_rows[0]["method_run_id"])
    dense_adaptive = find_one(rows, method_label="dense_adaptive")
    return policy, policy_rows, dense_adaptive


def audit_table_1_and_g1(audit: Audit, manuscript: str) -> None:
    policies: dict[str, bool] = {}
    for scale in ["100k", "200k", "400k", "638k"]:
        rel = f"paper/experiments/results/task38_{scale}_calibrated_context_budget.test_paired.csv"
        meta = read_json(f"paper/experiments/results/task38_{scale}_calibrated_context_budget.json")
        policy, policy_rows, dense_row = selected_policy_rows(rel)
        policy_delta = mean_float(policy_rows, "hit_delta_mean")
        policy_saving = mean_float(policy_rows, "token_saving_percent")
        dense_delta = float(dense_row["hit_delta_mean"])
        dense_saving = float(dense_row["token_saving_percent"])
        policies[scale] = bool(meta["selected_policy"]["eligible"])
        row = (
            f"| {scale} | `{policy}` | {pp_from_fraction(policy_delta)} | "
            f"{pct(policy_saving)} | {pp_from_fraction(dense_delta)} | {pct(dense_saving)} |"
        )
        audit.contains(f"Table 1 row {scale}", rel, row, manuscript)
        g1_row = (
            f"| {scale} | `{policy}` | {str(policies[scale])} | "
            f"{pp_from_fraction(policy_delta)} | {pct(policy_saving)} | "
            f"{pp_from_fraction(dense_delta)} | {pct(dense_saving)} |"
        )
        audit.contains(f"Appendix G1 row {scale}", rel, g1_row, manuscript)


def audit_table_2_and_h(audit: Audit, manuscript: str) -> None:
    geometry = {
        "20k/q200": find_one(
            read_csv("paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv"),
            scale="20k_q200",
        ),
        "100k": find_one(
            read_csv("paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv"),
            scale="100k",
        ),
    }
    for scale_label, row in geometry.items():
        main_row = (
            f"| science/search {scale_label} | {f4(row['dense_hit@10'])} | "
            f"{f4(row['task29_hit@10'])} | {pp_from_points(row['task29_hit_delta_pp'])} |"
        )
        audit.contains(
            f"Table 2 fixed top-10 row science {scale_label}",
            "paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv",
            main_row,
            manuscript,
        )
        h1_row = (
            f"| science/search {scale_label} | {int_comma(row['num_corpus_chunks'])} | "
            f"{int(row['num_queries'])} | {f4(row['dense_hit@10'])} | "
            f"{f4(row['task29_hit@10'])} | {pp_from_points(row['task29_hit_delta_pp'])} |"
        )
        audit.contains(
            f"Appendix H1 row science {scale_label}",
            "paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv",
            h1_row,
            manuscript,
        )

    for scale_key, label in [("20k_q200", "20k/q200"), ("100k", "100k")]:
        rel = f"paper/experiments/results/task39_lotte_science_{scale_key}_calibrated_context_budget.test_paired.csv"
        policy, policy_rows, _ = selected_policy_rows(rel)
        savings = [float(row["token_saving_percent"]) for row in policy_rows]
        main_range = f"{f2(min(savings))}-{f2(max(savings))}%"
        audit.contains(
            f"Table 2 budget range science {label}",
            rel,
            f"| science/search {label} |",
            manuscript,
        )
        audit.contains(
            f"Table 2 budget saving range science {label}",
            rel,
            main_range,
            manuscript,
        )
        for row in policy_rows:
            h2_row = (
                f"| {label} | `{policy}` | {int(row['seed'])} | "
                f"{pp_from_fraction(row['hit_delta_mean'])} | "
                f"{pct(row['token_saving_percent'])} | {row['noninferior_by_ci']} |"
            )
            audit.contains(f"Appendix H2 row {label} seed {row['seed']}", rel, h2_row, manuscript)


def audit_ablation_tables(audit: Audit, manuscript: str) -> None:
    rows = read_csv("paper/experiments/results/task33_3_clean_ablation_table.csv")
    expected = [
        ("Dense-only", "Dense-only", "Quality floor"),
        ("BM25-only", "BM25-only", "Lexical baseline"),
        ("Dense+BM25 hybrid", "Dense+BM25 hybrid", "Static fusion"),
        ("No feedback gated routing", "No feedback gated", "Full dense fallback, no learning"),
        ("Equal noisy feedback", "Equal noisy feedback", "No trust weighting"),
        ("Trust-weighted feedback", "Trust-weighted feedback", "Default trust scoring"),
        ("Trust-weighted mild noise", "Trust-weighted mild noise", "Best controlled-noise point"),
        ("Task29-C final policy", "Conservative final policy", "Confidence-only baseline"),
        ("Oracle feedback", "Oracle feedback", "Upper bound"),
    ]
    for source_component, display_component, role in expected:
        row = find_one(rows, component=source_component)
        dense_rate = f4(row["dense_rate"]) if row["dense_rate"] else "-"
        linucb_rate = f4(row["linucb_primary_rate"]) if row["linucb_primary_rate"] else "-"
        cluster_hit = f4(row["selected_cluster_hit"]) if row["selected_cluster_hit"] else "-"
        reward = f4(row["last_true_reward"]) if row["last_true_reward"] else "-"
        table_row = (
            f"| {display_component} | {role} | {f4(row['hit@10'])} | "
            f"{f4(row['evidence_recall@10'])} | {float(row['avg_context_tokens@10']):.2f} | "
            f"{f4(row['token_ratio_vs_dense'])} | {dense_rate} | {linucb_rate} | "
            f"{cluster_hit} | {reward} |"
        )
        audit.contains(f"Table 3 row {display_component}", "paper/experiments/results/task33_3_clean_ablation_table.csv", table_row, manuscript)

    for component, feedback in [
        ("Equal noisy feedback", "Equal noisy feedback"),
        ("Trust-weighted feedback", "Trust-weighted feedback"),
        ("Trust-weighted mild noise", "Trust-weighted mild noise"),
        ("Oracle feedback", "Oracle feedback"),
    ]:
        row = find_one(rows, component=component)
        table_row = (
            f"| {feedback} | {f4(row['hit@10'])} | {f4(row['token_ratio_vs_dense'])} | "
            f"{f4(row['dense_rate'])} | {f4(row['linucb_primary_rate'])} | "
            f"{f4(row['selected_cluster_hit'])} | {f4(row['last_true_reward'])} |"
        )
        audit.contains(f"Table 4 row {feedback}", "paper/experiments/results/task33_3_clean_ablation_table.csv", table_row, manuscript)


def audit_recovery_tables(audit: Audit, manuscript: str) -> None:
    config = [
        ("science/search 100k", "science 100k", "paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv"),
        ("technology/search 100k", "technology 100k", "paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv"),
    ]
    pooled_affected = 0
    pooled_recovered = 0
    for main_domain, appendix_domain, rel in config:
        rows = read_csv(rel)
        conservative = rows_where(rows, protocol="same_query_retry", method="same_arm_boost_conservative")
        affected = sum(int(row["affected_count"]) for row in conservative)
        recovered = sum(int(row["recovered_count"]) for row in conservative)
        saving = mean_float(conservative, "token_saving_percent_vs_dense")
        pooled_affected += affected
        pooled_recovered += recovered
        main_row = (
            f"| {main_domain} | {affected} | {recovered} | "
            f"{pct(recovered / affected * 100)} | {pct(saving)} |"
        )
        audit.contains(f"Table 5 row {main_domain}", rel, main_row, manuscript)

        for method, label in [
            ("same_arm_boost", "arm boost"),
            ("same_arm_boost_conservative", "arm boost + conservative budget"),
            ("same_full_context", "full-context fallback"),
        ]:
            method_rows = rows_where(rows, protocol="same_query_retry", method=method)
            m_affected = sum(int(row["affected_count"]) for row in method_rows)
            m_recovered = sum(int(row["recovered_count"]) for row in method_rows)
            m_saving = mean_float(method_rows, "token_saving_percent_vs_dense")
            appendix_row = (
                f"| {appendix_domain} | {label} | {m_affected} | {m_recovered} | "
                f"{pct(m_recovered / m_affected * 100)} | {pct(m_saving)} |"
            )
            audit.contains(f"Appendix I1 row {appendix_domain} {label}", rel, appendix_row, manuscript)

        for method, label in [
            ("generalized_conservative_budget", "conservative budget on learned risky arms after calibration"),
            ("generalized_full_context", "full-context fallback on learned risky arms after calibration"),
        ]:
            method_rows = rows_where(rows, protocol="calibration_to_test", method=method)
            hit_delta = mean_float(method_rows, "hit_delta_vs_before")
            saving = mean_float(method_rows, "token_saving_percent_vs_dense")
            appendix_row = (
                f"| {appendix_domain} | {label} | {pp_from_fraction(hit_delta)} | {pct(saving)} |"
            )
            audit.contains(f"Appendix I2 row {appendix_domain} {label}", rel, appendix_row, manuscript)

    pooled_row = (
        f"| pooled | {pooled_affected} | {pooled_recovered} | "
        f"{pct(pooled_recovered / pooled_affected * 100)} | - |"
    )
    audit.contains("Table 5 pooled row", "task40 pooled same-query recovery", pooled_row, manuscript)


def audit_geometry_table_and_figure(audit: Audit, manuscript: str) -> None:
    tech = read_csv("paper/experiments/results/task30_lotte_geometry_scale_validation.csv")
    science = read_csv("paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv")
    for domain, rows in [("technology/search", tech), ("science/search", science)]:
        for row in rows:
            scale = row["scale"].replace("20k_q200", "20k/q200")
            table_row = (
                f"| {domain} {scale} | {int(row['pca_sample_dim_for_90pct'])} | "
                f"{f4(row['pca_sample_var@64'])} | {f4(row['nearest_cluster_hit@3_mean'])} | "
                f"{f4(row['context_recall_retention@10'])} | {pp_from_points(row['task29_hit_delta_pp'])} |"
            )
            audit.contains(
                f"Table 6 geometry row {domain} {scale}",
                "task30/task43 geometry diagnostics",
                table_row,
                manuscript,
            )

    fig3_rows = read_csv("paper/full_draft/figures/figure3_geometry_diagnostics_data.csv")
    for row in tech + science:
        domain = "technology/search" if "technology" in row["dataset"] else "science/search"
        scale = row["scale"].replace("20k_q200", "20k/q200")
        fig = find_one(fig3_rows, domain=domain, scale=scale)
        audit.eq(f"Figure 3 corpus_chunks {domain} {scale}", "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv", str(int(row["num_corpus_chunks"])), fig["corpus_chunks"])
        audit.eq(f"Figure 3 pca_dim90 {domain} {scale}", "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv", str(int(row["pca_sample_dim_for_90pct"])), fig["pca_dim90"])
        audit.eq(f"Figure 3 pca_var64 {domain} {scale}", "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv", f4(row["pca_sample_var@64"]), fig["pca_var64"])
        audit.eq(f"Figure 3 nearest_cluster_hit {domain} {scale}", "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv", f4(row["nearest_cluster_hit@3_mean"]), fig["nearest_cluster_hit_at_3"])
        audit.eq(f"Figure 3 context_retention {domain} {scale}", "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv", f4(row["context_recall_retention@10"]), fig["context_retention_at_10"])


def audit_figure_2(audit: Audit) -> None:
    fig2_rows = read_csv("paper/full_draft/figures/figure2_token_quality_frontier_data.csv")
    expected_specs = [
        ("technology/search", "100k", 101311, "paper/experiments/results/task38_100k_calibrated_context_budget.test_paired.csv"),
        ("technology/search", "200k", 201010, "paper/experiments/results/task38_200k_calibrated_context_budget.test_paired.csv"),
        ("technology/search", "400k", 400674, "paper/experiments/results/task38_400k_calibrated_context_budget.test_paired.csv"),
        ("technology/search", "638k", 638509, "paper/experiments/results/task38_638k_calibrated_context_budget.test_paired.csv"),
        ("science/search", "20k/q200", 20490, "paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv"),
        ("science/search", "100k", 101187, "paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv"),
    ]
    for domain, scale, corpus_chunks, rel in expected_specs:
        _, policy_rows, dense_row = selected_policy_rows(rel)
        expected = {
            "corpus_chunks": str(corpus_chunks),
            "policy_hit_delta_pp": f2(mean_float(policy_rows, "hit_delta_mean") * 100),
            "policy_saving_pct": f2(mean_float(policy_rows, "token_saving_percent")),
            "dense_adaptive_hit_delta_pp": f2(float(dense_row["hit_delta_mean"]) * 100),
            "dense_adaptive_saving_pct": f2(dense_row["token_saving_percent"]),
        }
        fig = find_one(fig2_rows, domain=domain, scale=scale)
        for key, value in expected.items():
            audit.eq(f"Figure 2 {key} {domain} {scale}", "paper/full_draft/figures/figure2_token_quality_frontier_data.csv", value, fig[key])


def audit_figure_4(audit: Audit) -> None:
    fig2_rows = read_csv("paper/full_draft/figures/figure2_token_quality_frontier_data.csv")
    fig3_rows = read_csv("paper/full_draft/figures/figure3_geometry_diagnostics_data.csv")
    fig4_rows = read_csv("paper/full_draft/figures/figure4_geometry_to_gain_data.csv")
    for fig3 in fig3_rows:
        domain = fig3["domain"]
        scale = fig3["scale"]
        fig2 = find_one(fig2_rows, domain=domain, scale=scale)
        fig4 = find_one(fig4_rows, domain=domain, scale=scale)
        expected = {
            "corpus_chunks": fig3["corpus_chunks"],
            "nearest_cluster_hit_at_3": fig3["nearest_cluster_hit_at_3"],
            "context_retention_at_10": fig3["context_retention_at_10"],
            "policy_hit_delta_pp": fig2["policy_hit_delta_pp"],
            "policy_saving_pct": fig2["policy_saving_pct"],
        }
        for key, value in expected.items():
            audit.eq(f"Figure 4 {key} {domain} {scale}", "paper/full_draft/figures/figure4_geometry_to_gain_data.csv", value, fig4[key])


def audit_figure_5(audit: Audit) -> None:
    fig5_rows = read_csv("paper/full_draft/figures/figure5_feedback_adaptation_data.csv")
    ablation_rows = read_csv("paper/experiments/results/task33_3_clean_ablation_table.csv")
    expected_components = [
        "No feedback gated routing",
        "Equal noisy feedback",
        "Trust-weighted feedback",
        "Trust-weighted mild noise",
        "Oracle feedback",
    ]
    for component in expected_components:
        source = find_one(ablation_rows, component=component)
        fig = find_one(fig5_rows, setting=component)
        expected = {
            "hit_at_10": f4(source["hit@10"]),
            "token_ratio_vs_dense": f4(source["token_ratio_vs_dense"]),
            "dense_rate": f4(source["dense_rate"]),
            "linucb_rate": f4(source["linucb_primary_rate"]),
            "selected_cluster_hit": f4(source["selected_cluster_hit"]),
            "last_true_reward": f4(source["last_true_reward"]),
        }
        for key, value in expected.items():
            audit.eq(f"Figure 5 {key} {component}", "paper/full_draft/figures/figure5_feedback_adaptation_data.csv", value, fig[key])

    strong_summary = read_csv("paper/experiments/results/task33_2_feedback_trust_strong/linucb_cost_summary.csv")[0]
    strong_context = rows_where(
        read_csv("paper/experiments/results/task33_2_feedback_sensitivity_context_tokens.csv"),
        source_label="trust_strong",
    )
    fig = find_one(fig5_rows, setting="Trust-weighted strong noise")
    expected = {
        "hit_at_10": f4(strong_summary["hit@10_mean"]),
        "token_ratio_vs_dense": f4(mean_float(strong_context, "context_token_ratio_vs_baseline@10")),
        "dense_rate": f4(strong_summary["dense_query_rate_mean"]),
        "linucb_rate": f4(strong_summary["linucb_primary_rate_mean"]),
        "selected_cluster_hit": f4(strong_summary["selected_cluster_hit_rate_mean"]),
        "last_true_reward": f4(strong_summary["last_epoch_true_reward_mean"]),
    }
    for key, value in expected.items():
        audit.eq(f"Figure 5 {key} Trust-weighted strong noise", "paper/full_draft/figures/figure5_feedback_adaptation_data.csv", value, fig[key])


def audit_appendix_a(audit: Audit, manuscript: str) -> None:
    rows = read_csv("paper/experiments/results/task29_3_seed_variance_ci.csv")
    for scale in ["100k", "200k", "400k", "638k"]:
        hit = find_one(rows, scale=scale, metric="hit@10")
        delta = find_one(rows, scale=scale, metric="hit_delta_vs_baseline@10")
        token = find_one(rows, scale=scale, metric="avg_context_tokens@10")
        saving = find_one(rows, scale=scale, metric="context_token_saving_pct@10")
        a1 = (
            f"| {scale} | {f4(hit['dense_baseline'])} | {f4(hit['mean'])} | {f4(hit['std'])} | "
            f"[{f4(hit['ci95_low'])}, {f4(hit['ci95_high'])}] | {float(delta['mean']):+.4f} |"
        )
        audit.contains(f"Appendix A1 row {scale}", "paper/experiments/results/task29_3_seed_variance_ci.csv", a1, manuscript)
        a2 = (
            f"| {scale} | {float(token['dense_baseline']):.2f} | {float(token['mean']):.2f} | "
            f"{float(token['std']):.2f} | [{float(token['ci95_low']):.2f}, {float(token['ci95_high']):.2f}] | "
            f"{pct(saving['mean'])} | [{pct(saving['ci95_low'])}, {pct(saving['ci95_high'])}] |"
        )
        audit.contains(f"Appendix A2 row {scale}", "paper/experiments/results/task29_3_seed_variance_ci.csv", a2, manuscript)

    rows_5 = read_csv("paper/experiments/results/task33_6_100k_5seed_context_tokens.csv")
    dense = find_one(rows_5, run_id="dense")
    policies = [row for row in rows_5 if row["run_id"] != "dense"]
    hit_mean = mean_float(policies, "hit@10")
    token_mean = mean_float(policies, "avg_context_tokens@10")
    ratio_mean = mean_float(policies, "context_token_ratio_vs_baseline@10")
    a3_dense = f"| Dense-only | 1 | {f4(dense['hit@10'])} | {float(dense['avg_context_tokens@10']):.2f} | {ratio(dense['context_token_ratio_vs_baseline@10'])} | 0.00% |"
    a3_policy = f"| Conservative policy | 5 | {f4(hit_mean)} | {token_mean:.2f} | {ratio(ratio_mean)} | {pct((1 - ratio_mean) * 100)} |"
    audit.contains("Appendix A3 dense row", "paper/experiments/results/task33_6_100k_5seed_context_tokens.csv", a3_dense, manuscript)
    audit.contains("Appendix A3 policy row", "paper/experiments/results/task33_6_100k_5seed_context_tokens.csv", a3_policy, manuscript)


def audit_appendix_b_c(audit: Audit, manuscript: str) -> None:
    rows = read_csv("paper/experiments/results/task23_lotte_scaleup_summary.csv")
    for row in rows:
        b1 = (
            f"| {row['scale']} | {int(row['corpus_chunks'])} | {f4(row['bm25_recall@10'])} | "
            f"{f4(row['dense_recall@10'])} | {f4(row['hybrid_recall@10'])} |"
        )
        audit.contains(f"Appendix B1 row {row['scale']}", "paper/experiments/results/task23_lotte_scaleup_summary.csv", b1, manuscript)

    rows = read_csv("paper/experiments/results/task28_1_context_token_backfill_aggregated.csv")
    c_specs = [
        ("banking77", "gated_cost_aware", "Banking77", "Gated cost-aware routing"),
        ("emanual", "gated_cost_aware", "eManual", "Gated cost-aware routing"),
        ("lotte_technology_search_100k", "quality_first", "LoTTE 100k", "Quality-first routing"),
        ("lotte_technology_search_100k", "conditional_fallback", "LoTTE 100k", "Conditional fallback routing"),
        ("lotte_technology_search_100k", "cluster_credit", "LoTTE 100k", "Cluster-credit routing"),
        ("lotte_technology_search_200k", "initial_gated", "LoTTE 200k", "Initial gated routing"),
        ("lotte_technology_search_400k", "initial_gated", "LoTTE 400k", "Initial gated routing"),
        ("lotte_technology_search_638k", "initial_gated", "LoTTE 638k", "Initial gated routing"),
    ]
    method_alias = {
        "quality_first": ("task19_ablation_D", "gated_cost_aware"),
        "conditional_fallback": ("task20_conditional_S", "gated_cost_aware"),
        "cluster_credit": ("task25_100k_cluster_credit_formal", "gated_cost_aware"),
        "initial_gated": (None, "gated_cost_aware"),
    }
    for dataset, method_key, label, setting in c_specs:
        if method_key in {"gated_cost_aware"}:
            matches = [row for row in rows if row["dataset"] == dataset and row["method"] == method_key]
        elif method_key == "initial_gated":
            task_by_dataset = {
                "lotte_technology_search_200k": "task22_200k_formal",
                "lotte_technology_search_400k": "task22_5_lotte_400k_linucb_formal",
                "lotte_technology_search_638k": "task22_9_lotte_638k_linucb_formal",
            }
            matches = [
                row
                for row in rows
                if row["dataset"] == dataset
                and row["method"] == "gated_cost_aware"
                and row["task"] == task_by_dataset[dataset]
            ]
        else:
            task, method = method_alias[method_key]
            matches = [
                row
                for row in rows
                if row["dataset"] == dataset and row["method"] == method and row["task"] == task
            ]
        if len(matches) != 1:
            raise AssertionError(f"Appendix C match failed for {(dataset, method_key)}: {len(matches)}")
        row = matches[0]
        c1 = (
            f"| {label} | {setting} | {f4(row['hit@10_mean'])} | "
            f"{float(row['avg_context_tokens@10_mean']):.2f} | "
            f"{ratio(row['context_token_ratio_vs_baseline@10_mean'])} | "
            f"{float(row['avg_source_candidate_cost_mean']):.2f} |"
        )
        audit.contains(f"Appendix C1 row {label} {setting}", "paper/experiments/results/task28_1_context_token_backfill_aggregated.csv", c1, manuscript)


def audit_secondary_and_robustness(audit: Audit, manuscript: str) -> None:
    dense_pubmedqa = read_json("paper/experiments/results/dense_pubmedqa_metrics.json")
    dense_banking77 = read_json("paper/experiments/results/dense_banking77_metrics.json")
    dense_cuad = read_json("paper/experiments/results/dense_cuad_metrics.json")
    trust_pubmedqa = next(row for row in read_json("paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json") if row["feedback_mode"] == "trust_weighted")
    trust_banking77 = next(row for row in read_json("paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json") if row["feedback_mode"] == "trust_weighted")
    trust_cuad = next(row for row in read_json("paper/experiments/results/linucb_trust_cuad_prequential_metrics.json") if row["feedback_mode"] == "trust_weighted")
    for item, token, rel in [
        ("Appendix D PubMedQA dense", f"Dense reaches $\\mathrm{{Hit@10}}={f4(dense_pubmedqa['recall@10'])}$", "paper/experiments/results/dense_pubmedqa_metrics.json"),
        ("Appendix D PubMedQA trust hit", f"$\\mathrm{{Hit@10}}={f4(trust_pubmedqa['recall@10_mean'])}$", "paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json"),
        ("Appendix D PubMedQA reward", f"last reward ${f4(trust_pubmedqa['last_epoch_true_reward_mean'])}$", "paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json"),
        ("Appendix D PubMedQA last-epoch cluster", f"selected-cluster hit\n  ${f4(trust_pubmedqa['last_epoch_selected_cluster_hit_rate_mean'])}$", "paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json"),
        ("Appendix D Banking77 dense", f"Dense/reference $\\mathrm{{Hit@10}}$ is ${f4(dense_banking77['recall@10'])}$", "paper/experiments/results/dense_banking77_metrics.json"),
        ("Appendix D Banking77 trust hit", f"$\\mathrm{{Hit@10}}={f4(trust_banking77['recall@10_mean'])}$", "paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json"),
        ("Appendix D Banking77 reward", f"last reward ${f4(trust_banking77['last_epoch_true_reward_mean'])}$", "paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json"),
        ("Appendix D Banking77 last-epoch cluster", f"selected-cluster hit ${f4(trust_banking77['last_epoch_selected_cluster_hit_rate_mean'])}$", "paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json"),
        ("Appendix D CUAD dense", f"$\\mathrm{{Hit@10}}$ is ${f4(dense_cuad['recall@10'])}$", "paper/experiments/results/dense_cuad_metrics.json"),
        ("Appendix D CUAD trust", f"$\\mathrm{{Hit@10}}={f4(trust_cuad['recall@10_mean'])}$", "paper/experiments/results/linucb_trust_cuad_prequential_metrics.json"),
    ]:
        audit.contains(item, rel, token, manuscript)

    d_rows = read_csv("paper/experiments/results/emanual_failure_analysis_tables.csv")
    d_specs = [
        ("bm25", "strict_chunk_id", "BM25", "Strict chunk ID"),
        ("bm25", "text_equivalent", "BM25", "Text-equivalent"),
        ("dense", "strict_chunk_id", "Dense", "Strict chunk ID"),
        ("dense", "text_equivalent", "Dense", "Text-equivalent"),
        ("hybrid_rrf", "strict_chunk_id", "Static hybrid", "Strict chunk ID"),
        ("hybrid_rrf", "text_equivalent", "Static hybrid", "Text-equivalent"),
        ("dedup_dense", "deduplicated_text_corpus", "Dense", "Deduplicated corpus"),
    ]
    for method, mode, label, mode_label in d_specs:
        row = find_one(d_rows, method=method, evaluation_mode=mode)
        recall = row["recall@10_mean"] or row["recall@10"]
        mrr = row["mrr@10_mean"] or row["mrr@10"]
        ndcg = row["ndcg@10_mean"] or row["ndcg@10"]
        table_row = (
            f"| {label} | {mode_label} | {f4(recall)} | "
            f"{f4(mrr)} | {f4(ndcg)} |"
        )
        audit.contains(f"Appendix D1 row {label} {mode_label}", "paper/experiments/results/emanual_failure_analysis_tables.csv", table_row, manuscript)

    e_rows = read_csv("paper/experiments/results/task33_1a_multiqa_100k_context_tokens.csv")
    dense = find_one(e_rows, run_id="dense")
    policies = [row for row in e_rows if row["run_id"] != "dense"]
    e_dense = (
        f"| Dense-only | {f4(dense['hit@10'])} | {f4(dense['mrr@10'])} | "
        f"{f4(dense['ndcg@10'])} | {f4(dense['evidence_recall@10'])} | "
        f"{float(dense['avg_context_tokens@10']):.2f} | {ratio(dense['context_token_ratio_vs_baseline@10'])} |"
    )
    e_policy = (
        f"| Conservative policy | {f4(mean_float(policies, 'hit@10'))} | "
        f"{f4(mean_float(policies, 'mrr@10'))} | {f4(mean_float(policies, 'ndcg@10'))} | "
        f"{f4(mean_float(policies, 'evidence_recall@10'))} | "
        f"{mean_float(policies, 'avg_context_tokens@10'):.2f} | "
        f"{ratio(mean_float(policies, 'context_token_ratio_vs_baseline@10'))} |"
    )
    audit.contains("Appendix E1 dense row", "paper/experiments/results/task33_1a_multiqa_100k_context_tokens.csv", e_dense, manuscript)
    audit.contains("Appendix E1 conservative row", "paper/experiments/results/task33_1a_multiqa_100k_context_tokens.csv", e_policy, manuscript)

    summary = read_json("paper/experiments/results/task33_5_llm_generation_smoke/summary.json")
    f_dense = (
        f"| Dense top-10 | {float(summary['dense_score_mean']):.4f} | "
        f"{float(summary['dense_faithfulness_mean']):.4f} | "
        f"{float(summary['dense_answer_relevance_mean']):.4f} | "
        f"{summary['winner_counts']['dense']} | 1.0000x |"
    )
    f_policy = (
        f"| Conservative policy | {float(summary['treatment_score_mean']):.4f} | "
        f"{float(summary['treatment_faithfulness_mean']):.4f} | "
        f"{float(summary['treatment_answer_relevance_mean']):.4f} | "
        f"{summary['winner_counts']['treatment']} | 0.9321x |"
    )
    f_tie = f"| Tie | - | - | - | {summary['winner_counts']['tie']} | - |"
    audit.contains("Appendix F1 dense row", "paper/experiments/results/task33_5_llm_generation_smoke/summary.json", f_dense, manuscript)
    audit.contains("Appendix F1 conservative row", "paper/experiments/results/task33_5_llm_generation_smoke/summary.json", f_policy, manuscript)
    audit.contains("Appendix F1 tie row", "paper/experiments/results/task33_5_llm_generation_smoke/summary.json", f_tie, manuscript)


def audit_assets(audit: Audit) -> None:
    assets = [
        "paper/full_draft/figures/figure1_system_diagram.svg",
        "paper/full_draft/figures/figure2_token_quality_frontier.svg",
        "paper/full_draft/figures/figure2_token_quality_frontier_data.csv",
        "paper/full_draft/figures/figure3_geometry_diagnostics.svg",
        "paper/full_draft/figures/figure3_geometry_diagnostics_data.csv",
        "paper/full_draft/figures/figure4_geometry_to_gain.svg",
        "paper/full_draft/figures/figure4_geometry_to_gain_data.csv",
        "paper/full_draft/figures/figure5_feedback_adaptation.svg",
        "paper/full_draft/figures/figure5_feedback_adaptation_data.csv",
        "paper/latex/figures/figure1_system_diagram.pdf",
        "paper/latex/figures/figure2_token_quality_frontier.pdf",
        "paper/latex/figures/figure3_geometry_diagnostics.pdf",
        "paper/latex/figures/figure4_geometry_to_gain.pdf",
        "paper/latex/figures/figure5_feedback_adaptation.pdf",
    ]
    for rel in assets:
        audit.check(f"Figure asset exists {Path(rel).name}", rel, rel, (ROOT / rel).exists())


def write_report(audit: Audit) -> None:
    passed = sum(1 for row in audit.rows if row["status"] == "PASS")
    failed = sum(1 for row in audit.rows if row["status"] == "FAIL")
    lines = [
        "# Task43 Manuscript Table/Figure Data Audit",
        "",
        "This audit checks manuscript-facing table and figure numbers against the",
        "source experiment CSV/JSON artifacts. It verifies the markdown draft and",
        "figure data CSVs; LaTeX layout is checked separately by `make -C paper/latex audit`.",
        "Task40 same-query recovery token savings are checked with the same",
        "seed-level average used in `task40_feedback_recovery_summary.md`, not an",
        "affected-query-weighted average.",
        "",
        f"- Checks: {len(audit.rows)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
    ]
    if failed:
        lines += ["## Failures", ""]
        for row in audit.rows:
            if row["status"] == "FAIL":
                lines.append(f"- **{row['item']}**")
                lines.append(f"  - Source: `{row['source']}`")
                lines.append(f"  - Expected: `{row['expected']}`")
                if row["detail"]:
                    lines.append(f"  - Detail: {row['detail']}")
        lines.append("")
    lines += ["## Full Check Log", "", "| Status | Item | Source | Expected | Detail |", "|---|---|---|---|---|"]
    for row in audit.rows:
        expected = row["expected"].replace("|", "\\|")
        detail = row["detail"].replace("|", "\\|")
        lines.append(
            f"| {row['status']} | {row['item']} | `{row['source']}` | `{expected}` | {detail} |"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manuscript = "\n".join(
        [
            read_text("paper/full_draft/06_results.md"),
            read_text("paper/full_draft/12_appendix.md"),
        ]
    )
    audit = Audit()
    audit_assets(audit)
    audit_table_1_and_g1(audit, manuscript)
    audit_table_2_and_h(audit, manuscript)
    audit_ablation_tables(audit, manuscript)
    audit_recovery_tables(audit, manuscript)
    audit_geometry_table_and_figure(audit, manuscript)
    audit_figure_2(audit)
    audit_figure_4(audit)
    audit_figure_5(audit)
    audit_appendix_a(audit, manuscript)
    audit_appendix_b_c(audit, manuscript)
    audit_secondary_and_robustness(audit, manuscript)
    write_report(audit)
    failures = [row for row in audit.rows if row["status"] == "FAIL"]
    print(f"checks={len(audit.rows)} passed={len(audit.rows) - len(failures)} failed={len(failures)}")
    print(f"report={REPORT.relative_to(ROOT)}")
    if failures:
        for row in failures[:20]:
            print(f"FAIL {row['item']}: {row['expected']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
