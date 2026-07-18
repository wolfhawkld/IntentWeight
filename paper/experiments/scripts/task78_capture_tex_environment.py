#!/usr/bin/env python3
"""Capture the exact local TeX toolchain used by the submission builds."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DEFAULT_OUTPUT_DIR = EXPERIMENT_DIR / "reproducibility" / "task78"

REQUIRED_FILES = (
    "lineno.sty",
    "caption.sty",
    "microtype.sty",
    "upquote.sty",
    "stfloats.sty",
    "cas-sc.cls",
    "cas-common.sty",
    "makecell.sty",
    "xstring.sty",
    "footmisc.sty",
    "multirow.sty",
    "colortbl.sty",
    "moreverb.sty",
    "wrapfig.sty",
)


def run_text(command: Sequence[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def portable(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME")


def portable_tree(value):
    if isinstance(value, str):
        return portable(value)
    if isinstance(value, list):
        return [portable_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: portable_tree(item) for key, item in value.items()}
    return value


def command_version(command: str, *args: str) -> dict[str, str]:
    executable = shutil.which(command)
    if executable is None:
        return {"path": "", "version": "", "status": "missing"}
    return {
        "path": portable(executable),
        "version": run_text([executable, *args]),
        "status": "present",
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    installed = run_text(["tlmgr", "info", "--only-installed"])
    lock_path = args.output_dir / "texlive-installed-lock.txt"
    lock_path.write_text(installed + "\n", encoding="utf-8")

    required = {}
    for filename in REQUIRED_FILES:
        resolved = run_text(["kpsewhich", filename])
        required[filename] = {
            "status": "present" if resolved else "missing",
            "path": portable(resolved),
        }

    payload = {
        "git_commit": run_text(["git", "rev-parse", "HEAD"]),
        "tools": {
            "tlmgr": command_version("tlmgr", "--version"),
            "pdflatex": command_version("pdflatex", "--version"),
            "latexmk": command_version("latexmk", "--version"),
            "bibtex": command_version("bibtex", "--version"),
        },
        "texmfroot": portable(run_text(["kpsewhich", "--var-value=TEXMFROOT"])),
        "required_files": required,
        "all_required_present": all(item["status"] == "present" for item in required.values()),
        "lock_file": str(lock_path.relative_to(REPO_ROOT)),
        "lock_sha256": sha256_file(lock_path),
    }
    payload = portable_tree(payload)
    output_path = args.output_dir / "environment-tex.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(output_path),
        "lock": str(lock_path),
        "all_required_present": payload["all_required_present"],
    }, indent=2))
    return 0 if payload["all_required_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
