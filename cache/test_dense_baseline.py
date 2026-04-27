#!/usr/bin/env python3
"""Regression tests for dense embedding retrieval baseline."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "dense_baseline.py"

spec = importlib.util.spec_from_file_location("dense_baseline", MODULE_PATH)
dense_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dense_baseline)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class DenseBaselineTests(unittest.TestCase):
    def test_normalize_embeddings_handles_zero_rows(self):
        embeddings = np.asarray([[3.0, 4.0], [0.0, 0.0]], dtype=np.float32)
        normalized = dense_baseline.normalize_embeddings(embeddings)
        np.testing.assert_allclose(normalized[0], [0.6, 0.8], rtol=1e-6)
        np.testing.assert_allclose(normalized[1], [0.0, 0.0], rtol=1e-6)

    def test_top_k_indices_are_score_descending_and_tie_stable(self):
        indices = dense_baseline.top_k_indices([0.1, 0.5, 0.5, 0.2], 3)
        self.assertEqual(indices, [1, 2, 3])

    def test_run_dense_returns_rankings_and_metrics_for_toy_data(self):
        corpus = [
            {"chunk_id": "c_card", "text": "card document"},
            {"chunk_id": "c_cash", "text": "cash document"},
            {"chunk_id": "c_fee", "text": "fee document"},
        ]
        queries = [
            {"query_id": "q_card", "text": "card query", "ground_truth_chunk_ids": ["c_card"]},
            {"query_id": "q_cash", "text": "cash query", "ground_truth_chunk_ids": ["c_cash"]},
        ]
        encoder = FakeEncoder({
            "card document": [1.0, 0.0],
            "cash document": [0.0, 1.0],
            "fee document": [-1.0, 0.0],
            "card query": [0.9, 0.1],
            "cash query": [0.1, 0.9],
        })

        result = dense_baseline.run_dense(corpus, queries, encoder, top_k=2, ks=(1, 2), batch_size=2)

        self.assertEqual(result["rankings"]["q_card"][0], "c_card")
        self.assertEqual(result["rankings"]["q_cash"][0], "c_cash")
        self.assertEqual(result["metrics"]["num_queries"], 2)
        self.assertAlmostEqual(result["metrics"]["recall@1"], 1.0)
        self.assertAlmostEqual(result["metrics"]["mrr@2"], 1.0)

    def test_run_dense_honors_max_queries_and_max_corpus(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        encoder = FakeEncoder({
            "alpha document": [1.0, 0.0],
            "alpha query": [1.0, 0.0],
        })

        result = dense_baseline.run_dense(
            corpus,
            queries,
            encoder,
            top_k=1,
            ks=(1,),
            batch_size=1,
            max_queries=1,
            max_corpus=1,
        )

        self.assertEqual(list(result["rankings"]), ["q_alpha"])
        self.assertEqual(result["rankings"]["q_alpha"], ["c_alpha"])
        self.assertEqual(result["metrics"]["num_queries"], 1)

    def test_run_dataset_writes_rankings_metrics_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            data_dir.mkdir()
            corpus = [
                {"chunk_id": "c_alpha", "text": "alpha document"},
                {"chunk_id": "c_beta", "text": "beta document"},
            ]
            queries = [
                {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            encoder = FakeEncoder({
                "alpha document": [1.0, 0.0],
                "beta document": [0.0, 1.0],
                "alpha query": [1.0, 0.0],
            })

            metrics = dense_baseline.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                top_k=2,
                ks=(1, 2),
                batch_size=2,
            )
            dense_baseline.update_summary(out_dir / "dense_baseline_summary.csv", [metrics])

            self.assertEqual(metrics["dataset"], "toy")
            self.assertEqual(metrics["method"], "dense")
            self.assertEqual(metrics["model"], "fake-model")
            self.assertTrue((out_dir / "dense_toy_rankings.json").exists())
            self.assertTrue((out_dir / "dense_toy_metrics.json").exists())
            self.assertTrue((out_dir / "dense_baseline_summary.csv").exists())
            self.assertAlmostEqual(metrics["recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
