#!/usr/bin/env python3
"""Render and audit the compiled ACL-style IntentRoute PDF."""

from __future__ import annotations

import shutil
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "paper" / "latex" / "main.pdf"
LOG = ROOT / "paper" / "latex" / "main.log"
OUTPUT = Path("/tmp/intentroute_pdf_audit")
RENDER_SCALE = 1.1
CRITICAL_LOG_RE = re.compile(
    r"Overfull|undefined citations|undefined references|Missing character|"
    r"LaTeX Warning: Reference|Package natbib Warning: Citation|"
    r"Fatal error|Emergency stop|Illegal, another"
)


def render_page(page: fitz.Page, index: int) -> tuple[Path, float]:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False)
    path = OUTPUT / f"page_{index + 1:02d}.png"
    pixmap.save(path)
    image = Image.open(path).convert("L")
    histogram = image.histogram()
    non_white = sum(histogram[:245])
    foreground_ratio = non_white / (image.width * image.height)
    return path, foreground_ratio


def contact_sheet(paths: list[Path], name: str) -> Path:
    thumbnails: list[Image.Image] = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((250, 330))
        thumbnails.append(image)

    columns = 5
    rows = (len(thumbnails) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 270, rows * 370), "white")
    draw = ImageDraw.Draw(sheet)
    for index, image in enumerate(thumbnails):
        x = (index % columns) * 270 + 10
        y = (index // columns) * 370 + 25
        sheet.paste(image, (x, y))
        draw.text((x, 5 + (index // columns) * 370), paths[index].stem, fill="black")

    output = OUTPUT / name
    sheet.save(output)
    return output


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"missing compiled PDF: {PDF.relative_to(ROOT)}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    document = fitz.open(PDF)
    paths: list[Path] = []
    references_page: int | None = None
    appendix_page: int | None = None
    print(f"pdf={PDF.relative_to(ROOT)}")
    print(f"pages={document.page_count}")
    for index, page in enumerate(document):
        text = page.get_text()
        if references_page is None and "References" in text:
            references_page = index + 1
        if appendix_page is None and "Seed Stability Diagnostics" in text:
            appendix_page = index + 1
        path, foreground_ratio = render_page(page, index)
        paths.append(path)
        print(
            f"page={index + 1:02d} chars={len(text):04d} "
            f"foreground_ratio={foreground_ratio:.4f}"
        )
        if foreground_ratio < 0.005:
            raise SystemExit(f"page {index + 1} appears blank")

    first = contact_sheet(paths[:10], "contact_sheet_01_10.png")
    second = contact_sheet(paths[10:], "contact_sheet_11_end.png")
    log_text = LOG.read_text(encoding="utf-8", errors="replace")
    critical_log_lines = [
        line for line in log_text.splitlines() if CRITICAL_LOG_RE.search(line)
    ]
    references_rect = document[references_page - 1].search_for("References")[0] if references_page else None
    appendix_rect = (
        document[appendix_page - 1].search_for("Seed Stability Diagnostics")[0]
        if appendix_page
        else None
    )
    print(f"references_page={references_page}")
    print(f"appendix_page={appendix_page}")
    if references_rect is not None:
        print(f"references_y={references_rect.y0:.1f}")
    if appendix_rect is not None:
        print(f"appendix_y={appendix_rect.y0:.1f}")
    print(f"critical_log_lines={len(critical_log_lines)}")
    print(f"contact_sheet={first}")
    print(f"contact_sheet={second}")
    if critical_log_lines:
        for line in critical_log_lines:
            print(f"log_error={line}")
        raise SystemExit("compiled PDF has critical LaTeX log warnings")
    print("pdf_audit=passed")


if __name__ == "__main__":
    main()
