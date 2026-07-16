#!/usr/bin/env python3
"""Validate Task75 terminology, cost scope, feedback framing, and citations."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

SOURCE_FILES = [
    *(ROOT / "paper" / "full_draft").glob("*.md"),
    ROOT / "paper" / "experiments" / "task73_lotte_domain_expansion_plan.md",
    ROOT / "paper" / "experiments" / "task73_lotte_domain_expansion_summary.md",
    ROOT / "paper" / "experiments" / "task74_task73_manuscript_integration_plan.md",
    ROOT / "paper" / "experiments" / "task74_task73_manuscript_integration_summary.md",
    ROOT / "paper" / "experiments" / "post_task69_submission_readiness_plan.md",
    ROOT / "paper" / "experiments" / "task_paper_use_status.md",
    ROOT / "paper" / "experiments" / "results" / "task73_lotte_domain_expansion.md",
    ROOT / "paper" / "experiments" / "results" / "task73_lotte_domain_expansion.json",
]

GENERATED_FILES = [
    ROOT / "paper" / "review_packet" / "manuscript.md",
    ROOT / "paper" / "review_packet" / "supplementary_material.md",
    *(ROOT / "paper" / "latex" / "sections").glob("*.tex"),
    *(ROOT / "paper" / "journal_submission" / "latex" / "sections").glob("*.tex"),
]

FORBIDDEN_PATTERNS = {
    "formal preregistration wording": re.compile(r"\bpre-?register\w*\b", re.IGNORECASE),
    "total-cost equivalence wording": re.compile(
        r"proportional per-query inference-cost reduction|most expensive recurring component",
        re.IGNORECASE,
    ),
    "overstrong feedback heading": re.compile(
        r"Feedback Improves the Policy Field", re.IGNORECASE
    ),
}

REQUIRED_TEXT = {
    ROOT / "paper" / "full_draft" / "03_related_work.md": (
        "@zhao2026r3ag",
        "@kim2026qudar",
        "@qureshi2026budget",
        "@guo2026routerag",
    ),
    ROOT / "paper" / "full_draft" / "02_introduction.md": (
        "input-price component",
        "total serving cost",
    ),
    ROOT / "paper" / "full_draft" / "07_discussion.md": (
        "Feedback Updates Route State under Controlled Credit",
        "system cost separately",
    ),
}

BIB_KEYS = {
    "zhao2026r3ag",
    "kim2026qudar",
    "qureshi2026budget",
    "guo2026routerag",
}
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")


def validate_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing file: {path.relative_to(ROOT)}"]
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for label, pattern in FORBIDDEN_PATTERNS.items():
        for match in pattern.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            errors.append(
                f"{path.relative_to(ROOT)}:{line}: {label}: {match.group(0)}"
            )
    return errors


def main() -> None:
    files = sorted(set(SOURCE_FILES + GENERATED_FILES))
    errors = [error for path in files for error in validate_file(path)]

    for path, required_values in REQUIRED_TEXT.items():
        content = path.read_text(encoding="utf-8")
        for value in required_values:
            if value not in content:
                errors.append(f"{path.relative_to(ROOT)}: missing required text: {value}")

    bibliography = (ROOT / "paper" / "full_draft" / "references.bib").read_text(
        encoding="utf-8"
    )
    found_keys = set(BIB_KEY_RE.findall(bibliography))
    missing_keys = sorted(BIB_KEYS - found_keys)
    if missing_keys:
        errors.append(f"paper/full_draft/references.bib: missing keys: {missing_keys}")

    print(f"checked_files={len(files)}")
    print(f"required_2026_citations={len(BIB_KEYS)}")
    if errors:
        print("validation=failed")
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("validation=passed")


if __name__ == "__main__":
    main()
