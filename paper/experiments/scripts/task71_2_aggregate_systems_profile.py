#!/usr/bin/env python3
"""Aggregate independently collected Task71.2 operational profile runs."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DEFAULT_RUN_ROOT = ROOT / "paper" / "experiments" / "results" / "task71_2_systems_profile_runs_v2"
DEFAULT_OUTPUT_DIR = ROOT / "paper" / "experiments" / "results" / "task71_2_systems_profile"
RUN_DIRECTORY_NAMES = {"none": "none", "trust_weighted": "trust"}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def summarize(values: Iterable[float | int]) -> dict[str, float | int]:
    items = [float(value) for value in values]
    if not items:
        raise ValueError("cannot summarize an empty sequence")
    return {
        "median": round(float(median(items)), 4),
        "min": round(min(items), 4),
        "max": round(max(items), 4),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_paths(run_root: Path, dataset: str, mode: str, expected_runs: int) -> list[Path]:
    directory_prefix = RUN_DIRECTORY_NAMES[mode]
    pattern = re.compile(rf"^{re.escape(directory_prefix)}_(\d+)$")
    candidates: list[tuple[int, Path]] = []
    for directory in run_root.iterdir():
        if not directory.is_dir():
            continue
        match = pattern.fullmatch(directory.name)
        if match is None:
            continue
        path = directory / f"{dataset}_systems_profile.json"
        if path.exists():
            candidates.append((int(match.group(1)), path))
    candidates.sort(key=lambda item: item[0])
    require(len(candidates) == expected_runs, f"expected {expected_runs} {mode} runs under {run_root}, found {len(candidates)}")
    require([index for index, _ in candidates] == list(range(1, expected_runs + 1)), f"non-contiguous {mode} run indices")
    return [path for _, path in candidates]


def validate_run(payload: Mapping[str, Any], *, path: Path, dataset: str, mode: str) -> Mapping[str, Any]:
    require(payload.get("task") == "Task71.2", f"unexpected task in {path}")
    require(payload.get("dataset") == dataset, f"dataset mismatch in {path}")
    require(payload.get("epochs") == 1 and payload.get("repetitions") == 1, f"Task71.2 profile must be one epoch/run: {path}")
    require(payload.get("cluster_retrieval_engine") == "on_demand", f"unexpected retrieval engine in {path}")
    profiles = payload.get("online_profiles", {})
    require(list(profiles) == [mode], f"feedback mode mismatch in {path}")
    online = profiles[mode]
    require(int(online.get("interactions", 0)) == int(payload.get("num_queries", 0)), f"interaction count mismatch in {path}")
    require(float(online.get("stream_elapsed_ms", -1.0)) > 0.0, f"non-positive elapsed time in {path}")
    required_stages = {
        "routing_and_gating",
        "dense_route",
        "bm25_route",
        "cluster_route",
        "fusion_and_dense_floor",
        "final_context_budget",
        "feedback_reward_measurement",
        "feedback_observation",
        "feedback_trust_weighting",
        "feedback_state_update",
        "feedback_memory_append",
    }
    stage_timings = online.get("stage_timings", {})
    require(required_stages <= set(stage_timings), f"missing stage timing in {path}")
    if mode == "trust_weighted":
        require("linucb_update" in stage_timings, f"missing LinUCB updates in {path}")
        require(int(online["feedback_state"].get("feedback_context_count", 0)) > 0, f"missing feedback memory in {path}")
    else:
        require("linucb_update" not in stage_timings, f"unexpected LinUCB updates in no-feedback control: {path}")
        require(int(online["feedback_state"].get("feedback_context_count", 0)) == 0, f"no-feedback control retained feedback memory: {path}")
    return online


def summarize_stages(runs: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    stage_names = sorted({name for run in runs for name in run["stage_timings"]})
    output: dict[str, dict[str, Any]] = {}
    for stage in stage_names:
        values = [run["stage_timings"][stage] for run in runs if stage in run["stage_timings"]]
        output[stage] = {
            "runs": len(values),
            "calls_per_run": summarize(value["calls"] for value in values),
            "total_ms_per_run": summarize(value["total_ms"] for value in values),
            "run_p50_ms": summarize(value["p50_ms"] for value in values if value["p50_ms"] is not None),
            "run_p95_ms": summarize(value["p95_ms"] for value in values if value["p95_ms"] is not None),
            "run_max_ms": summarize(value["max_ms"] for value in values if value["max_ms"] is not None),
        }
    return output


def summarize_mode(runs: list[Mapping[str, Any]], payloads: list[Mapping[str, Any]]) -> dict[str, Any]:
    state_rows = [run["feedback_state"] for run in runs]
    return {
        "runs": len(runs),
        "warm_stream": {
            "elapsed_ms_per_run": summarize(run["stream_elapsed_ms"] for run in runs),
            "interactions_per_sec": summarize(run["interactions_per_sec"] for run in runs),
            "peak_rss_bytes_per_run": summarize(payload["peak_rss_bytes"] for payload in payloads),
        },
        "stage_timing": summarize_stages(runs),
        "feedback_state": {
            "feedback_context_count": summarize(row["feedback_context_count"] for row in state_rows),
            "feedback_reward_record_count": summarize(row["feedback_reward_record_count"] for row in state_rows),
            "in_memory_numeric_bytes": summarize(row["in_memory_numeric_bytes"] for row in state_rows),
            "snapshot_pickle_bytes": summarize(row["snapshot_pickle_bytes"] for row in state_rows),
            "snapshot_serialize_ms": summarize(row["snapshot_serialize_ms"] for row in state_rows),
            "snapshot_deserialize_ms": summarize(row["snapshot_deserialize_ms"] for row in state_rows),
        },
    }


def markdown(path: Path, profile: Mapping[str, Any]) -> None:
    lines = [
        "# Task71.2 Systems and Feedback Operational Profile",
        "",
        f"Dataset: `{profile['dataset']}`. Corpus: {profile['num_corpus_chunks']:,} chunks; queries: {profile['num_queries']:,}.",
        "",
        "## Measurement Protocol",
        "",
        "- Three independent CPU processes per feedback mode; one prequential epoch per process.",
        "- MiniLM artifacts were pre-existing and loaded from local cache. Dense and BM25 routes are cached ranking lookups; cluster-local retrieval uses the declared `on_demand` exact scorer.",
        "- The common full multi-route policy is held fixed. This is an operational profile, not a retrieval-quality comparison or a real-user RLHF evaluation.",
        "- Per-stage p50/p95 values are first computed within each run, then summarized across the three runs; they are not pooled into a synthetic request-level distribution.",
        "",
        "## Warm Online Workload",
        "",
        "| Feedback mode | Median stream wall ms (range) | Median interactions/s (range) | Median peak RSS GiB (range) |",
        "|---|---:|---:|---:|",
    ]
    for mode, values in profile["modes"].items():
        warm = values["warm_stream"]
        rss = warm["peak_rss_bytes_per_run"]
        lines.append(
            f"| `{mode}` | {warm['elapsed_ms_per_run']['median']:.2f} "
            f"({warm['elapsed_ms_per_run']['min']:.2f}-{warm['elapsed_ms_per_run']['max']:.2f}) | "
            f"{warm['interactions_per_sec']['median']:.2f} "
            f"({warm['interactions_per_sec']['min']:.2f}-{warm['interactions_per_sec']['max']:.2f}) | "
            f"{rss['median'] / 1024**3:.3f} ({rss['min'] / 1024**3:.3f}-{rss['max'] / 1024**3:.3f}) |"
        )
    lines.extend([
        "",
        "## Stage Timing",
        "",
        "Values are medians of run-level timing summaries. Stage p95 is a within-run p95, then the median across runs.",
        "",
    ])
    for mode, values in profile["modes"].items():
        lines.extend([
            f"### `{mode}`",
            "",
            "| Stage | Calls/run | p50 ms | p95 ms | Total ms/run |",
            "|---|---:|---:|---:|---:|",
        ])
        for stage, stats in values["stage_timing"].items():
            calls = stats["calls_per_run"]
            p50 = stats["run_p50_ms"]
            p95 = stats["run_p95_ms"]
            total = stats["total_ms_per_run"]
            lines.append(
                f"| {stage} | {calls['median']:.0f} | {p50['median']:.4f} | "
                f"{p95['median']:.4f} | {total['median']:.4f} |"
            )
        state = values["feedback_state"]
        lines.extend([
            "",
            f"Feedback-state median: {state['feedback_context_count']['median']:.0f} contexts; "
            f"{state['in_memory_numeric_bytes']['median']:.0f} numeric bytes; "
            f"{state['snapshot_pickle_bytes']['median']:.0f}-byte snapshot.",
            "",
        ])
    encoding = profile.get("query_encoding", {})
    if encoding.get("enabled"):
        lines.extend([
            "## Query-Encoding Microbenchmark",
            "",
            f"MiniLM CPU load: {encoding['model_load_ms']:.2f} ms; "
            f"{encoding['samples']} single-query samples, p50 {encoding['p50_ms']:.4f} ms, p95 {encoding['p95_ms']:.4f} ms.",
            "",
        ])
    lines.extend([
        "## Interpretation Boundary",
        "",
        "- Cluster-local retrieval dominates the measured warm route. The trust-weighting and individual LinUCB-update stages are reported separately rather than attributed to retrieval quality.",
        "- The `none` control still constructs controlled synthetic observations for a comparable diagnostic path, but assigns zero update weight: it performs no LinUCB update and retains no feedback-memory records.",
        "- Trust-weighted versus `none` wall-time runs are independent process launches, not a paired latency significance test; changing system load can affect their absolute difference.",
        "- The feedback snapshot uses pickle only as a state-size microbenchmark. It is not a production persistence protocol.",
        "- This operational profile does not establish real-user RLHF efficacy. Task72 remains the controlled recurrent-feedback effectiveness evaluation.",
        "- Final-context token savings and conditional LLM input-cost calculations remain traceable to the calibrated Task69 evidence, not to this fixed-top-k operational workload.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, profile: Mapping[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for mode, values in profile["modes"].items():
        for stage, stats in values["stage_timing"].items():
            rows.append({
                "feedback_mode": mode,
                "stage": stage,
                "runs": stats["runs"],
                "calls_per_run_median": stats["calls_per_run"]["median"],
                "stage_p50_ms_median_of_runs": stats["run_p50_ms"]["median"],
                "stage_p95_ms_median_of_runs": stats["run_p95_ms"]["median"],
                "total_ms_per_run_median": stats["total_ms_per_run"]["median"],
            })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="lotte_technology_search_100k")
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--expected-runs", type=int, default=3)
    parser.add_argument("--query-encoding-profile", type=Path, default=None)
    args = parser.parse_args()
    require(args.expected_runs > 0, "expected-runs must be positive")
    args.run_root = args.run_root.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.query_encoding_profile is not None:
        args.query_encoding_profile = args.query_encoding_profile.resolve()

    mode_payloads: dict[str, list[dict[str, Any]]] = {}
    mode_online_runs: dict[str, list[Mapping[str, Any]]] = {}
    all_paths: dict[str, list[Path]] = {}
    for mode in RUN_DIRECTORY_NAMES:
        paths = run_paths(args.run_root, args.dataset, mode, args.expected_runs)
        payloads = [read_json(path) for path in paths]
        online_runs = [validate_run(payload, path=path, dataset=args.dataset, mode=mode) for payload, path in zip(payloads, paths)]
        mode_payloads[mode] = payloads
        mode_online_runs[mode] = online_runs
        all_paths[mode] = paths

    reference = mode_payloads["none"][0]
    for mode, payloads in mode_payloads.items():
        for payload in payloads:
            for key in ("model", "num_corpus_chunks", "num_queries", "seed", "epochs", "repetitions", "cluster_retrieval_engine"):
                require(payload.get(key) == reference.get(key), f"{key} mismatch across runs ({mode})")
            require(payload.get("hardware") == reference.get("hardware"), f"hardware metadata mismatch across runs ({mode})")

    query_encoding: dict[str, Any] = {"enabled": False}
    if args.query_encoding_profile is not None:
        encoding_payload = read_json(args.query_encoding_profile)
        require(encoding_payload.get("dataset") == args.dataset, "query encoding dataset mismatch")
        require(encoding_payload.get("model") == reference.get("model"), "query encoding model mismatch")
        query_encoding = dict(encoding_payload.get("query_encoding", {}))

    profile = {
        "task": "Task71.2",
        "purpose": "artifact-backed operational profile; controller overhead only",
        "dataset": args.dataset,
        "model": reference["model"],
        "num_corpus_chunks": reference["num_corpus_chunks"],
        "num_queries": reference["num_queries"],
        "seed": reference["seed"],
        "epochs_per_run": 1,
        "independent_runs_per_mode": args.expected_runs,
        "cluster_retrieval_engine": reference["cluster_retrieval_engine"],
        "hardware": reference["hardware"],
        "run_artifacts": {
            mode: [str(path.relative_to(ROOT)) for path in paths]
            for mode, paths in all_paths.items()
        },
        "modes": {
            mode: summarize_mode(mode_online_runs[mode], mode_payloads[mode])
            for mode in RUN_DIRECTORY_NAMES
        },
        "cold_artifact_load_ms_per_run": {
            name: summarize(payload["cold_artifact_load_ms"][name] for payload in mode_payloads["none"] + mode_payloads["trust_weighted"])
            for name in sorted(reference["cold_artifact_load_ms"])
        },
        "cache_disk_bytes": reference["cache_disk_bytes"],
        "historical_offline_metadata": reference["historical_offline_metadata"],
        "query_encoding": query_encoding,
        "interpretation_boundary": [
            "The workload profiles cached-artifact online routing, not offline preprocessing or an end-to-end service.",
            "The fixed top-k route workload is not the calibrated final-context token evaluation.",
            "Feedback measurements establish local operational overhead, not real-user RLHF effectiveness.",
            "Mode-specific wall times are unpaired independent process measurements and are not a latency significance test.",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.output_dir / f"{args.dataset}_systems_profile_aggregate"
    write_json_atomic(prefix.with_suffix(".json"), profile)
    write_csv(prefix.with_suffix(".csv"), profile)
    markdown(prefix.with_suffix(".md"), profile)
    print(f"aggregate_json={prefix.with_suffix('.json')}")
    print(f"aggregate_csv={prefix.with_suffix('.csv')}")
    print(f"aggregate_markdown={prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
