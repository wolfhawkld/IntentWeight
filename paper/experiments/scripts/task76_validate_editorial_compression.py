#!/usr/bin/env python3
"""Validate Task76 compression and post-Task76 preservation guardrails."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "paper" / "full_draft"

SECTION_FILES = (
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

TASK75_WORD_COUNTS = {
    "01_abstract.md": 234,
    "02_introduction.md": 1447,
    "03_related_work.md": 1542,
    "04_method.md": 2268,
    "05_experimental_setup.md": 2293,
    "06_results.md": 2448,
    "07_discussion.md": 1793,
    "08_limitations.md": 1234,
    "09_conclusion.md": 387,
}

# Task76 deliberately leaves the evidence-dense technical sections unchanged.
PRESERVED_HASHES = {
    "01_abstract.md": "3c43511cd857ca2c6eb1cca38782367bdccb6355399aaa7e4c081bfd2c35ff82",
    "03_related_work.md": "2af8ad461c9ca17d4ede2d0f2c56ebd789d9d679a75cb8804d8ae1df29e1d9cf",
    "04_method.md": "50c7948beafa0a00af10793970954d004fdc859da68bba6ba41dbc3aeb4660a9",
    "05_experimental_setup.md": "4746d2bd709cbaa382010c5b9e493bc97d62f087907a3ef01006f8a9ac2d5b7b",
    "06_results.md": "65328c722358df55ae9753b05bad07530ae727e73d30c2b0f9b6e65a24cf3910",
    "09_conclusion.md": "57b59eef6fc54ec53e5e5cd4f4757021d8b0e5c1c9bb78ef0680abfbe1a3abfa",
}

TASK77_PLAN = ROOT / "paper" / "experiments" / "task77_occam_display_and_narrative_revision_plan.md"

REQUIRED_TEXT = {
    "02_introduction.md": (
        "piecewise relevance-manifold hypothesis",
        "Trust-weighted LinUCB",
        "dense retrieval as a recall floor",
        "final budget is calibrated separately",
        "input-price component",
        "not total serving cost, latency, memory, energy, output tokens, or retrieval overhead",
        "nine dataset settings",
        "LoTTE technology/search",
        "LoTTE science/search",
        "recreation/search and writing/search",
        "PubMedQA and CovidQA-RAG",
        "Banking77",
        "eManual and CUAD",
        "100k, 200k, and 638k save 6-18%",
        "400k diagnostic point",
        "14.50% mean saving",
        "4.7-5.3%",
        "BGE-base and E5-base",
        "300 queries and three LLM judges",
    ),
    "07_discussion.md": (
        "eligible 100k, 200k, and 638k points save 6--18%",
        "400k point is calibration-ineligible",
        "14.50% mean saving",
        "no strict seed-level non-inferiority",
        "4.7--5.3% saving baseline",
        "majority-detected BGE faithfulness decrease",
        "10.09% cross-fitted saving point",
        "trust-weighted calibration safely falls back to Dense",
        "route reward reaches 0.6790",
        "confidence-tier shuffling lowers Hit@10 by 4.80pp",
        "mean AUROC 0.434 versus 0.573",
        "+0.08pp",
        "97.8% of actions are safe",
        "mean Spearman $-0.056$",
        "2.121 versus 2.315",
        "route confidence alone is not one here",
        "measure total system cost separately",
    ),
    "08_limitations.md": (
        "simulated feedback from ground truth",
        "does not outperform matched static-nearest or cold no-feedback",
        "300 frozen-test queries",
        "2,100 answers",
        "6,272 valid",
        "leaves 28 judgments",
        "Dense-only retrieval remains a strong baseline",
        "saves 17--21%",
        "70%/85% of 100k/400k",
        "14.50% mean 400k saving",
        "10.09% saving",
        "not a universal quality-preserving token-saving guarantee",
        "strict non-inferiority in 0/3 seeds",
        "geometry is not a direct compression-safety predictor",
        "Across $K=8$--$128$",
        "Of nine settings",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).strip()


def main() -> None:
    errors: list[str] = []
    current_counts: dict[str, int] = {}

    for name in SECTION_FILES:
        path = DRAFT / name
        if not path.exists():
            errors.append(f"missing canonical section: {path.relative_to(ROOT)}")
            continue
        current_counts[name] = len(path.read_text(encoding="utf-8").split())

    baseline_total = sum(TASK75_WORD_COUNTS.values())
    current_total = sum(current_counts.values())
    reduction = (baseline_total - current_total) / baseline_total
    upper_bound = 0.15 if TASK77_PLAN.exists() else 0.12
    if not 0.09 <= reduction <= upper_bound:
        errors.append(
            f"main-text reduction {reduction:.2%} is outside the 9-{upper_bound:.0%} guardrail"
        )

    checked_hashes = 0
    if not TASK77_PLAN.exists():
        for name, expected_hash in PRESERVED_HASHES.items():
            actual_hash = sha256(DRAFT / name)
            checked_hashes += 1
            if actual_hash != expected_hash:
                errors.append(f"Task76-preserved section changed: paper/full_draft/{name}")

    for name, required_values in REQUIRED_TEXT.items():
        content = normalized(DRAFT / name)
        for value in required_values:
            if value not in content:
                errors.append(f"paper/full_draft/{name}: missing required detail: {value}")

    print(f"task75_words={baseline_total}")
    print(f"task76_words={current_total}")
    print(f"reduction_words={baseline_total - current_total}")
    print(f"reduction_percent={reduction:.2%}")
    print(f"preserved_sections={checked_hashes}")
    if TASK77_PLAN.exists():
        print("preserved_hashes=superseded_by_task77")
    print(f"required_details={sum(map(len, REQUIRED_TEXT.values()))}")
    if errors:
        print("validation=failed")
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("validation=passed")


if __name__ == "__main__":
    main()
