#!/usr/bin/env python3
"""Migrate the paper-facing Markdown draft into modular ACL-style LaTeX."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / "paper" / "full_draft"
LATEX = ROOT / "paper" / "latex"
SECTIONS = LATEX / "sections"

TITLE_RE = re.compile(r"## Recommended Title\s*\n+\s*(.+)")
CITATION_RE = re.compile(r"\[((?:@[A-Za-z0-9_:-]+(?:;\s*)?)+)\]")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
TABLE_CAPTION_RE = re.compile(r"\*\*(?:Appendix )?Table ([A-Z]?\d+)\.\s*(.+)\*\*")
LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.+)$")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")
PLACEHOLDER_RE = re.compile(r"@@LATEX(\d+)@@")
NUMERIC_CELL_RE = re.compile(r"^[\[\]\d\s.,+\-%x]+$")

CHAPTERS = [
    ("02_introduction.md", "introduction.tex", False),
    ("03_related_work.md", "related_work.tex", False),
    ("04_method.md", "method.tex", False),
    ("05_experimental_setup.md", "experimental_setup.tex", False),
    ("06_results.md", "results.tex", False),
    ("07_discussion.md", "discussion.tex", False),
    ("09_conclusion.md", "conclusion.tex", False),
    ("08_limitations.md", "limitations.tex", False),
    ("12_appendix.md", "appendix.tex", True),
]

FIGURE_REFS = {
    "Figure 1": r"Figure~\ref{fig:system}",
    "Figure 2": r"Figure~\ref{fig:token-quality}",
    "Figure 3": r"Figure~\ref{fig:geometry}",
}


def title() -> str:
    match = TITLE_RE.search((DRAFT / "00_title.md").read_text(encoding="utf-8"))
    if not match:
        raise ValueError("recommended title not found")
    return match.group(1).strip()


def escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def inline(text: str) -> str:
    placeholders: list[str] = []

    def protect(value: str) -> str:
        placeholders.append(value)
        return f"@@LATEX{len(placeholders) - 1}@@"

    text = re.sub(r"\$([^$]+)\$", lambda match: protect(f"${match.group(1)}$"), text)
    text = CITATION_RE.sub(
        lambda match: protect(
            r"\citep{" + ",".join(re.findall(r"@([A-Za-z0-9_:-]+)", match.group(1))) + "}"
        ),
        text,
    )
    text = CODE_RE.sub(lambda match: protect(r"\texttt{" + escape_latex(match.group(1)) + "}"), text)
    text = BOLD_RE.sub(lambda match: protect(r"\textbf{" + escape_latex(match.group(1)) + "}"), text)
    for source, replacement in FIGURE_REFS.items():
        text = text.replace(source, protect(replacement))

    escaped = escape_latex(text)
    return PLACEHOLDER_RE.sub(lambda match: placeholders[int(match.group(1))], escaped)


def slug(value: str) -> str:
    value = re.sub(r"^(?:\d+(?:\.\d+)*|[A-Z](?:\.\d+)?)\.?\s+", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "section"


def heading_title(value: str) -> str:
    return re.sub(r"^(?:\d+(?:\.\d+)*|[A-Z](?:\.\d+)?)\.?\s+", "", value).strip()


def table_label(identifier: str) -> str:
    return "tab:" + identifier.lower().replace(".", "-")


def emit_table(rows: list[str], caption: tuple[str, str] | None) -> list[str]:
    cells = [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in rows]
    if len(cells) < 2:
        raise ValueError("Markdown table requires header and alignment row")
    header = cells[0]
    body = cells[2:]
    columns = len(header)
    if any(len(row) != columns for row in body):
        raise ValueError("Markdown table has inconsistent column counts")

    text_heavy = any(len(cell) > 45 for row in body for cell in row)
    wide = columns > 5 or text_heavy
    environment = "table*" if wide else "table"
    width = r"\textwidth" if wide else r"\linewidth"
    identifier, title_text = caption or ("generated", "Migrated result table.")
    numeric_columns = [
        all(NUMERIC_CELL_RE.fullmatch(row[index]) for row in body)
        for index in range(columns)
    ]
    column_spec = "".join("r" if numeric else "l" for numeric in numeric_columns)
    result = [
        rf"\begin{{{environment}}}[t]",
        r"\centering",
        r"\small",
        rf"\caption{{{inline(title_text.rstrip('.'))}}}",
        rf"\label{{{table_label(identifier)}}}",
    ]
    if text_heavy:
        column_spec = "".join("r" if numeric else "X" for numeric in numeric_columns)
        result.extend([rf"\begin{{tabularx}}{{{width}}}{{{column_spec}}}"])
    else:
        result.extend([rf"\resizebox{{{width}}}{{!}}{{%", rf"\begin{{tabular}}{{{column_spec}}}"])
    result.extend(
        [
        r"\toprule",
        " & ".join(inline(cell) for cell in header) + r" \\",
        r"\midrule",
        ]
    )
    result.extend(" & ".join(inline(cell) for cell in row) + r" \\" for row in body)
    result.append(r"\bottomrule")
    if text_heavy:
        result.append(r"\end{tabularx}")
    else:
        result.extend([r"\end{tabular}%", r"}"])
    result.extend([rf"\end{{{environment}}}", ""])
    return result


def join_multiline_captions(lines: list[str]) -> list[str]:
    joined: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("**") and "Table " in line and not line.strip().endswith("**"):
            parts = [line.strip()]
            index += 1
            while index < len(lines):
                parts.append(lines[index].strip())
                if lines[index].strip().endswith("**"):
                    break
                index += 1
            joined.append(" ".join(parts))
        else:
            joined.append(line)
        index += 1
    return joined


def convert_markdown(path: Path, *, appendix: bool = False, abstract: bool = False) -> str:
    lines = join_multiline_captions(path.read_text(encoding="utf-8").splitlines())
    label_prefix = path.stem.replace("_", "-")
    output = ["% Generated from paper/full_draft. Edit the Markdown source or migration script.", ""]
    paragraph: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    pending_caption: tuple[str, str] | None = None
    table_rows: list[str] = []
    quote_lines: list[str] = []
    in_display_math = False
    first_heading_seen = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(inline(" ".join(part.strip() for part in paragraph)))
            output.append("")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_items:
            environment = "enumerate" if list_type == "ordered" else "itemize"
            output.append(rf"\begin{{{environment}}}")
            output.extend(r"\item " + inline(item) for item in list_items)
            output.append(rf"\end{{{environment}}}")
            output.append("")
            list_items = []
            list_type = None

    def flush_table() -> None:
        nonlocal table_rows, pending_caption
        if table_rows:
            output.extend(emit_table(table_rows, pending_caption))
            table_rows = []
            pending_caption = None

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            output.extend([r"\begin{quote}", inline(" ".join(quote_lines)), r"\end{quote}", ""])
            quote_lines = []

    for line in lines:
        if in_display_math:
            if line.strip() == "$$":
                output.append(r"\]")
                output.append("")
                in_display_math = False
            else:
                output.append(line)
            continue

        if line.strip() == "$$":
            flush_paragraph()
            flush_list()
            output.append(r"\[")
            in_display_math = True
            continue

        if line.startswith("|"):
            flush_paragraph()
            flush_list()
            flush_quote()
            table_rows.append(line)
            continue
        flush_table()

        if line.startswith("> "):
            flush_paragraph()
            flush_list()
            quote_lines.append(line[2:])
            continue
        flush_quote()

        caption_match = TABLE_CAPTION_RE.fullmatch(line.strip())
        if caption_match:
            flush_paragraph()
            flush_list()
            pending_caption = (caption_match.group(1), caption_match.group(2))
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            flush_list()
            hashes, value = heading_match.groups()
            if not first_heading_seen:
                first_heading_seen = True
                if abstract or appendix:
                    continue
            command = "section" if len(hashes) == 1 or (appendix and len(hashes) == 2) else "subsection"
            if appendix and len(hashes) == 3:
                command = "subsubsection"
            clean_title = heading_title(value)
            output.append(rf"\{command}{{{inline(clean_title)}}}")
            output.append(rf"\label{{sec:{label_prefix}:{slug(clean_title)}}}")
            output.append("")
            continue

        list_match = LIST_RE.match(line)
        if list_match:
            flush_paragraph()
            marker = list_match.group(2)
            current_type = "ordered" if marker.endswith(".") and marker[0].isdigit() else "unordered"
            if list_type and list_type != current_type:
                flush_list()
            list_type = current_type
            list_items.append(list_match.group(3))
            continue

        if list_items and line.startswith("  "):
            list_items[-1] += " " + line.strip()
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_list()
    flush_table()
    flush_quote()
    if in_display_math:
        raise ValueError(f"{path}: unclosed display math")
    return "\n".join(output).rstrip() + "\n"


def main() -> None:
    SECTIONS.mkdir(parents=True, exist_ok=True)
    (SECTIONS / "abstract.tex").write_text(
        convert_markdown(DRAFT / "01_abstract.md", abstract=True), encoding="utf-8"
    )
    for source, target, appendix in CHAPTERS:
        (SECTIONS / target).write_text(
            convert_markdown(DRAFT / source, appendix=appendix), encoding="utf-8"
        )
    shutil.copyfile(DRAFT / "references.bib", LATEX / "references.bib")
    print(f"title={title()}")
    print(f"sections={1 + len(CHAPTERS)}")
    print("bibliography=paper/latex/references.bib")
    print("migration=passed")


if __name__ == "__main__":
    main()
