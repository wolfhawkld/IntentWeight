#!/usr/bin/env python3
"""Tests for global LinUCB prequential retrieval baseline."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_online_baseline.py"

spec = importlib.util.spec_from_file_location("linucb_online_baseline", MODULE_PATH)
linucb_online_baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linucb_online_baseline)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class LinUCBOnlineBaselineTests(unittest.TestCase):
    def test_retrieve_from_selected_arms_only(self):
        corpus_embeddings = np.asarray([
            [1.0, 0.0],
            [0.9, 0.1],
            [0.0, 1.0],
        ], dtype=np.float32)
        chunk_ids = ["c_a", "c_b", "c_c"]
        arm_labels = np.asarray([0, 0, 1], dtype=np.int32)

        ranking = linucb_online_baseline.retrieve_from_arms(
            np.asarray([1.0, 0.0], dtype=np.float32),
            corpus_embeddings,
            chunk_ids,
            arm_labels,
            [0],
            top_k=3,
        )

        self.assertEqual(ranking, ["c_a", "c_b"])

    def test_prequential_seed_returns_metrics_and_updates_feedback(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        corpus_embeddings = linucb_online_baseline.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ], dtype=np.float32))
        query_embeddings = linucb_online_baseline.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))

        result = linucb_online_baseline.run_prequential_seed(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            seed=7,
            top_k=1,
            ks=(1,),
            n_clusters=2,
            context_dim=2,
            candidate_arms=2,
            alpha=1.0,
            alpha_decay=0.01,
            alpha_min=0.3,
        )

        self.assertEqual(result["metrics"]["seed"], 7)
        self.assertEqual(result["metrics"]["num_queries"], 2)
        self.assertEqual(result["metrics"]["total_feedback_updates"], 4)
        self.assertIn("q_alpha", result["rankings"])

    def test_aggregate_seed_metrics_reports_mean_and_std(self):
        aggregated = linucb_online_baseline.aggregate_seed_metrics([
            {"seed": 1, "recall@10": 0.5, "avg_feedback_reward": 0.2},
            {"seed": 2, "recall@10": 1.0, "avg_feedback_reward": 0.4},
        ])

        self.assertEqual(aggregated["num_seeds"], 2)
        self.assertAlmostEqual(aggregated["recall@10_mean"], 0.75)
        self.assertAlmostEqual(aggregated["avg_feedback_reward_mean"], 0.3)

    def test_run_dataset_writes_metrics_rankings_and_summary(self):
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
                {
                    "query_id": "q_alpha",
                    "text": "alpha query",
                    "ground_truth_chunk_ids": ["c_alpha"],
                    "split": "test",
                },
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            encoder = FakeEncoder({
                "alpha document": [1.0, 0.0],
                "beta document": [0.0, 1.0],
                "alpha query": [1.0, 0.0],
            })

            metrics = linucb_online_baseline.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                top_k=1,
                ks=(1,),
                batch_size=2,
                seeds=(1, 2),
                n_clusters=2,
                context_dim=2,
                candidate_arms=2,
                alpha=1.0,
                alpha_decay=0.01,
                alpha_min=0.3,
                query_split="test",
            )
            linucb_online_baseline.update_summary(out_dir / "linucb_online_summary.csv", [metrics])

            self.assertEqual(metrics["method"], "linucb_global")
            self.assertEqual(metrics["protocol"], "prequential")
            self.assertEqual(metrics["query_split"], "test")
            self.assertEqual(metrics["num_seeds"], 2)
            self.assertTrue((out_dir / "linucb_toy_prequential_metrics.json").exists())
            self.assertTrue((out_dir / "linucb_toy_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_online_summary.csv").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
