#!/usr/bin/env python3
"""Capture exact Task78 CPU or ROCm environment provenance."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DEFAULT_OUTPUT_DIR = EXPERIMENT_DIR / "reproducibility" / "task78"


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_text(command: Sequence[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()


def portable(value: str) -> str:
    home = str(Path.home())
    return value.replace(home, "$HOME")


def portable_tree(value):
    if isinstance(value, str):
        return portable(value)
    if isinstance(value, list):
        return [portable_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: portable_tree(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", choices=("cpu", "rocm"), required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    import numpy as np
    import scipy
    import sklearn
    import sentence_transformers
    import threadpoolctl
    import torch
    import transformers

    args.output_dir.mkdir(parents=True, exist_ok=True)
    freeze = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze", "--all"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    lock_path = args.output_dir / f"requirements-{args.name}-lock.txt"
    lock_path.write_text(freeze + "\n", encoding="utf-8")

    config_buffer = io.StringIO()
    with contextlib.redirect_stdout(config_buffer):
        np.show_config()
    git_commit = run_text(["git", "rev-parse", "HEAD"])
    git_status = run_text(["git", "status", "--short"])
    gpu_available = bool(torch.cuda.is_available())
    activation = REPO_ROOT / ".venv-rocm" / "bin" / "activate-rocm"
    rocdxg = Path.home() / ".local" / "rocdxg" / "lib" / "librocdxg.so.1.2.0"
    payload = {
        "environment": args.name,
        "git_commit": git_commit,
        "git_dirty": bool(git_status),
        "python": platform.python_version(),
        "python_executable": portable(sys.executable),
        "platform": platform.platform(),
        "kernel": run_text(["uname", "-a"]),
        "machine": platform.machine(),
        "packages": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
            "torch_hip": torch.version.hip,
            "transformers": transformers.__version__,
            "sentence_transformers": sentence_transformers.__version__,
        },
        "numpy_config": config_buffer.getvalue(),
        "threadpools": threadpoolctl.threadpool_info(),
        "gpu": {
            "available": gpu_available,
            "count": torch.cuda.device_count() if gpu_available else 0,
            "device": torch.cuda.get_device_name(0) if gpu_available else "",
        },
        "rocm": {
            "rocm_path": portable(os.environ.get("ROCM_PATH", "")),
            "hsa_enable_dxg_detection": os.environ.get("HSA_ENABLE_DXG_DETECTION", ""),
            "ld_library_path": portable(os.environ.get("LD_LIBRARY_PATH", "")),
            "dxg_visible": Path("/dev/dxg").exists(),
            "activation_sha256": sha256_file(activation) if activation.exists() else "",
            "rocdxg_sha256": sha256_file(rocdxg) if rocdxg.exists() else "",
        },
        "lock_file": str(lock_path.relative_to(REPO_ROOT)),
        "lock_sha256": sha256_file(lock_path),
    }
    payload = portable_tree(payload)
    output_path = args.output_dir / f"environment-{args.name}.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "environment": args.name,
        "output": str(output_path),
        "lock": str(lock_path),
        "gpu": payload["gpu"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
