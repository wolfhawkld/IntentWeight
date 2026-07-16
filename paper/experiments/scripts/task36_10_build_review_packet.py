#!/usr/bin/env python3
"""Build a self-contained review packet from the paper-facing draft."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "paper" / "full_draft"
PACKET = ROOT / "paper" / "review_packet"
VALIDATOR = ROOT / "paper" / "experiments" / "scripts" / "task36_9_validate_full_draft.py"

MAIN_CHAPTERS = [
    DRAFT / "01_abstract.md",
    DRAFT / "02_introduction.md",
    DRAFT / "03_related_work.md",
    DRAFT / "04_method.md",
    DRAFT / "05_experimental_setup.md",
    DRAFT / "06_results.md",
    DRAFT / "07_discussion.md",
    DRAFT / "08_limitations.md",
    DRAFT / "09_conclusion.md",
]
SUPPLEMENT = DRAFT / "12_appendix.md"

FIGURES = [
    (
        "Figure 1",
        "IntentRoute system diagram",
        DRAFT / "figures" / "figure1_system_diagram.svg",
        DRAFT / "figures" / "figure1_author_spec.md",
    ),
    (
        "Figure 2",
        "Token-quality frontier across LoTTE scale",
        DRAFT / "figures" / "figure2_token_quality_frontier.svg",
        DRAFT / "figures" / "figure2_token_quality_frontier_data.csv",
    ),
    (
        "Figure 3",
        "Local geometry to route-control behavior",
        DRAFT / "figures" / "figure3_geometry_to_control.svg",
        DRAFT / "figures" / "figure3_geometry_to_control_data.csv",
    ),
]

FORBIDDEN_PATTERNS = {
    "internal task label": re.compile(r"\b[Tt]ask\d+(?:[._-]\d+)*\b"),
    "unfinished marker": re.compile(r"\b(?:TODO|FIXME|TBD)\b"),
    "overstrong manifold wording": re.compile(r"\bmanifold-structured\b", re.IGNORECASE),
}

CITATION_RE = re.compile(r"(?<![\w/])@([A-Za-z0-9_:-]+)")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")


def read_title() -> str:
    content = (DRAFT / "00_title.md").read_text(encoding="utf-8")
    match = re.search(r"## Recommended Title\s*\n+\s*(.+)", content)
    if not match:
        raise ValueError("Could not find the recommended title")
    return match.group(1).strip()


def assemble_manuscript() -> str:
    parts = [f"# {read_title()}", "", "<!-- Generated review packet. Edit source chapters under paper/full_draft/. -->", ""]
    for path in MAIN_CHAPTERS:
        parts.append(path.read_text(encoding="utf-8").rstrip())
        parts.extend(["", "---", ""])
    return "\n".join(parts[:-3]).rstrip() + "\n"


def assemble_supplement() -> str:
    return (
        "<!-- Generated review packet. Edit paper/full_draft/12_appendix.md. -->\n\n"
        + SUPPLEMENT.read_text(encoding="utf-8").rstrip()
        + "\n"
    )


def figure_index() -> str:
    rows = [
        "# Figure Index",
        "",
        "Updated: 2026-07-17",
        "",
        "Data figures are generated deterministically from experiment artifacts.",
        "Figure 1 remains an author-owned placeholder and must be replaced from its specification.",
        "",
        "| Figure | Purpose | Review asset | Regeneration source |",
        "|---|---|---|---|",
    ]
    for label, purpose, asset, source in FIGURES:
        asset_link = f"../full_draft/{asset.relative_to(DRAFT)}"
        source_link = f"../full_draft/{source.relative_to(DRAFT)}"
        rows.append(f"| {label} | {purpose} | [{asset.name}]({asset_link}) | [{source.name}]({source_link}) |")
    rows.extend(
        [
            "",
            "Regenerate deterministic data-figure review assets from the repository root:",
            "",
            "```bash",
            ".venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py",
            "```",
            "",
        ]
    )
    return "\n".join(rows)


def submission_checklist() -> str:
    return """# Submission Review Checklist

Updated: 2026-07-05

## Claim Boundary

- [ ] Keep the central claim on adaptive evidence selection and final
  retrieved-context token control.
- [ ] Describe the geometry framing as a piecewise relevance-manifold
  assumption supported by diagnostics, not as theorem-level proof.
- [ ] State that the evaluated implementation is retrieval-backed QA over LoTTE
  technology/search, not every possible knowledge-carrier format.
- [ ] Keep dense retrieval visible as a strong baseline, recall floor, and
  fallback route.
- [ ] Avoid universal or statistically significant dense-dominance wording.

## Experimental Disclosure

- [ ] Disclose that feedback is controlled simulation derived from ground
  truth under noise and trust settings.
- [ ] Describe multi-epoch prequential adaptation as repeated simulated
  interaction, not IID held-out generalization.
- [ ] Keep query-level `Hit@10` separate from complete-evidence
  `EvidenceRecall@10`.
- [ ] Use final retrieved context tokens for the headline token-efficiency
  claim.
- [ ] Do not equate evidence-input token reduction with total serving cost,
  latency, memory, or energy reduction.
- [ ] Label source candidate cost and dense invocation rate as retrieval-stage
  diagnostics.

## Reviewer-Risk Disclosure

- [ ] Mention the limited three-seed scale-up diagnostics and the wider 400k
  token-saving interval.
- [ ] Mention the five-seed LoTTE 100k extension without claiming statistical
  superiority.
- [ ] Report the matched MiniLM, BGE-base, and E5-base comparisons against
  their own dense baselines.
- [ ] Keep the 300-query downstream evaluation framed as single-generator,
  three-model judge support rather than human evaluation.
- [ ] Keep PubMedQA and Banking77 as supporting evidence; keep eManual and CUAD
  as boundary cases.

## Venue Migration

- [x] Use Information Processing & Management as the primary target.
- [ ] Convert selected Markdown tables into LaTeX.
- [x] Separate complete supporting evidence into a standalone supplement.
- [ ] Normalize `references.bib` to the target bibliography style.
- [x] Size deterministic data figures at the 190 mm Elsevier full-width target.
- [ ] Replace Figure 1 with author-produced vector artwork that follows the
  sizing and typography specification.
"""


def packet_readme() -> str:
    return """# IntentRoute Review Packet

Updated: 2026-07-05

This directory is the venue-neutral review handoff for the IntentRoute paper.
It is generated from `paper/full_draft/` and should be used for independent
academic review before LaTeX venue migration.

## Review Entry Points

- `manuscript.md`: assembled paper-facing main manuscript.
- `supplementary_material.md`: complete supporting evidence separated under
  approved Task67 scheme A.
- `references.bib`: provisional BibTeX bibliography.
- `figure_index.md`: draft figure assets and regeneration sources.
- `submission_checklist.md`: claim-boundary and migration checklist.
- `validation_report.md`: automated draft and packet validation output.
- `manifest.sha256`: content hashes for packet files.

## Regeneration

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_10_build_review_packet.py
```

Edit source chapters under `paper/full_draft/`, then regenerate this packet.
Do not manually edit generated packet files.
"""


def validate_packet(manuscript: str, bibliography: str) -> list[str]:
    errors: list[str] = []
    for label, pattern in FORBIDDEN_PATTERNS.items():
        for match in pattern.finditer(manuscript):
            line = manuscript.count("\n", 0, match.start()) + 1
            errors.append(f"manuscript.md:{line}: {label}: {match.group(0)}")

    display_count = manuscript.count("$$")
    inline_count = manuscript.replace("$$", "").count("$")
    if display_count % 2:
        errors.append("manuscript.md: unpaired display-math delimiter")
    if inline_count % 2:
        errors.append("manuscript.md: unpaired inline-math delimiter")

    cited_keys = set(CITATION_RE.findall(manuscript))
    bib_keys = BIB_KEY_RE.findall(bibliography)
    bib_key_set = set(bib_keys)
    duplicate_keys = sorted({key for key in bib_keys if bib_keys.count(key) > 1})
    missing_keys = sorted(cited_keys - bib_key_set)

    if duplicate_keys:
        errors.append(f"references.bib: duplicate keys: {duplicate_keys}")
    if missing_keys:
        errors.append(f"references.bib: missing cited keys: {missing_keys}")

    for _, _, asset, source in FIGURES:
        if not asset.exists():
            errors.append(f"missing figure asset: {asset.relative_to(ROOT)}")
        if not source.exists():
            errors.append(f"missing figure source: {source.relative_to(ROOT)}")

    return errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(paths: list[Path]) -> None:
    lines = [f"{sha256(path)}  {path.name}" for path in paths]
    (PACKET / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    PACKET.mkdir(parents=True, exist_ok=True)

    source_audit = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    manuscript = assemble_manuscript()
    supplement = assemble_supplement()
    bibliography = (DRAFT / "references.bib").read_text(encoding="utf-8")
    errors = validate_packet(manuscript + "\n" + supplement, bibliography)
    if errors:
        print("packet_validation=failed")
        for error in errors:
            print(error)
        raise SystemExit(1)

    (PACKET / "README.md").write_text(packet_readme(), encoding="utf-8")
    (PACKET / "manuscript.md").write_text(manuscript, encoding="utf-8")
    (PACKET / "supplementary_material.md").write_text(supplement, encoding="utf-8")
    shutil.copyfile(DRAFT / "references.bib", PACKET / "references.bib")
    (PACKET / "figure_index.md").write_text(figure_index(), encoding="utf-8")
    (PACKET / "submission_checklist.md").write_text(submission_checklist(), encoding="utf-8")

    cited_keys = set(CITATION_RE.findall(manuscript))
    bib_entries = BIB_KEY_RE.findall(bibliography)
    word_count = len(re.findall(r"\b[\w-]+\b", manuscript))
    supplement_word_count = len(re.findall(r"\b[\w-]+\b", supplement))
    report = f"""# Review Packet Validation Report

Updated: 2026-07-05

## Source Draft Audit

```text
{source_audit.stdout.strip()}
```

## Packet Audit

```text
packet_validation=passed
main_chapters={len(MAIN_CHAPTERS)}
manuscript_words={word_count}
supplement_words={supplement_word_count}
citation_keys={len(cited_keys)}
bib_entries={len(bib_entries)}
figure_assets={len(FIGURES)}
```

## Scope

This report checks structural consistency only. It does not replace independent
academic review, visual inspection of draft figures, target-venue formatting,
or final bibliography verification.
"""
    (PACKET / "validation_report.md").write_text(report, encoding="utf-8")

    packet_files = [
        PACKET / "README.md",
        PACKET / "manuscript.md",
        PACKET / "supplementary_material.md",
        PACKET / "references.bib",
        PACKET / "figure_index.md",
        PACKET / "submission_checklist.md",
        PACKET / "validation_report.md",
    ]
    write_manifest(packet_files)

    print("packet_validation=passed")
    print(f"main_chapters={len(MAIN_CHAPTERS)}")
    print(f"manuscript_words={word_count}")
    print(f"citation_keys={len(cited_keys)}")
    print(f"bib_entries={len(bib_entries)}")
    print(f"figure_assets={len(FIGURES)}")
    print(f"packet_dir={PACKET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
