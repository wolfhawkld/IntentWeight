#!/usr/bin/env python3
"""Perform static validation of the ACL-style LaTeX migration."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LATEX = ROOT / "paper" / "latex"
MAIN = LATEX / "main.tex"
BIB = LATEX / "references.bib"

REQUIRED = [
    MAIN,
    LATEX / "acl.sty",
    LATEX / "acl_natbib.bst",
    BIB,
    LATEX / "figures" / "figure1_system_diagram.pdf",
    LATEX / "figures" / "figure2_token_quality_frontier.pdf",
    LATEX / "figures" / "figure3_geometry_diagnostics.pdf",
]
SECTION_RE = re.compile(r"\\input\{([^}]+)\}")
CITATION_RE = re.compile(r"\\cite\w*\{([^}]+)\}")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")
MARKDOWN_RE = re.compile(r"(^|\n)(?:#{1,3}\s|\|.+\||```)|\[@[A-Za-z0-9_:-]+", re.MULTILINE)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\ref\{([^}]+)\}")


def main() -> None:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        print("latex_validation=failed")
        for error in errors:
            print(error)
        raise SystemExit(1)

    main_text = MAIN.read_text(encoding="utf-8")
    section_paths = [LATEX / f"{path}.tex" for path in SECTION_RE.findall(main_text)]
    for path in section_paths:
        if not path.exists():
            errors.append(f"missing input file: {path.relative_to(ROOT)}")

    manuscript = main_text + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in section_paths if path.exists()
    )
    markdown_match = MARKDOWN_RE.search(manuscript)
    if markdown_match:
        errors.append(f"unconverted Markdown residue near: {markdown_match.group(0)!r}")

    citations = {
        key.strip()
        for group in CITATION_RE.findall(manuscript)
        for key in group.split(",")
        if key.strip()
    }
    bib_keys = BIB_KEY_RE.findall(BIB.read_text(encoding="utf-8"))
    bib_key_set = set(bib_keys)
    missing_citations = sorted(citations - bib_key_set)
    duplicate_keys = sorted({key for key in bib_keys if bib_keys.count(key) > 1})
    if missing_citations:
        errors.append(f"missing BibTeX keys: {missing_citations}")
    if duplicate_keys:
        errors.append(f"duplicate BibTeX keys: {duplicate_keys}")

    labels = LABEL_RE.findall(manuscript)
    refs = set(REF_RE.findall(manuscript))
    duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
    missing_labels = sorted(refs - set(labels))
    if duplicate_labels:
        errors.append(f"duplicate LaTeX labels: {duplicate_labels}")
    if missing_labels:
        errors.append(f"missing LaTeX labels: {missing_labels}")
    if "tab:generated" in labels:
        errors.append("generated fallback table label remains in manuscript")

    for path in [MAIN, *section_paths]:
        content = path.read_text(encoding="utf-8")
        if content.count(r"\begin{") != content.count(r"\end{"):
            errors.append(f"environment count mismatch: {path.relative_to(ROOT)}")

    print(f"latex_inputs={len(section_paths)}")
    print(f"citation_keys={len(citations)}")
    print(f"bib_entries={len(bib_keys)}")
    print(f"uncited_bib_entries={len(bib_key_set - citations)}")
    print(f"cross_references={len(refs)}")
    tex_tools = ("latexmk", "pdflatex", "bibtex")
    compile_status = "available_not_run" if all(shutil.which(tool) for tool in tex_tools) else "skipped_no_tex_toolchain"
    print(f"pdf_compile={compile_status}")
    if errors:
        print("latex_validation=failed")
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("latex_validation=passed")


if __name__ == "__main__":
    main()
