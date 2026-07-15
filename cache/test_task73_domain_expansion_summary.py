#!/usr/bin/env python3
"""Unit tests for Task73 domain-property statistics."""
import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "task73_domain_expansion_summary.py"
spec = importlib.util.spec_from_file_location("task73_domain_expansion_summary", MODULE_PATH)
task73 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task73)


class Task73DomainExpansionSummaryTests(unittest.TestCase):
    def test_lexical_metrics_use_best_positive_without_pooling_queries(self):
        corpus = [
            {"chunk_id": "c1", "text": "alpha beta gamma"},
            {"chunk_id": "c2", "text": "unrelated evidence"},
        ]
        queries = [
            {
                "query_id": "q1",
                "text": "alpha beta",
                "ground_truth_chunk_ids": ["c2", "c1"],
            }
        ]

        rows = task73.lexical_query_metrics(corpus, queries)

        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["query_token_coverage"], 1.0)
        self.assertAlmostEqual(rows[0]["jaccard"], 2.0 / 3.0)

    def test_independent_bootstrap_difference_is_reproducible(self):
        first = task73.bootstrap_independent_difference_ci(
            [1.0, 0.9, 0.8], [0.2, 0.1, 0.0], seed=73, samples=500
        )
        second = task73.bootstrap_independent_difference_ci(
            [1.0, 0.9, 0.8], [0.2, 0.1, 0.0], seed=73, samples=500
        )

        self.assertEqual(first, second)
        self.assertGreater(first[0], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
