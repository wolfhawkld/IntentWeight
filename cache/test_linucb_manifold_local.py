#!/usr/bin/env python3
"""Tests for manifold-local LinUCB prequential experiment."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_manifold_local.py"

spec = importlib.util.spec_from_file_location("linucb_manifold_local", MODULE_PATH)
linucb_manifold_local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linucb_manifold_local)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class ManifoldLocalLinUCBTests(unittest.TestCase):
    def test_local_feedback_boosts_nearby_rewarded_arm(self):
        context = np.asarray([1.0, 0.0], dtype=np.float32)
        feedback_contexts = [
            np.asarray([1.0, 0.0], dtype=np.float32),
            np.asarray([0.0, 1.0], dtype=np.float32),
        ]
        feedback_arm_rewards = [
            {0: 1.0},
            {1: 1.0},
        ]

        boosts = linucb_manifold_local.local_feedback_boosts(
            context,
            feedback_contexts,
            feedback_arm_rewards,
            n_arms=2,
            feedback_k=2,
            tau=0.5,
            feedback_weight=0.4,
        )

        self.assertGreater(boosts[0], boosts[1])
        self.assertLessEqual(boosts[0], 0.4)

    def test_arm_propagation_weights_decay_to_neighbors(self):
        centroids = np.asarray([
            [1.0, 0.0],
            [0.8, 0.2],
            [-1.0, 0.0],
        ], dtype=np.float32)
        centroids = linucb_manifold_local.global_linucb.l2_normalize(centroids)

        weights = linucb_manifold_local.arm_propagation_weights(
            centroids,
            0,
            sigma=0.75,
            neighbor_k=2,
            propagation_strength=0.25,
        )

        self.assertEqual(weights[0], (0, 1.0))
        self.assertEqual(weights[1][0], 1)
        self.assertGreater(weights[1][1], 0.0)
        self.assertLess(weights[1][1], 0.25)

    def test_prequential_seed_records_manifold_update_metrics(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        corpus_embeddings = linucb_manifold_local.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ], dtype=np.float32))
        query_embeddings = linucb_manifold_local.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))

        result = linucb_manifold_local.run_prequential_seed(
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
            arm_neighbor_k=2,
            arm_decay_sigma=0.75,
            propagation_strength=0.25,
            feedback_k=2,
            feedback_tau=0.75,
            feedback_weight=0.35,
        )

        self.assertEqual(result["metrics"]["seed"], 7)
        self.assertGreater(result["metrics"]["cross_arm_update_weight"], 0.0)
        self.assertGreater(result["metrics"]["propagated_updates"], 0)
        self.assertIn("q_alpha", result["rankings"])

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

            metrics = linucb_manifold_local.run_dataset(
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
                arm_neighbor_k=2,
                arm_decay_sigma=0.75,
                propagation_strength=0.25,
                feedback_k=2,
                feedback_tau=0.75,
                feedback_weight=0.35,
                query_split="test",
            )
            linucb_manifold_local.update_summary(out_dir / "linucb_manifold_summary.csv", [metrics])

            self.assertEqual(metrics["method"], "linucb_manifold_local")
            self.assertEqual(metrics["online_learning_scope"], "manifold_local_feedback_propagation")
            self.assertEqual(metrics["query_split"], "test")
            self.assertEqual(metrics["num_seeds"], 2)
            self.assertTrue((out_dir / "linucb_manifold_toy_prequential_metrics.json").exists())
            self.assertTrue((out_dir / "linucb_manifold_toy_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_manifold_summary.csv").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
