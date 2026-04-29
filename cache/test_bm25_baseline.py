#!/usr/bin/env python3
"""Regression tests for BM25 retrieval baseline."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "bm25_baseline.py"

spec = importlib.util.spec_from_file_location("bm25_baseline", MODULE_PATH)
bm25_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm25_baseline)


class BM25BaselineTests(unittest.TestCase):
    def test_tokenize_lowercases_and_keeps_alphanumeric_terms(self):
        tokens = bm25_baseline.tokenize("Card-arrival fee: $10, refund?")
        self.assertEqual(tokens, ["card", "arrival", "fee", "10", "refund"])

    def test_top_k_indices_are_score_descending_and_tie_stable(self):
        indices = bm25_baseline.top_k_indices([0.1, 0.5, 0.5, 0.2], 3)
        self.assertEqual(indices, [1, 2, 3])

    def test_top_k_sparse_indices_are_score_descending_and_tie_stable(self):
        indices = bm25_baseline.top_k_sparse_indices({0: 0.1, 1: 0.5, 2: 0.5, 3: 0.2}, 3)
        self.assertEqual(indices, [1, 2, 3])

    def test_sparse_bm25_only_scores_matching_documents(self):
        scorer = bm25_baseline.SparseBM25([
            ["alpha", "beta"],
            ["gamma"],
            ["alpha", "alpha"],
        ])
        scores = scorer.get_scores(["alpha"])
        self.assertEqual(set(scores), {0, 2})
        self.assertGreater(scores[2], scores[0])

    def test_run_bm25_returns_rankings_and_metrics_for_toy_data(self):
        corpus = [
            {"chunk_id": "c_card", "text": "lost card arrival replacement"},
            {"chunk_id": "c_cash", "text": "cash withdrawal from atm"},
            {"chunk_id": "c_fee", "text": "international transfer fee"},
        ]
        queries = [
            {"query_id": "q_card", "text": "where is my card", "ground_truth_chunk_ids": ["c_card"]},
            {"query_id": "q_cash", "text": "atm cash", "ground_truth_chunk_ids": ["c_cash"]},
        ]

        result = bm25_baseline.run_bm25(corpus, queries, top_k=2, ks=(1, 2))

        self.assertEqual(result["rankings"]["q_card"][0], "c_card")
        self.assertEqual(result["rankings"]["q_cash"][0], "c_cash")
        self.assertEqual(result["metrics"]["num_queries"], 2)
        self.assertAlmostEqual(result["metrics"]["recall@1"], 1.0)
        self.assertAlmostEqual(result["metrics"]["mrr@2"], 1.0)

    def test_run_bm25_honors_max_queries(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta", "ground_truth_chunk_ids": ["c_beta"]},
        ]

        result = bm25_baseline.run_bm25(corpus, queries, top_k=1, ks=(1,), max_queries=1)

        self.assertEqual(list(result["rankings"]), ["q_alpha"])
        self.assertEqual(result["metrics"]["num_queries"], 1)

    def test_cli_writes_rankings_metrics_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            data_dir.mkdir()
            corpus = [
                {"chunk_id": "c_alpha", "text": "alpha beta document"},
                {"chunk_id": "c_gamma", "text": "gamma delta document"},
            ]
            queries = [
                {"query_id": "q_alpha", "text": "alpha", "ground_truth_chunk_ids": ["c_alpha"]},
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")

            exit_code = bm25_baseline.main([
                "--dataset", "toy",
                "--data-dir", str(data_dir),
                "--output-dir", str(out_dir),
                "--top-k", "2",
                "--ks", "1,2",
            ])

            self.assertEqual(exit_code, 0)
            rankings_path = out_dir / "bm25_toy_rankings.json"
            metrics_path = out_dir / "bm25_toy_metrics.json"
            summary_path = out_dir / "bm25_baseline_summary.csv"
            self.assertTrue(rankings_path.exists())
            self.assertTrue(metrics_path.exists())
            self.assertTrue(summary_path.exists())
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics["dataset"], "toy")
            self.assertEqual(metrics["method"], "bm25")
            self.assertEqual(metrics["task_type"], "unknown")
            self.assertAlmostEqual(metrics["recall@1"], 1.0)

    def test_run_dataset_filters_query_split_and_marks_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            data_dir.mkdir()
            corpus = [
                {"chunk_id": "c_train", "text": "alpha train"},
                {"chunk_id": "c_test", "text": "beta test"},
            ]
            queries = [
                {"query_id": "q_train", "text": "alpha", "ground_truth_chunk_ids": ["c_train"], "split": "train"},
                {"query_id": "q_test", "text": "beta", "ground_truth_chunk_ids": ["c_test"], "split": "test"},
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")

            metrics = bm25_baseline.run_dataset(
                "toy",
                data_dir,
                out_dir,
                top_k=1,
                ks=(1,),
                query_split="test",
            )

            rankings = json.loads((out_dir / "bm25_toy_rankings.json").read_text(encoding="utf-8"))
            self.assertEqual(list(rankings), ["q_test"])
            self.assertEqual(metrics["query_split"], "test")
            self.assertEqual(metrics["query_scope"], "split_test")
            self.assertEqual(metrics["num_query_candidates"], 1)
            self.assertAlmostEqual(metrics["recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
