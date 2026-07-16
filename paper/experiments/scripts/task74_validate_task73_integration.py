#!/usr/bin/env python3
"""Validate source-derived Task73 evidence across Task74 manuscript outputs."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "paper" / "experiments" / "results" / "task73_lotte_domain_expansion.json"
APPENDIX = ROOT / "paper" / "full_draft" / "12_appendix.md"
REPORT_JSON = ROOT / "paper" / "experiments" / "results" / "task74_task73_integration_audit.json"
REPORT_MD = ROOT / "paper" / "experiments" / "results" / "task74_task73_integration_audit.md"


def signed(value: float) -> str:
    return f"{value:+.2f}"


def parse_supplementary_table(number: int) -> list[list[str]]:
    lines = APPENDIX.read_text(encoding="utf-8").splitlines()
    marker = re.compile(rf"^\*\*Supplementary Table S{number}\.")
    start = next(index for index, line in enumerate(lines) if marker.match(line))
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows:
            break
    if len(rows) < 3:
        raise ValueError(f"Supplementary Table S{number} is missing or malformed")
    return rows[2:]


def expected_domain_expansion_rows(payload: dict[str, object]) -> list[list[str]]:
    rows: list[list[str]] = []
    for domain in payload["domains"]:
        short_name = str(domain["domain"])
        for control, label in (("trust", "trust"), ("none", "no feedback")):
            calibration = domain["calibration"][control]
            eligible = int(calibration["eligible_folds"])
            strict_ni = (
                "n/a (fallback)"
                if eligible == 0
                else f"{int(calibration['strict_ni_seeds_1pp'])}/3"
            )
            rows.append(
                [
                    f"{short_name} / {label}",
                    f"{float(domain['lexical']['max_query_token_coverage_mean']):.4f}",
                    f"{float(domain['baseline']['dense']['hit@10']):.4f}",
                    f"{float(domain['route'][control + '_full_multi_route']['hit@10']):.4f}",
                    f"{float(domain['geometry']['nearest_cluster_hit@3']):.4f}",
                    f"{eligible}/5",
                    f"{signed(float(calibration['hit_delta_mean_pp']))} pp",
                    f"{float(calibration['token_saving_mean_pct']):.2f}%",
                    strict_ni,
                ]
            )
    return rows


def require_fragments(path: Path, fragments: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing generated file: {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    return [
        f"{path.relative_to(ROOT)} lacks {fragment!r}"
        for fragment in fragments
        if fragment not in text
    ]


def run_validation() -> dict[str, object]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []
    errors: list[str] = []

    actual_table = parse_supplementary_table(23)
    expected_table = expected_domain_expansion_rows(payload)
    table_ok = actual_table == expected_table
    checks.append({"item": "supplementary_table_s23", "status": "PASS" if table_ok else "ERROR", "rows": len(actual_table)})
    if not table_ok:
        errors.append("Supplementary Table S23 differs from Task73 source-derived values")

    source_requirements = {
        "paper/full_draft/01_abstract.md": ["nine dataset settings", "eight domain", "10.09%", "5.42%"],
        "paper/full_draft/02_introduction.md": ["recreation/search and writing/search", "nine dataset settings"],
        "paper/full_draft/05_experimental_setup.md": ["924", "1,071", "no cross-domain pooled effect"],
        "paper/full_draft/06_results.md": ["0.8366", "0.8655", "0/3", "2/3", "Supplementary Table S23"],
        "paper/full_draft/07_discussion.md": ["trust-weighted calibration safely falls back to Dense"],
        "paper/full_draft/08_limitations.md": ["not a universal quality-preserving token-saving guarantee"],
        "paper/full_draft/09_conclusion.md": ["nine dataset settings", "10.09%", "5.42%"],
        "paper/full_draft/12_appendix.md": ["recreation-minus-writing", "n/a (fallback)", "28/29"],
        "paper/full_draft/README.md": ["nine dataset settings across eight domain areas"],
        "paper/experiments/task_paper_use_status.md": ["task73_lotte_domain_expansion_summary.md"],
    }
    source_errors: list[str] = []
    for relative, fragments in source_requirements.items():
        source_errors.extend(require_fragments(ROOT / relative, fragments))
    full_draft_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "paper" / "full_draft").glob("*.md"))
    )
    for stale in ("seven dataset settings", "six domain areas"):
        if stale in full_draft_text:
            source_errors.append(f"stale manuscript scope remains: {stale!r}")
    checks.append({"item": "canonical_manuscript", "status": "PASS" if not source_errors else "ERROR", "files": len(source_requirements)})
    errors.extend(source_errors)

    generated_requirements = {
        "paper/review_packet/manuscript.md": ["nine dataset settings", "recreation/search", "10.09%"],
        "paper/review_packet/supplementary_material.md": ["Supplementary Table S23", "28/29"],
        "paper/latex/sections/abstract.tex": ["nine dataset settings", "recreation/search", "10.09"],
        "paper/latex/sections/appendix.tex": ["Prospectively Specified LoTTE Domain Expansion", "28/29"],
        "paper/journal_submission/latex/sections/abstract.tex": ["nine dataset settings", "recreation/search", "10.09"],
        "paper/journal_submission/latex/sections/appendix.tex": ["Prospectively Specified LoTTE Domain Expansion", "28/29"],
    }
    generated_errors: list[str] = []
    for relative, fragments in generated_requirements.items():
        generated_errors.extend(require_fragments(ROOT / relative, fragments))
    checks.append({"item": "generated_packages", "status": "PASS" if not generated_errors else "ERROR", "files": len(generated_requirements)})
    errors.extend(generated_errors)

    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    return {
        "task": "Task74",
        "status": "PASS" if not errors else "ERROR",
        "task73_source": str(SOURCE.relative_to(ROOT)),
        "task73_source_sha256": source_sha256,
        "checks": checks,
        "errors": errors,
    }


def write_reports(payload: dict[str, object]) -> None:
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Task74 Task73 Manuscript Integration Audit",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"Task73 source: `{payload['task73_source']}`",
        f"SHA-256: `{payload['task73_source_sha256']}`",
        "",
        "| Check | Status | Coverage |",
        "|---|---|---:|",
    ]
    for check in payload["checks"]:
        coverage = check.get("rows", check.get("files", ""))
        lines.append(f"| {check['item']} | {check['status']} | {coverage} |")
    lines.extend(["", "## Errors", ""])
    if payload["errors"]:
        lines.extend(f"- {error}" for error in payload["errors"])
    else:
        lines.append("None.")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload = run_validation()
    write_reports(payload)
    print(f"checks={len(payload['checks'])}")
    print(f"validation={str(payload['status']).lower()}")
    for error in payload["errors"]:
        print(f"ERROR: {error}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
