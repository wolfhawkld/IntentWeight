#!/usr/bin/env python3
"""Build a portable source manifest for the Task78 colleague handoff."""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
DATA_DIR = EXPERIMENT_DIR / "data"
RESULTS_DIR = EXPERIMENT_DIR / "results"
OUTPUT_DIR = EXPERIMENT_DIR / "reproducibility" / "task78"

DATASETS = (
    "lotte_technology_search_100k",
    "lotte_technology_search_200k",
    "lotte_technology_search_400k",
    "lotte_technology_search_638k",
    "lotte_science_search_20k_q200",
    "lotte_science_search_100k",
    "lotte_science_search_200k",
    "lotte_science_search_400k",
    "lotte_recreation_search_100k",
    "lotte_writing_search_100k",
    "pubmedqa",
    "covidqa",
    "emanual_deduplicated",
    "banking77",
    "cuad",
)

STANDARD_EMBEDDING_PREFIXES = (
    "lotte_technology_search_100k__sentence-transformers-all-MiniLM-L6-v2__",
    "lotte_technology_search_100k__BAAI-bge-base-en-v1.5__",
    "lotte_technology_search_100k__intfloat-e5-base-v2__",
    "lotte_science_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n596__",
    "lotte_science_search_400k__sentence-transformers-all-MiniLM-L6-v2__queries__n596__",
    "lotte_recreation_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n924__",
    "lotte_writing_search_100k__sentence-transformers-all-MiniLM-L6-v2__queries__n1071__",
)

FULL_ARTIFACT_COUNTS = {
    "lotte_technology_search_100k": (101311, 596),
    "lotte_science_search_100k": (102369, 596),
    "lotte_science_search_400k": (400902, 596),
    "lotte_recreation_search_100k": (100714, 924),
    "lotte_writing_search_100k": (100696, 1071),
}

MODEL_SNAPSHOTS = {
    "sentence-transformers/all-MiniLM-L6-v2": (
        "c9745ed1d9f207416be6d2e6f8de32d1f16199bf",
        Path.home()
        / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots"
        / "c9745ed1d9f207416be6d2e6f8de32d1f16199bf",
    ),
    "BAAI/bge-base-en-v1.5": (
        "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
        DATA_DIR
        / "hf_cache/hub/models--BAAI--bge-base-en-v1.5/snapshots"
        / "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
    ),
    "intfloat/e5-base-v2": (
        "f52bf8ec8c7124536f0efb74aca902b2995e5bcd",
        DATA_DIR
        / "hf_cache/hub/models--intfloat--e5-base-v2/snapshots"
        / "f52bf8ec8c7124536f0efb74aca902b2995e5bcd",
    ),
    "cross-encoder/ms-marco-MiniLM-L-6-v2": (
        "c5ee24cb16019beea0893ab7796b1df96625c6b8",
        Path.home()
        / ".cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/snapshots"
        / "c5ee24cb16019beea0893ab7796b1df96625c6b8",
    ),
}

FRESH_ROUTE_GAPS = (
    "technology/search 200k, 400k, and 638k do not all have a current hardened BM25 plus seeds-13/17/19 context-cluster cache set; tracked historical route outputs remain authoritative.",
    "science/search 20k/q200 and 200k do not have a complete current hardened embedding/ranking/cluster/score cache set; processed records and tracked outputs are present.",
    "PubMedQA, eManual, Banking77, and CUAD do not all have complete current hardened BM25/cluster/score caches for a fresh route-engine replay.",
    "The original historical CovidQA embedding cache remains absent, but the replacement canonical branch is complete: pinned ROCm embeddings, Dense/BM25/Hybrid, seeds-13/17/19 trust/no-feedback routes, exact score and cluster caches, cross-fitted budgets, and feedback recovery. Exact reproduction uses this fixed canonical generation; historical artifacts are retained only for comparison.",
)


@dataclass
class Asset:
    path: Path
    categories: set[str] = field(default_factory=set)
    levels: set[int] = field(default_factory=set)
    roles: set[str] = field(default_factory=set)


def run_text(command: Sequence[str]) -> str:
    return subprocess.check_output(command, cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def tracked_files(root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--", repo_relative(root)],
        cwd=REPO_ROOT,
    )
    return [REPO_ROOT / value.decode("utf-8") for value in output.split(b"\0") if value]


def add_asset(
    assets: dict[Path, Asset],
    path: Path,
    *,
    category: str,
    level: int,
    role: str,
) -> None:
    resolved = path.resolve()
    asset = assets.setdefault(resolved, Asset(path=resolved))
    asset.categories.add(category)
    asset.levels.add(level)
    asset.roles.add(role)


def add_tree(
    assets: dict[Path, Asset],
    root: Path,
    *,
    category: str,
    level: int,
    role: str,
) -> None:
    if not root.is_dir():
        return
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        add_asset(assets, path, category=category, level=level, role=role)


def processed_assets(assets: dict[Path, Asset]) -> list[str]:
    missing = []
    for dataset in DATASETS:
        for kind in ("corpus", "queries"):
            path = DATA_DIR / "processed" / f"{dataset}_{kind}.json"
            if path.is_file():
                add_asset(
                    assets,
                    path,
                    category="processed_data",
                    level=2,
                    role=f"ordered {dataset} {kind} records",
                )
            else:
                missing.append(repo_relative(path))
    return missing


def standard_embedding_assets(assets: dict[Path, Asset]) -> None:
    root = DATA_DIR / "embeddings"
    if not root.is_dir():
        return
    for path in sorted(item for item in root.iterdir() if item.is_file()):
        if path.name.startswith(STANDARD_EMBEDDING_PREFIXES):
            add_asset(
                assets,
                path,
                category="embedding_checkpoint",
                level=2,
                role="frozen historical embedding or metadata",
            )


def selected_retrieval_assets(assets: dict[Path, Asset]) -> None:
    root = DATA_DIR / "retrieval_artifacts"
    if not root.is_dir():
        return
    for metadata_path in sorted(root.glob("*.meta.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        dataset = str(metadata.get("dataset", ""))
        expected = FULL_ARTIFACT_COUNTS.get(dataset)
        if expected is None:
            continue
        if (metadata.get("corpus_count"), metadata.get("query_count")) != expected:
            continue
        artifact_path = Path(str(metadata.get("artifact_path", "")))
        if not artifact_path.is_file():
            artifact_path = metadata_path.parent / metadata_path.name.removesuffix(".meta.json")
            if str(metadata.get("artifact_kind")) == "context_clusters":
                artifact_path = artifact_path.with_suffix(".npz")
            elif str(metadata.get("artifact_kind")) == "query_corpus_scores":
                artifact_path = artifact_path.with_suffix(".npy")
            else:
                artifact_path = artifact_path.with_suffix(".json")
        for path in (metadata_path, artifact_path):
            if path.is_file():
                add_asset(
                    assets,
                    path,
                    category="retrieval_checkpoint",
                    level=2,
                    role=f"{dataset} {metadata.get('artifact_kind')} checkpoint",
                )


def external_output_assets(assets: dict[Path, Asset]) -> None:
    add_tree(
        assets,
        RESULTS_DIR / "task63_downstream_llm_evaluation",
        category="fixed_external_output",
        level=2,
        role="frozen answer and primary-judge records",
    )
    for path in sorted(RESULTS_DIR.glob("task65_7_multi_judge_analysis*")):
        if path.is_file():
            add_asset(
                assets,
                path,
                category="fixed_external_output",
                level=2,
                role="frozen multi-judge analysis",
            )


def asset_payload(assets: Iterable[Asset], tracked: set[Path]) -> tuple[list[dict[str, object]], list[str]]:
    output = []
    checksum_lines = []
    for asset in sorted(assets, key=lambda value: repo_relative(value.path)):
        relative = repo_relative(asset.path)
        if not asset.path.is_file():
            output.append({
                "path": relative,
                "status": "missing",
                "categories": sorted(asset.categories),
                "levels": sorted(asset.levels),
                "roles": sorted(asset.roles),
            })
            continue
        digest = sha256_file(asset.path)
        output.append({
            "path": relative,
            "status": "present",
            "bytes": asset.path.stat().st_size,
            "sha256": digest,
            "git_tracked": asset.path in tracked,
            "categories": sorted(asset.categories),
            "levels": sorted(asset.levels),
            "roles": sorted(asset.roles),
        })
        checksum_lines.append(f"{digest}  {relative}")
    return output, checksum_lines


def render_markdown(payload: Mapping[str, object]) -> str:
    summary = payload["summary"]
    readiness = payload["readiness"]
    lines = [
        "# Task78 Handoff Source Manifest",
        "",
        f"- Git commit: `{payload['git']['commit']}`",
        f"- Manifested files: {summary['present_files']:,}",
        f"- Manifested bytes: {summary['present_bytes'] / (1024 ** 3):.2f} GiB",
        f"- Level 1 paper/result regeneration: **{readiness['level1_paper_regeneration']}**",
        f"- Level 2 exact final-result regeneration: **{readiness['level2_final_result_regeneration']}**",
        f"- Level 2 fresh execution of every historical route run: **{readiness['level2_all_fresh_route_runs']}**",
        f"- Level 3 cross-backend encoder verification: **{readiness['level3_encoder_verification']}**",
        "",
        "## Transfer Rule",
        "",
        "For hardware-independent reproduction, transfer the processed records, fixed",
        "embeddings/scale stores, selected retrieval checkpoints, tracked per-query",
        "rankings/results, fixed answer/judge outputs, tokenizer cache, and environment",
        "locks listed by this manifest. Do not transfer `.venv`, `.venv-rocm`, `.env`,",
        "API keys, resumable checkpoints, or the machine-local ROCm installation.",
        "",
        "The tracked result files are authoritative when an original historical cache is",
        "unavailable. Re-encoding on CUDA, ROCm, or CPU is a Level 3 numerical check, not",
        "a byte-identical substitute for the fixed Level 2 boundary.",
        "",
        "## Remaining Fresh-Route Gaps",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["fresh_route_gaps"])
    lines.extend(["", "## Model Snapshots", ""])
    for name, model in payload["model_snapshots"].items():
        lines.append(
            f"- `{name}` @ `{model['revision']}`: "
            f"{'available locally' if model['available'] else 'not available locally'}"
        )
    lines.extend([
        "",
        "Before redistribution, dataset/model licenses and blinded-review constraints",
        "must be checked. The manifest records source files; it does not grant a license",
        "to redistribute model weights or raw restricted datasets.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    assets: dict[Path, Asset] = {}
    missing_processed = processed_assets(assets)

    for path in tracked_files(RESULTS_DIR):
        add_asset(
            assets,
            path,
            category="reference_result",
            level=1,
            role="authoritative tracked paper-facing result",
        )
    add_tree(
        assets,
        RESULTS_DIR / "task78_gpu_revalidation",
        category="reference_result",
        level=1,
        role="Task78 validation evidence",
    )
    add_tree(
        assets,
        RESULTS_DIR / "task78_covidqa_canonical",
        category="reference_result",
        level=1,
        role="provenance-pinned CovidQA canonical results and historical comparison",
    )
    for pattern in ("environment-*.json", "requirements-*-lock.txt", "texlive-installed-lock.txt"):
        for path in sorted(OUTPUT_DIR.glob(pattern)):
            add_asset(
                assets,
                path,
                category="environment_lock",
                level=1,
                role="CPU, ROCm, and TeX environment provenance",
            )
    add_tree(
        assets,
        DATA_DIR / "task78_handoff" / "scale_store",
        category="scale_store_checkpoint",
        level=2,
        role="technology/search canonical MiniLM scale store",
    )
    add_tree(
        assets,
        DATA_DIR / "task78_handoff" / "embeddings",
        category="embedding_checkpoint",
        level=2,
        role="Task78 handoff query/external embedding checkpoints",
    )
    add_tree(
        assets,
        DATA_DIR / "task78_handoff" / "retrieval_artifacts",
        category="retrieval_checkpoint",
        level=2,
        role="Task78 regenerated ranking checkpoints",
    )
    add_tree(
        assets,
        DATA_DIR / "task78_covidqa_canonical",
        category="retrieval_checkpoint",
        level=2,
        role="CovidQA canonical embeddings, rankings, clusters, and exact score cache",
    )
    for store in ("lotte_science_search", "lotte_recreation_search", "lotte_writing_search"):
        add_tree(
            assets,
            DATA_DIR / "scale_store" / store,
            category="scale_store_checkpoint",
            level=2,
            role=f"{store} canonical MiniLM scale store",
        )
    standard_embedding_assets(assets)
    selected_retrieval_assets(assets)
    external_output_assets(assets)
    add_tree(
        assets,
        DATA_DIR / "tiktoken_cache",
        category="tokenizer_checkpoint",
        level=2,
        role="cl100k_base tokenizer cache",
    )

    tracked = {path.resolve() for path in tracked_files(REPO_ROOT)}
    records, checksum_lines = asset_payload(assets.values(), tracked)
    present_records = [record for record in records if record["status"] == "present"]
    missing_records = [record for record in records if record["status"] == "missing"]
    model_snapshots = {
        name: {
            "revision": revision,
            "available": path.is_dir(),
            "path": str(path).replace(str(Path.home()), "$HOME"),
        }
        for name, (revision, path) in MODEL_SNAPSHOTS.items()
    }

    payload = {
        "manifest_version": "task78_handoff_source_manifest_v1",
        "git": {
            "commit": run_text(["git", "rev-parse", "HEAD"]),
            "branch": run_text(["git", "branch", "--show-current"]),
            "dirty": bool(run_text(["git", "status", "--short"])),
        },
        "readiness": {
            "level1_paper_regeneration": "PASS" if not missing_records else "CHECK",
            "level2_final_result_regeneration": "PASS_WITH_DOCUMENTED_NUMERICAL_BOUNDARIES"
            if not missing_processed else "MISSING_PROCESSED_DATA",
            "level2_all_fresh_route_runs": "PARTIAL",
            "level3_encoder_verification": "PASS_WITH_CROSS_BACKEND_NUMERICAL_EQUIVALENCE",
        },
        "summary": {
            "present_files": len(present_records),
            "missing_manifest_files": len(missing_records),
            "missing_processed_files": len(missing_processed),
            "present_bytes": sum(int(record["bytes"]) for record in present_records),
        },
        "missing_processed": missing_processed,
        "fresh_route_gaps": list(FRESH_ROUTE_GAPS),
        "model_snapshots": model_snapshots,
        "assets": records,
    }
    json_path = OUTPUT_DIR / "handoff-source-manifest.json"
    markdown_path = OUTPUT_DIR / "handoff-source-manifest.md"
    checksum_path = OUTPUT_DIR / "SHA256SUMS"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "json": str(json_path),
        "markdown": str(markdown_path),
        "checksums": str(checksum_path),
        "summary": payload["summary"],
        "readiness": payload["readiness"],
    }, indent=2))
    return 0 if not missing_processed and not missing_records else 1


if __name__ == "__main__":
    raise SystemExit(main())
