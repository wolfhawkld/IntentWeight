#!/usr/bin/env python3
"""Validate the Task71.2 aggregate profile and its source-run invariants."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
DEFAULT_PROFILE = ROOT / "paper" / "experiments" / "results" / "task71_2_systems_profile" / "lotte_technology_search_100k_systems_profile_aggregate.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = parser.parse_args()
    profile = read_json(args.profile)
    require(profile.get("task") == "Task71.2", "wrong task identifier")
    require(profile.get("epochs_per_run") == 1, "systems profile must retain one epoch per independent run")
    require(profile.get("independent_runs_per_mode") == 3, "expected three independent runs per feedback mode")
    require(profile.get("cluster_retrieval_engine") == "on_demand", "retrieval engine provenance mismatch")
    require(profile.get("dataset") == "lotte_technology_search_100k", "unexpected dataset")
    require(int(profile.get("num_corpus_chunks", 0)) == 101_311, "unexpected corpus size")
    require(int(profile.get("num_queries", 0)) == 596, "unexpected query count")

    modes: Mapping[str, Mapping[str, Any]] = profile.get("modes", {})
    require(set(modes) == {"none", "trust_weighted"}, "missing feedback modes")
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
    for mode, values in modes.items():
        stages = values.get("stage_timing", {})
        require(required_stages <= set(stages), f"missing stages for {mode}")
        require(values["warm_stream"]["interactions_per_sec"]["min"] > 0, f"non-positive throughput for {mode}")
        for stage in required_stages:
            require(stages[stage]["runs"] == 3, f"wrong run count for {mode}/{stage}")
            require(stages[stage]["calls_per_run"]["min"] > 0, f"zero calls for {mode}/{stage}")
            require(stages[stage]["run_p50_ms"]["min"] >= 0, f"negative p50 for {mode}/{stage}")
            require(stages[stage]["run_p95_ms"]["min"] >= 0, f"negative p95 for {mode}/{stage}")

    trust = modes["trust_weighted"]
    none = modes["none"]
    require("linucb_update" in trust["stage_timing"], "trust profile lacks LinUCB update timing")
    require("linucb_update" not in none["stage_timing"], "no-feedback control unexpectedly updated LinUCB")
    require(trust["feedback_state"]["feedback_context_count"]["min"] == 596, "trust feedback state is incomplete")
    require(none["feedback_state"]["feedback_context_count"]["max"] == 0, "no-feedback control retained feedback state")

    encoding = profile.get("query_encoding", {})
    require(encoding.get("enabled") is True, "missing query encoding microbenchmark")
    require(int(encoding.get("samples", 0)) == 64, "unexpected query encoding sample count")
    require(float(encoding.get("p50_ms", -1)) > 0, "invalid query encoding p50")
    require(float(encoding.get("p95_ms", -1)) >= float(encoding.get("p50_ms", 0)), "invalid query encoding percentiles")

    run_artifacts = profile.get("run_artifacts", {})
    for mode, paths in run_artifacts.items():
        require(len(paths) == 3, f"wrong source-artifact count for {mode}")
        for relative_path in paths:
            path = ROOT / relative_path
            require(path.exists(), f"missing source artifact: {relative_path}")

    report = {
        "task": "Task71.2",
        "status": "pass",
        "checks": 48,
        "dataset": profile["dataset"],
        "runs_per_mode": profile["independent_runs_per_mode"],
        "boundary": "operational overhead only; no real-user RLHF or end-to-end cost claim",
    }
    output = args.profile.with_name(args.profile.stem.replace("_aggregate", "_validation") + ".json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
