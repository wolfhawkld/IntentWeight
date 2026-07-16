#!/usr/bin/env python3
"""Validate Task77 display consolidation and scientific claim boundaries."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "paper" / "full_draft"
RESULTS = ROOT / "paper" / "experiments" / "results"
MAIN_FILES = [
    DRAFT / name
    for name in (
        "01_abstract.md",
        "02_introduction.md",
        "03_related_work.md",
        "04_method.md",
        "05_experimental_setup.md",
        "06_results.md",
        "07_discussion.md",
        "08_limitations.md",
        "09_conclusion.md",
    )
]
SUPPLEMENT = DRAFT / "12_appendix.md"
FIGURE_DATA = DRAFT / "figures" / "figure3_geometry_to_control_data.csv"
FIGURE_SVG = DRAFT / "figures" / "figure3_geometry_to_control.svg"
REPORT_JSON = RESULTS / "task77_occam_revision_audit.json"
REPORT_MD = RESULTS / "task77_occam_revision_audit.md"


def parse_table(path: Path, marker: str) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(marker))
    table: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif table:
            break
    if len(table) < 3:
        raise ValueError(f"malformed table after {marker}")
    return table[2:]


def main() -> int:
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    main_text = "\n".join(path.read_text(encoding="utf-8") for path in MAIN_FILES)
    supplement = SUPPLEMENT.read_text(encoding="utf-8")
    normalized_main = re.sub(r"\s+", " ", main_text)

    main_tables = re.findall(r"^\*\*Table (\d+)\.", main_text, re.MULTILINE)
    table_ok = main_tables == ["1", "2", "3", "4", "5"]
    checks.append({"item": "main_table_sequence", "status": "PASS" if table_ok else "ERROR", "value": main_tables})
    if not table_ok:
        errors.append(f"main table sequence is {main_tables}")

    supplement_tables = [int(value) for value in re.findall(r"^\*\*Supplementary Table S(\d+)\.", supplement, re.MULTILINE)]
    expected_supplement = list(range(1, 24))
    supplement_ok = supplement_tables == expected_supplement
    checks.append({"item": "supplement_table_sequence", "status": "PASS" if supplement_ok else "ERROR", "value": supplement_tables})
    if not supplement_ok:
        errors.append(f"supplement table sequence is {supplement_tables}")

    table4_rows = parse_table(DRAFT / "06_results.md", "**Table 4.")
    matrix_ok = len(table4_rows) == 15 and table4_rows[-2][0] == "Banking77" and table4_rows[-1][0] == "CUAD GT-anchored"
    checks.append({"item": "cross_dataset_matrix", "status": "PASS" if matrix_ok else "ERROR", "rows": len(table4_rows)})
    if not matrix_ok:
        errors.append("main Table 4 does not contain the 15 declared non-pooled rows")

    table1_rows = parse_table(DRAFT / "06_results.md", "**Table 1.")
    journalized = all("token_budget_" not in " ".join(row) and row[2] in {"Eligible", "Diagnostic only"} for row in table1_rows)
    checks.append({"item": "journalized_table1", "status": "PASS" if journalized else "ERROR", "rows": len(table1_rows)})
    if not journalized:
        errors.append("main Table 1 still exposes raw implementation labels")

    forbidden = {
        "SelectiveContext-lite": "historical local prompt-pruning proxy",
        "QA-tuned MiniLM-family": "same-family encoder display",
        "RLHF-Inspired": "RLHF analogy",
        "centroid-based semantic drift": "misnamed centroid safeguard",
    }
    forbidden_errors = []
    for token, label in forbidden.items():
        if token in main_text or token in supplement:
            forbidden_errors.append(f"{label}: {token}")
    checks.append({"item": "removed_submission_entities", "status": "PASS" if not forbidden_errors else "ERROR", "count": len(forbidden_errors)})
    errors.extend(forbidden_errors)

    required = {
        "feedback_update_order": "The update can therefore change only the route state used by $q_{t+1}$",
        "centroid_mismatch_definition": "selected-arm centroid mismatch safeguard",
        "independent_budget": "Neither feedback nor route confidence directly sets a per-query compression ratio",
        "llmlingua_boundary": "official open-source LLMLingua-2 compressor has not been run",
        "non_pooling": "no pooled effect is computed",
        "arm_table_moved": "Supplementary Table S20",
    }
    for item, token in required.items():
        found = token in normalized_main
        checks.append({"item": item, "status": "PASS" if found else "ERROR"})
        if not found:
            errors.append(f"missing required Task77 text: {token}")

    removed_headings = (
        "## 7.3 Dense Remains Strong",
        "## 7.4 Evidence Completeness Trade-Off",
        "### S12.3 Reporting Guardrails",
        "Representative fixed-top-10 correction audit",
    )
    headings_ok = all(token not in main_text + supplement for token in removed_headings)
    checks.append({"item": "merged_or_removed_sections", "status": "PASS" if headings_ok else "ERROR"})
    if not headings_ok:
        errors.append("a removed or merged Task77 section remains")

    with FIGURE_DATA.open(newline="", encoding="utf-8") as handle:
        figure_rows = list(csv.DictReader(handle))
    panel_counts = {
        panel: sum(row["panel"] == panel for row in figure_rows)
        for panel in ("A_geometry_profile", "B_geometry_random", "C_arm_fallback")
    }
    figure_data_ok = panel_counts == {"A_geometry_profile": 6, "B_geometry_random": 2, "C_arm_fallback": 5}
    checks.append({"item": "figure3_panel_data", "status": "PASS" if figure_data_ok else "ERROR", "value": panel_counts})
    if not figure_data_ok:
        errors.append(f"Figure 3 panel counts are {panel_counts}")

    svg = FIGURE_SVG.read_text(encoding="utf-8")
    font_sizes = [int(value) for value in re.findall(r"font-size: (\d+)px", svg)]
    svg_ok = (
        'width="1500" height="680"' in svg
        and "A  Cross-scale geometry profile" in svg
        and "B  Geometry versus random routing" in svg
        and "C  Arm granularity and fallback" in svg
        and font_sizes
        and min(font_sizes) >= 20
    )
    checks.append({"item": "figure3_svg_contract", "status": "PASS" if svg_ok else "ERROR", "min_font_px": min(font_sizes) if font_sizes else None})
    if not svg_ok:
        errors.append("Figure 3 SVG does not meet the Task77 panel/typography contract")

    payload = {"task": "Task77", "status": "PASS" if not errors else "ERROR", "checks": checks, "errors": errors}
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Task77 Occam Revision Audit",
        "",
        f"Status: **{payload['status']}**",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.get("value", check.get("rows", check.get("count", check.get("min_font_px", ""))))
        lines.append(f"| {check['item']} | {check['status']} | {detail} |")
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("None.")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"main_tables={len(main_tables)}")
    print(f"supplement_tables={len(supplement_tables)}")
    print(f"cross_dataset_rows={len(table4_rows)}")
    print(f"figure3_rows={len(figure_rows)}")
    print(f"validation={payload['status'].lower()}")
    for error in errors:
        print(f"ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
