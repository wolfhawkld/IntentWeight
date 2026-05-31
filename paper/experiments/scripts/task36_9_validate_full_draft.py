#!/usr/bin/env python3
"""Validate paper-facing Markdown and provisional BibTeX consistency."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "paper" / "full_draft"
BIB_PATH = DRAFT / "references.bib"

MANUSCRIPT_FILES = [
    DRAFT / "00_title.md",
    DRAFT / "01_abstract.md",
    DRAFT / "02_introduction.md",
    DRAFT / "03_related_work.md",
    DRAFT / "04_method.md",
    DRAFT / "05_experimental_setup.md",
    DRAFT / "06_results.md",
    DRAFT / "07_discussion.md",
    DRAFT / "08_limitations.md",
    DRAFT / "09_conclusion.md",
    DRAFT / "12_appendix.md",
]

FORBIDDEN_PATTERNS = {
    "internal task label": re.compile(r"\b[Tt]ask\d+(?:[._-]\d+)*\b"),
    "unfinished marker": re.compile(r"\b(?:TODO|FIXME|TBD)\b"),
    "overstrong manifold wording": re.compile(r"\bmanifold-structured\b", re.IGNORECASE),
}

CITATION_RE = re.compile(r"(?<![\w/])@([A-Za-z0-9_:-]+)")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")


def validate_markdown() -> tuple[list[str], set[str]]:
    errors: list[str] = []
    citations: set[str] = set()

    for path in MANUSCRIPT_FILES:
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)

        for label, pattern in FORBIDDEN_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: {label}: {match.group(0)}")

        display_count = content.count("$$")
        inline_count = content.replace("$$", "").count("$")
        if display_count % 2:
            errors.append(f"{relative}: unpaired display-math delimiter")
        if inline_count % 2:
            errors.append(f"{relative}: unpaired inline-math delimiter")

        citations.update(CITATION_RE.findall(content))

    return errors, citations


def validate_bib(citations: set[str]) -> list[str]:
    errors: list[str] = []
    content = BIB_PATH.read_text(encoding="utf-8")
    keys = BIB_KEY_RE.findall(content)
    key_set = set(keys)

    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    missing = sorted(citations - key_set)
    if duplicates:
        errors.append(f"{BIB_PATH.relative_to(ROOT)}: duplicate keys: {duplicates}")
    if missing:
        errors.append(f"{BIB_PATH.relative_to(ROOT)}: missing cited keys: {missing}")

    print(f"manuscript_files={len(MANUSCRIPT_FILES)}")
    print(f"citation_keys={len(citations)}")
    print(f"bib_entries={len(keys)}")
    print(f"uncited_bib_entries={len(key_set - citations)}")
    return errors


def main() -> None:
    errors, citations = validate_markdown()
    errors.extend(validate_bib(citations))

    if errors:
        print("validation=failed")
        for error in errors:
            print(error)
        raise SystemExit(1)

    print("validation=passed")


if __name__ == "__main__":
    main()
