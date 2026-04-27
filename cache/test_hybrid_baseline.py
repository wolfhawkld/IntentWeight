#!/usr/bin/env python3
"""Regression tests for hybrid BM25 + dense retrieval baseline."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "hybrid_baseline.py"

spec = importlib.util.spec_from_file_location("hybrid_baseline", MODULE_PATH)
hybrid_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hybrid_baseline)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class HybridBaselineTests(unittest.TestCase):
    def test_reciprocal_rank_fusion_combines_rankings_with_stable_ties(self):
        fused = hybrid_baseline.reciprocal_rank_fusion(
            [
                ["c_shared", "c_lexical", "c_dense"],
                ["c_dense", "c_shared", "c_other"],
            ],
            rrf_k=60,
            top_k=3,
        )

        self.assertEqual(fused[0], "c_shared")
        self.assertEqual(set(fused[1:]), {"c_dense", "c_lexical"})

    def test_run_hybrid_returns_rrf_rankings_and_metrics_for_toy_data(self):
        corpus = [
            {"chunk_id": "c_card", "text": "lost card arrival replacement"},
            {"chunk_id": "c_cash", "text": "cash withdrawal from atm"},
            {"chunk_id": "c_fee", "text": "international transfer fee"},
        ]
        queries = [
            {"query_id": "q_card", "text": "where is my card", "ground_truth_chunk_ids": ["c_card"]},
            {"query_id": "q_cash", "text": "atm cash", "ground_truth_chunk_ids": ["c_cash"]},
        ]
        encoder = FakeEncoder({
            "lost card arrival replacement": [1.0, 0.0],
            "cash withdrawal from atm": [0.0, 1.0],
            "international transfer fee": [-1.0, 0.0],
            "where is my card": [0.9, 0.1],
            "atm cash": [0.1, 0.9],
        })

        result = hybrid_baseline.run_hybrid(corpus, queries, encoder, top_k=2, ks=(1, 2), batch_size=2)

        self.assertEqual(result["rankings"]["q_card"][0], "c_card")
        self.assertEqual(result["rankings"]["q_cash"][0], "c_cash")
        self.assertEqual(result["metrics"]["num_queries"], 2)
        self.assertAlmostEqual(result["metrics"]["recall@1"], 1.0)
        self.assertAlmostEqual(result["metrics"]["mrr@2"], 1.0)

    def test_run_hybrid_honors_max_queries_and_max_corpus(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        encoder = FakeEncoder({
            "alpha document": [1.0, 0.0],
            "alpha": [1.0, 0.0],
        })

        result = hybrid_baseline.run_hybrid(
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
                {"query_id": "q_alpha", "text": "alpha", "ground_truth_chunk_ids": ["c_alpha"]},
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            encoder = FakeEncoder({
                "alpha document": [1.0, 0.0],
                "beta document": [0.0, 1.0],
                "alpha": [1.0, 0.0],
            })

            metrics = hybrid_baseline.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                top_k=2,
                ks=(1, 2),
                batch_size=2,
                rrf_k=60,
            )
            hybrid_baseline.update_summary(out_dir / "hybrid_baseline_summary.csv", [metrics])

            self.assertEqual(metrics["dataset"], "toy")
            self.assertEqual(metrics["method"], "hybrid_rrf")
            self.assertEqual(metrics["model"], "fake-model")
            self.assertTrue((out_dir / "hybrid_toy_rankings.json").exists())
            self.assertTrue((out_dir / "hybrid_toy_metrics.json").exists())
            self.assertTrue((out_dir / "hybrid_baseline_summary.csv").exists())
            self.assertAlmostEqual(metrics["recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
