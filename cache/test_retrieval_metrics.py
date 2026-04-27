#!/usr/bin/env python3
"""Regression tests for retrieval baseline metrics."""
import importlib.util
import math
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "retrieval_metrics.py"

spec = importlib.util.spec_from_file_location("retrieval_metrics", MODULE_PATH)
retrieval_metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retrieval_metrics)


class RetrievalMetricsTests(unittest.TestCase):
    def test_evaluate_rankings_computes_recall_mrr_and_ndcg_at_k(self):
        queries = [
            {"query_id": "q1", "ground_truth_chunk_ids": ["a", "b"]},
            {"query_id": "q2", "ground_truth_chunk_ids": ["x"]},
            {"query_id": "q3", "ground_truth_chunk_ids": ["z"]},
        ]
        rankings = {
            "q1": ["c", "a", "d"],  # first relevant at rank 2; one hit in top 3
            "q2": ["x", "y", "z"],  # first relevant at rank 1
            "q3": ["m", "n", "o"],  # no hit
        }

        metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=(1, 3))

        self.assertEqual(metrics["num_queries"], 3)
        self.assertAlmostEqual(metrics["recall@1"], 1 / 3)
        self.assertAlmostEqual(metrics["recall@3"], 2 / 3)
        self.assertAlmostEqual(metrics["mrr@3"], (1 / 2 + 1 + 0) / 3)

        q1_dcg = 1 / math.log2(2 + 1)
        q1_idcg = 1 + 1 / math.log2(2 + 1)
        expected_ndcg3 = (q1_dcg / q1_idcg + 1 + 0) / 3
        self.assertAlmostEqual(metrics["ndcg@3"], expected_ndcg3)

    def test_empty_ground_truth_queries_are_skipped_by_default(self):
        queries = [
            {"query_id": "q1", "ground_truth_chunk_ids": []},
            {"query_id": "q2", "ground_truth_chunk_ids": ["x"]},
        ]
        rankings = {
            "q1": ["anything"],
            "q2": ["x"],
        }

        metrics = retrieval_metrics.evaluate_rankings(queries, rankings, ks=(1,))

        self.assertEqual(metrics["num_queries"], 1)
        self.assertEqual(metrics["num_skipped_no_gt"], 1)
        self.assertAlmostEqual(metrics["recall@1"], 1.0)
        self.assertAlmostEqual(metrics["mrr@1"], 1.0)
        self.assertAlmostEqual(metrics["ndcg@1"], 1.0)

    def test_missing_ranking_counts_as_zero_score(self):
        queries = [
            {"query_id": "q1", "ground_truth_chunk_ids": ["x"]},
        ]

        metrics = retrieval_metrics.evaluate_rankings(queries, {}, ks=(5,))

        self.assertEqual(metrics["num_queries"], 1)
        self.assertAlmostEqual(metrics["recall@5"], 0.0)
        self.assertAlmostEqual(metrics["mrr@5"], 0.0)
        self.assertAlmostEqual(metrics["ndcg@5"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
