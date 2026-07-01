#!/usr/bin/env python3
"""Build the self-contained IP&M CAS submission package from canonical LaTeX."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "paper" / "latex"
SUBMISSION = ROOT / "paper" / "journal_submission"
TARGET = SUBMISSION / "latex"
SUBMISSION_FIGURES = (
    "figure1_system_diagram.pdf",
    "figure2_token_quality_frontier.pdf",
    "figure3_geometry_to_control.pdf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sync_file(source: Path, target: Path, *, single_column: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if single_column and source.suffix == ".tex":
        text = source.read_text(encoding="utf-8")
        text = text.replace(r"\begin{table*}", r"\begin{table}")
        text = text.replace(r"\end{table*}", r"\end{table}")
        text = re.sub(
            r"\\begin\{table\}\[([!htbp]+)\]",
            r"\\begin{table}[pos=\1]",
            text,
        )
        target.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(source, target)


def markdown_bullets(path: Path) -> list[str]:
    return [match.group(1).strip() for line in path.read_text(encoding="utf-8").splitlines()
            if (match := re.match(r"^-\s+(.+)$", line))]


def markdown_numbered(path: Path) -> list[str]:
    return [match.group(1).strip() for line in path.read_text(encoding="utf-8").splitlines()
            if (match := re.match(r"^\d+\.\s+(.+)$", line))]


def main() -> None:
    synced: list[Path] = []
    for source in sorted((SOURCE / "sections").glob("*.tex")):
        target = TARGET / "sections" / source.name
        sync_file(source, target, single_column=True)
        synced.append(target)

    figure_target = TARGET / "figures"
    figure_target.mkdir(parents=True, exist_ok=True)
    for stale in figure_target.glob("*.pdf"):
        if stale.name not in SUBMISSION_FIGURES:
            stale.unlink()
    for name in SUBMISSION_FIGURES:
        source = SOURCE / "figures" / name
        target = TARGET / "figures" / source.name
        sync_file(source, target)
        synced.append(target)

    for name in ("references.bib",):
        target = TARGET / name
        sync_file(SOURCE / name, target)
        synced.append(target)

    abstract_source = SOURCE / "sections" / "abstract.tex"
    abstract_lines = [
        line for line in abstract_source.read_text(encoding="utf-8").splitlines()
        if not line.startswith("% Generated from ")
    ]
    abstract_body = "\n".join(abstract_lines).strip()
    manuscript_path = TARGET / "anonymous_manuscript.tex"
    manuscript = manuscript_path.read_text(encoding="utf-8")
    start = "% TASK66_ABSTRACT_START"
    end = "% TASK66_ABSTRACT_END"
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    replacement = f"{start}\n{abstract_body}\n{end}"
    manuscript, count = pattern.subn(lambda _: replacement, manuscript)
    if count != 1:
        raise ValueError("anonymous manuscript must contain exactly one abstract marker pair")
    manuscript_path.write_text(manuscript, encoding="utf-8")

    highlights = markdown_bullets(SUBMISSION / "highlights.md")
    keywords = markdown_numbered(SUBMISSION / "keywords.md")
    (TARGET / "highlights.txt").write_text("\n".join(f"- {item}" for item in highlights) + "\n", encoding="utf-8")
    (TARGET / "keywords.txt").write_text("; ".join(keywords) + "\n", encoding="utf-8")
    synced.extend(
        (
            manuscript_path,
            TARGET / "title_page.tex",
            TARGET / "Makefile",
            TARGET / "highlights.txt",
            TARGET / "keywords.txt",
        )
    )

    manifest = {
        "format": "Elsevier CAS single-column",
        "primary_target": "Information Processing & Management",
        "generated_from": str(SOURCE.relative_to(ROOT)),
        "files": {
            str(path.relative_to(TARGET)): sha256(path)
            for path in sorted(synced)
        },
    }
    (TARGET / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"submission_files={len(synced)}")
    print(f"target={TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
