#!/usr/bin/env python3
"""Regression tests for Task40 recovery token accounting."""
import importlib.util
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
