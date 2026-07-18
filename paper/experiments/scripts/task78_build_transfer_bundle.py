#!/usr/bin/env python3
"""Create a portable Task78 handoff directory from its verified manifest.

The bundle keeps all large payload files below ``payload/`` using their
repository-relative paths.  It also captures the current Git worktree delta
and the Task78 untracked source files, so the recipient can recreate the
current state even before those changes are committed upstream.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DEFAULT_MANIFEST = EXPERIMENT_DIR / "reproducibility" / "task78" / "handoff-source-manifest.json"
DEFAULT_OUTPUT = (
    EXPERIMENT_DIR
    / "data"
    / "task78_transfer_bundle"
    / "IntentRoute_Task78_handoff_20260718"
)

# These files are deliberately untracked Task78 deliverables, rather than
# unrelated local smoke caches or any sensitive workspace configuration.
UNTRACKED_SOURCE_PATHS = (
    Path("cache/test_task69_cross_fitted_calibration.py"),
    Path("paper/experiments/scripts/task78_build_handoff_checkpoints.py"),
    Path("paper/experiments/scripts/task78_capture_environment.py"),
    Path("paper/experiments/scripts/task78_capture_tex_environment.py"),
    Path("paper/experiments/scripts/task78_compare_covidqa_canonical.py"),
    Path("paper/experiments/scripts/task78_external_checkpoint_audit.py"),
    Path("paper/experiments/scripts/task78_gpu_revalidation.py"),
    Path("paper/experiments/scripts/task78_handoff_manifest.py"),
    Path("paper/experiments/scripts/task78_build_transfer_bundle.py"),
    Path("paper/experiments/task78_cross_machine_reproduction_and_gpu_revalidation_plan.md"),
    Path("paper/experiments/task78_cross_machine_reproduction_and_gpu_revalidation_summary.md"),
    Path("paper/experiments/task79_post_task78_submission_completion_plan.md"),
)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True)


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Manifest path is not repository-relative: {value}")
    return path


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_text(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def metadata_checksums(paths: Iterable[Path], bundle_root: Path) -> str:
    lines = []
    for path in sorted(paths):
        relative = path.relative_to(bundle_root)
        lines.append(f"{sha256_file(path)}  {relative}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output = args.output.resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing Task78 manifest: {manifest_path}")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing bundle: {output}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = payload.get("assets", [])
    present_records = [record for record in records if record.get("status") == "present"]
    if len(present_records) != payload["summary"]["present_files"]:
        raise ValueError("Manifest present-file count does not match its records")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        payload_root = staging / "payload"
        checksum_lines = []
        copied_bytes = 0
        for index, record in enumerate(sorted(present_records, key=lambda item: item["path"]), start=1):
            relative = safe_relative_path(str(record["path"]))
            source = (REPO_ROOT / relative).resolve()
            if not source.is_file() or REPO_ROOT.resolve() not in source.parents:
                raise FileNotFoundError(f"Manifest source is unavailable: {relative}")
            source_digest = sha256_file(source)
            if source_digest != record["sha256"]:
                raise ValueError(f"Source checksum changed since manifest generation: {relative}")
            destination = payload_root / relative
            copy_file(source, destination)
            if sha256_file(destination) != source_digest:
                raise ValueError(f"Copied checksum mismatch: {relative}")
            copied_bytes += source.stat().st_size
            checksum_lines.append(f"{source_digest}  payload/{relative.as_posix()}")
            if index % 100 == 0 or index == len(present_records):
                print(f"copied={index}/{len(present_records)} bytes={copied_bytes}", flush=True)

        source_state = staging / "source-state"
        write_text(source_state / "git-head.txt", run_git("rev-parse", "HEAD"))
        write_text(source_state / "git-status.txt", run_git("status", "--short"))
        write_text(source_state / "tracked-changes.patch", run_git("diff", "--binary", "HEAD"))
        copied_untracked = []
        for relative in UNTRACKED_SOURCE_PATHS:
            source = REPO_ROOT / relative
            if source.is_file():
                copy_file(source, source_state / "untracked" / relative)
                copied_untracked.append(relative.as_posix())

        copied_manifest = staging / "handoff-source-manifest.json"
        copied_manifest_md = staging / "handoff-source-manifest.md"
        copy_file(manifest_path, copied_manifest)
        source_markdown = manifest_path.with_suffix(".md")
        if source_markdown.is_file():
            copy_file(source_markdown, copied_manifest_md)

        write_text(staging / "SHA256SUMS", "\n".join(checksum_lines) + "\n")
        write_text(
            staging / "verify-payload.sh",
            "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\"\nsha256sum --quiet -c SHA256SUMS\nprintf 'Payload SHA256 verification passed.\\n'\n",
            executable=True,
        )
        bundle_info = {
            "bundle_version": "task78_transfer_bundle_v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "head": run_git("rev-parse", "HEAD").strip(),
                "branch": run_git("branch", "--show-current").strip(),
                "dirty": bool(run_git("status", "--short").strip()),
            },
            "payload": {
                "files": len(present_records),
                "bytes": copied_bytes,
                "source_manifest_sha256": sha256_file(manifest_path),
            },
            "untracked_source_files": copied_untracked,
            "restore_order": [
                "Checkout the Git HEAD recorded in source-state/git-head.txt.",
                "Apply source-state/tracked-changes.patch and overlay source-state/untracked/ into the repository root when the Task78 work has not yet been committed upstream.",
                "Overlay payload/ into the repository root.",
                "Run ./verify-payload.sh from this bundle before using the copied artifacts.",
            ],
        }
        write_text(
            staging / "bundle-info.json",
            json.dumps(bundle_info, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        write_text(
            staging / "README.md",
            "# IntentRoute Task78 Transfer Bundle\n\n"
            "This directory is the hardware-independent Task78 handoff payload. "
            "It contains the verified intermediate artifacts required to reproduce "
            "the final paper-facing results without rerunning GPU embedding work.\n\n"
            "## Contents\n\n"
            "- `payload/`: manifest-listed data, fixed embeddings/rankings, score caches, "
            "result records, environment locks, and external judge outputs.\n"
            "- `SHA256SUMS` and `verify-payload.sh`: payload integrity verification.\n"
            "- `handoff-source-manifest.{json,md}`: provenance, readiness, and license notes.\n"
            "- `source-state/`: Git baseline plus the current tracked patch and allowed "
            "untracked Task78 source files.\n\n"
            "## Restore\n\n"
            "1. Check out the commit in `source-state/git-head.txt`.\n"
            "2. If the Task78 work has not yet been committed upstream, apply "
            "`source-state/tracked-changes.patch` and overlay `source-state/untracked/` "
            "into the repository root.\n"
            "3. Overlay `payload/` into that repository root, preserving paths.\n"
            "4. From this bundle root, run `./verify-payload.sh`.\n\n"
            "This bundle excludes virtual environments, `.env`, API keys, local ROCm "
            "binaries, resumable checkpoints, and model-weight snapshots. Fetch model "
            "weights by the pinned revisions recorded in the source manifest.\n",
        )
        metadata_paths = [
            staging / "README.md",
            staging / "bundle-info.json",
            staging / "handoff-source-manifest.json",
            staging / "SHA256SUMS",
            staging / "verify-payload.sh",
            source_state / "git-head.txt",
            source_state / "git-status.txt",
            source_state / "tracked-changes.patch",
        ]
        if copied_manifest_md.is_file():
            metadata_paths.append(copied_manifest_md)
        metadata_paths.extend(source_state / "untracked" / path for path in map(Path, copied_untracked))
        write_text(staging / "METADATA_SHA256SUMS", metadata_checksums(metadata_paths, staging))

        staging.rename(output)
        print(json.dumps({
            "bundle": str(output),
            "payload_files": len(present_records),
            "payload_bytes": copied_bytes,
            "untracked_source_files": len(copied_untracked),
        }, indent=2))
        return 0
    except Exception:
        print(f"Bundle staging retained for inspection: {staging}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
