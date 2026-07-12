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

    def test_cached_arm_score_retrieval_matches_legacy_with_interleaved_arms_and_ties(self):
        corpus_embeddings = np.asarray([
            [1.0, 0.0],
            [0.5, 0.0],
            [1.0, 0.0],
            [0.5, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32)
        chunk_ids = ["c0", "c1", "c2", "c3", "c4"]
        arm_labels = np.asarray([1, 0, 1, 0, 2], dtype=np.int32)
        query = np.asarray([1.0, 0.0], dtype=np.float32)

        legacy = linucb_online_baseline.retrieve_from_arms(
            query,
            corpus_embeddings,
            chunk_ids,
            arm_labels,
            [1, 0],
            top_k=3,
        )
        cached = linucb_online_baseline.retrieve_from_arm_score_cache(
            corpus_embeddings @ query,
            chunk_ids,
            linucb_online_baseline.build_arm_row_indices(arm_labels),
            [1, 0],
            top_k=3,
        )

        self.assertEqual(legacy, ["c0", "c2", "c1"])
        self.assertEqual(cached, legacy)

    def test_cached_arm_score_retrieval_matches_legacy_for_random_embeddings(self):
        rng = np.random.default_rng(23)
        corpus_embeddings = rng.normal(size=(127, 16)).astype(np.float32)
        query_embeddings = rng.normal(size=(5, 16)).astype(np.float32)
        chunk_ids = [f"c{idx}" for idx in range(len(corpus_embeddings))]
        arm_labels = rng.integers(0, 7, size=len(corpus_embeddings), dtype=np.int32)
        arm_indices = linucb_online_baseline.build_arm_row_indices(arm_labels)

        for query in query_embeddings:
            for selected_arms in ([0], [1, 4], [6, 2, 3]):
                legacy = linucb_online_baseline.retrieve_from_arms(
                    query,
                    corpus_embeddings,
                    chunk_ids,
                    arm_labels,
                    selected_arms,
                    top_k=10,
                )
                cached = linucb_online_baseline.retrieve_from_arm_score_cache(
                    corpus_embeddings @ query,
                    chunk_ids,
                    arm_indices,
                    selected_arms,
                    top_k=10,
                )
                self.assertEqual(cached, legacy)

    def test_policy_scores_match_two_solve_reference(self):
        policy = linucb_online_baseline.GlobalLinUCBPolicy(
            n_arms=2,
            context_dim=2,
            alpha=0.7,
            alpha_decay=0.0,
            alpha_min=0.7,
            seed=5,
            tie_jitter=0.0,
        )
        policy.A[0] = np.asarray([[2.0, 0.3], [0.3, 1.5]], dtype=np.float32)
        policy.A[1] = np.asarray([[1.2, 0.1], [0.1, 2.1]], dtype=np.float32)
        policy.b[0] = np.asarray([0.8, 0.2], dtype=np.float32)
        policy.b[1] = np.asarray([0.1, 0.9], dtype=np.float32)
        context = np.asarray([0.6, 0.4], dtype=np.float32)

        expected = []
        for arm in range(policy.n_arms):
            theta = np.linalg.solve(policy.A[arm], policy.b[arm])
            point_estimate = float(np.dot(theta, context))
            a_inv_context = np.linalg.solve(policy.A[arm], context)
            uncertainty = float(np.sqrt(max(0.0, np.dot(context, a_inv_context))))
            expected.append(point_estimate + policy.effective_alpha * uncertainty)

        np.testing.assert_allclose(policy.scores(context), np.asarray(expected), rtol=1e-6, atol=1e-7)

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
