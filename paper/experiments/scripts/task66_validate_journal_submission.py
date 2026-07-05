#!/usr/bin/env python3
"""Validate the self-contained IP&M journal submission package."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "paper" / "journal_submission" / "latex"
ERRORS: list[str] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def words(text: str) -> list[str]:
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"[{}$]", " ", text)
    return re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text)


def type3_fonts(path: Path) -> list[str]:
    fonts: set[str] = set()
    with fitz.open(path) as document:
        for page in document:
            for font in page.get_fonts(full=True):
                if font[2] == "Type3":
                    fonts.add(font[3])
    return sorted(fonts)


def validate_figure_pdf(path: Path, *, expected_width_mm: float, expected_height_mm: float | None = None) -> None:
    with fitz.open(path) as document:
        require(len(document) == 1, f"{path.name} has {len(document)} pages; expected one")
        if not document:
            return
        page = document[0]
        width_mm = page.rect.width * 25.4 / 72.0
        height_mm = page.rect.height * 25.4 / 72.0
        require(abs(width_mm - expected_width_mm) <= 0.2, f"{path.name} width is {width_mm:.2f} mm; expected {expected_width_mm:.2f} mm")
        if expected_height_mm is not None:
            require(abs(height_mm - expected_height_mm) <= 0.2, f"{path.name} height is {height_mm:.2f} mm; expected {expected_height_mm:.2f} mm")
        require(not page.get_images(full=True), f"{path.name} contains raster image objects")
        text_sizes = [
            float(span["size"])
            for block in page.get_text("dict").get("blocks", [])
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if str(span.get("text", "")).strip()
        ]
        require(bool(text_sizes), f"{path.name} has no machine-readable vector text")
        if text_sizes:
            require(min(text_sizes) >= 6.8, f"{path.name} minimum text size is {min(text_sizes):.2f} pt; expected at least 7 pt")


def validate_compile_log(path: Path, *, label: str) -> None:
    log = path.read_text(encoding="utf-8", errors="ignore")
    cas_frontmatter_overfull = re.findall(
        r"Overfull \\hbox \(117\.0831pt too wide\) detected at line \d+",
        log,
    )
    require(
        len(cas_frontmatter_overfull) <= 1,
        f"unexpected number of CAS double-blind frontmatter notices in {label}",
    )
    log = re.sub(
        r"Overfull \\hbox \(117\.0831pt too wide\) detected at line \d+",
        "",
        log,
    )
    warning_patterns = (
        r"Overfull \\hbox",
        r"LaTeX Warning:",
        r"Package \S+ Warning:",
        r"undefined citations?",
        r"undefined references?",
    )
    for pattern in warning_patterns:
        require(
            re.search(pattern, log, re.IGNORECASE) is None,
            f"{label} compile log matches warning pattern: {pattern}",
        )


def main() -> int:
    main_tex = TARGET / "anonymous_manuscript.tex"
    supplement_tex = TARGET / "supplementary_material.tex"
    title_tex = TARGET / "title_page.tex"
    manifest_path = TARGET / "source_manifest.json"
    for path in (
        main_tex,
        supplement_tex,
        title_tex,
        manifest_path,
        TARGET / "references.bib",
    ):
        require(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    if ERRORS:
        return finish()

    manuscript = main_tex.read_text(encoding="utf-8")
    supplement = supplement_tex.read_text(encoding="utf-8")
    require(r"\documentclass[a4paper,fleqn,doubleblind]{cas-sc}" in manuscript, "anonymous manuscript is not CAS single-column double-blind review")
    require("acl" not in manuscript.lower(), "ACL-specific text remains in anonymous manuscript")
    require("TODO" not in manuscript, "TODO remains in anonymous manuscript")
    require("Anonymous ACL submission" not in manuscript, "ACL author placeholder remains")
    require(r"\bibliographystyle{cas-model2-names}" in manuscript, "CAS bibliography style missing")
    require(r"\author" not in manuscript, "author field remains in anonymous manuscript")
    require(r"\affiliation" not in manuscript, "affiliation field remains in anonymous manuscript")
    require(r"\input{sections/appendix}" not in manuscript, "supplement remains embedded in main manuscript")
    require(r"\documentclass[a4paper,fleqn,doubleblind]{cas-sc}" in supplement, "supplement is not CAS double-blind")
    require(r"\input{sections/appendix}" in supplement, "supplement does not include the evidence appendix")
    require(r"\renewcommand{\thetable}{S\arabic{table}}" in supplement, "supplementary table numbering is not S-prefixed")
    require(r"\author" not in supplement, "author field remains in supplement")
    require(r"\affiliation" not in supplement, "affiliation field remains in supplement")

    abstract = (TARGET / "sections" / "abstract.tex").read_text(encoding="utf-8")
    abstract_words = len(words(abstract))
    require(abstract_words <= 250, f"abstract has {abstract_words} words; IP&M limit is 250")
    marker_match = re.search(
        r"% TASK66_ABSTRACT_START\s*(.*?)\s*% TASK66_ABSTRACT_END",
        manuscript,
        re.DOTALL,
    )
    require(marker_match is not None, "inline abstract markers are missing")
    if marker_match is not None:
        source_body = "\n".join(
            line for line in abstract.splitlines()
            if not line.startswith("% Generated from ")
        ).strip()
        require(marker_match.group(1).strip() == source_body, "inline abstract differs from canonical abstract")

    keywords = [item.strip() for item in (TARGET / "keywords.txt").read_text(encoding="utf-8").split(";") if item.strip()]
    require(1 <= len(keywords) <= 7, f"keyword count is {len(keywords)}; expected 1-7")
    highlights = [line[2:].strip() for line in (TARGET / "highlights.txt").read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
    require(3 <= len(highlights) <= 5, f"highlight count is {len(highlights)}; expected 3-5")
    for index, item in enumerate(highlights, 1):
        require(len(item) <= 85, f"highlight {index} has {len(item)} characters; limit is 85")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, expected in manifest.get("files", {}).items():
        path = TARGET / relative
        require(path.exists(), f"manifest file missing: {relative}")
        if path.exists():
            require(sha256(path) == expected, f"manifest hash mismatch: {relative}")

    all_anonymous_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [main_tex, supplement_tex, *sorted((TARGET / "sections").glob("*.tex"))]
    )
    require("/home/" not in all_anonymous_text, "local home path leaked into anonymous package")
    require("Anonymous ACL" not in all_anonymous_text, "venue-specific author placeholder leaked")
    display_labels = set(re.findall(r"\\label\{((?:tab|fig):[^}]+)\}", all_anonymous_text))
    display_refs = set(re.findall(r"\\(?:ref|autoref)\{((?:tab|fig):[^}]+)\}", all_anonymous_text))
    require(not (display_labels - display_refs), f"uncited display labels: {sorted(display_labels - display_refs)}")
    require(not (display_refs - display_labels), f"missing display labels: {sorted(display_refs - display_labels)}")

    manuscript_pdf = TARGET / "anonymous_manuscript.pdf"
    supplement_pdf = TARGET / "supplementary_material.pdf"
    title_pdf = TARGET / "title_page.pdf"
    manuscript_log = TARGET / "anonymous_manuscript.log"
    supplement_log = TARGET / "supplementary_material.log"
    title_log = TARGET / "title_page.log"
    bibliography_log = TARGET / "anonymous_manuscript.blg"
    for path in (
        manuscript_pdf,
        supplement_pdf,
        title_pdf,
        manuscript_log,
        supplement_log,
        title_log,
        bibliography_log,
    ):
        require(path.exists(), f"compiled artifact missing: {path.name}")
    if manuscript_pdf.exists():
        with fitz.open(manuscript_pdf) as document:
            manuscript_pages = len(document)
            first_page = document[0].get_text()
        require(manuscript_pages > 1, "anonymous manuscript PDF is unexpectedly short")
        require("Retrieval-augmented systems" in first_page, "abstract body is absent from first PDF page")
        require("sections/abstract" not in first_page, "literal abstract input path leaked into PDF")
    else:
        manuscript_pages = 0
    if supplement_pdf.exists():
        with fitz.open(supplement_pdf) as document:
            supplement_pages = len(document)
            supplement_first_page = document[0].get_text()
        require(supplement_pages > 1, "supplement PDF is unexpectedly short")
        require("Supplementary Material" in supplement_first_page, "supplement title is absent from first page")
    else:
        supplement_pages = 0
    if title_pdf.exists():
        with fitz.open(title_pdf) as document:
            title_pages = len(document)
        require(title_pages == 1, f"title page PDF has {title_pages} pages; expected 1")
    else:
        title_pages = 0
    if manuscript_log.exists():
        validate_compile_log(manuscript_log, label="main manuscript")
    if supplement_log.exists():
        validate_compile_log(supplement_log, label="supplement")
    if title_log.exists():
        log = title_log.read_text(encoding="utf-8", errors="ignore")
        for pattern in (r"Overfull \\hbox", r"LaTeX Warning:", r"Package \S+ Warning:"):
            require(re.search(pattern, log, re.IGNORECASE) is None, f"title-page log matches warning pattern: {pattern}")
    if bibliography_log.exists():
        log = bibliography_log.read_text(encoding="utf-8", errors="ignore")
        warnings = set(re.findall(r"^Warning--.+$", log, re.MULTILINE))
        allowed_warnings = {
            "Warning--empty pages in asai2024selfrag",
            "Warning--empty pages in christiano2017preferences",
        }
        require(not (warnings - allowed_warnings), f"unexpected BibTeX warnings: {sorted(warnings - allowed_warnings)}")
        require("error" not in log.lower(), "BibTeX log contains an error")

    for pdf in (
        manuscript_pdf,
        supplement_pdf,
        title_pdf,
        *sorted((TARGET / "figures").glob("*.pdf")),
    ):
        if pdf.exists():
            require(not type3_fonts(pdf), f"Type 3 fonts remain in {pdf.name}: {type3_fonts(pdf)}")

    figure1 = TARGET / "figures" / "figure1_system_diagram.pdf"
    figure2 = TARGET / "figures" / "figure2_token_quality_frontier.pdf"
    figure3 = TARGET / "figures" / "figure3_geometry_to_control.pdf"
    for figure in (figure1, figure2, figure3):
        require(figure.exists(), f"submission figure missing: {figure.name}")
    if figure1.exists():
        validate_figure_pdf(figure1, expected_width_mm=190.0)
    for figure in (figure2, figure3):
        if figure.exists():
            validate_figure_pdf(figure, expected_width_mm=190.0, expected_height_mm=76.0)

    print(f"abstract_words={abstract_words}")
    print(f"keywords={len(keywords)}")
    print(f"highlights={len(highlights)}")
    print(f"manifest_files={len(manifest.get('files', {}))}")
    print(f"display_crossrefs={len(display_labels)}")
    print(f"manuscript_pages={manuscript_pages}")
    print(f"supplement_pages={supplement_pages}")
    print(f"title_pages={title_pages}")
    return finish()


def finish() -> int:
    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"validation=failed errors={len(ERRORS)}", file=sys.stderr)
        return 1
    print("validation=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
