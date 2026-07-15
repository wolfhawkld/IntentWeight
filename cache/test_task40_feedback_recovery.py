#!/usr/bin/env python3
"""Regression tests for Task40 recovery token accounting."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "task40_feedback_recovery.py"

spec = importlib.util.spec_from_file_location("task40_feedback_recovery", MODULE_PATH)
task40 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task40)


class Task40TokenAccountingTests(unittest.TestCase):
    def test_average_tokens_uses_final_top_k_not_cache_depth(self):
        queries = [{"query_id": "q1"}]
        rankings = {"q1": ["a", "b", "cached_tail"]}
        chunk_tokens = {"a": 10, "b": 20, "cached_tail": 10_000}

        self.assertEqual(
            task40.average_tokens(queries, rankings, chunk_tokens, top_k=2),
            30,
        )

    def test_affected_queries_ignore_dense_cache_tail_beyond_top_k(self):
        query = {"query_id": "q1", "ground_truth_chunk_ids": ["tail"]}
        dense_rankings = {"q1": [f"head_{index}" for index in range(10)] + ["tail"]}
        fixed_rankings = {"q1": [f"head_{index}" for index in range(10)]}
        budgeted_rankings = {"q1": ["head_0"]}

        dense_affected, compression_affected = task40.affected_queries(
            [query],
            dense_rankings,
            fixed_rankings,
            budgeted_rankings,
            top_k=10,
        )

        self.assertEqual(dense_affected, [])
        self.assertEqual(compression_affected, [])

    def test_crossfit_policies_follow_calibration_fold_assignments(self):
        queries = [
            {
                "query_id": f"q{index}",
                "metadata": {"original_query_id": str(100 + index)},
            }
            for index in range(6)
        ]
        payload = {
            "protocol": {"fold_salt": "test-fold-salt", "num_folds": 3},
            "fold_selections": [
                {"fold": 0, "intentroute_policy": "token_budget_r0.88_m8"},
                {"fold": 1, "intentroute_policy": "dense_top10_fallback"},
                {"fold": 2, "intentroute_policy": "token_budget_r0.95_m4"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calibration.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            policies, metadata = task40.load_crossfit_query_policies(path, queries)

        self.assertEqual(len(policies), len(queries))
        self.assertEqual(metadata["fold_query_counts"], {"0": 2, "1": 2, "2": 2})
        self.assertEqual(sum(policy is None for policy in policies.values()), 2)
        self.assertEqual(
            sorted(policy for policy in policies.values() if policy is not None),
            sorted([
                task40.BudgetPolicy(0.88, 8),
                task40.BudgetPolicy(0.88, 8),
                task40.BudgetPolicy(0.95, 4),
                task40.BudgetPolicy(0.95, 4),
            ]),
        )

    def test_crossfit_dense_fallback_is_not_recompressed_on_retry(self):
        query = {"query_id": "q1", "ground_truth_chunk_ids": ["gt"]}
        context = task40.SeedContext(
            "13",
            {"q1": 0},
            {"gt": 0, "other": 1},
            task40.np.asarray([[1.0], [0.0]], dtype=task40.np.float32),
        )
        rows, variants = task40.same_query_recovery_rows(
            seed="13",
            queries=[query],
            affected=[query],
            dense_rankings={"q1": ["gt", "other"]},
            fixed_rankings={"q1": ["other", "gt"]},
            budget_rankings={"q1": ["gt", "other"]},
            context=context,
            chunk_tokens={"gt": 5, "other": 5},
            top_k=2,
            budget_ratio=0.85,
            min_keep=1,
            conservative_ratio=0.95,
            query_policies={"q1": None},
        )

        self.assertEqual(rows[0]["affected_count"], 1)
        for rankings in variants.values():
            self.assertEqual(rankings["q1"], ["gt", "other"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
