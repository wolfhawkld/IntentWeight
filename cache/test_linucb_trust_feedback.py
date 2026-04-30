#!/usr/bin/env python3
"""Tests for trust-weighted feedback LinUCB experiments."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_trust_feedback.py"

spec = importlib.util.spec_from_file_location("linucb_trust_feedback", MODULE_PATH)
linucb_trust_feedback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linucb_trust_feedback)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class LinUCBTrustFeedbackTests(unittest.TestCase):
    def test_parse_modes_rejects_unknown_mode(self):
        self.assertEqual(
            linucb_trust_feedback.parse_modes("none,oracle,trust_weighted"),
            ("none", "oracle", "trust_weighted"),
        )
        with self.assertRaises(ValueError):
            linucb_trust_feedback.parse_modes("none,bad")

    def test_build_artifact_slug_includes_run_scope(self):
        slug = linucb_trust_feedback.build_artifact_slug(
            "Banking77",
            {
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "num_queries": 3080,
            },
        )

        self.assertEqual(slug, "banking77_heldout-test_test_corpus-full_q3080")

    def test_feedback_simulation_and_mode_weights(self):
        rng = np.random.default_rng(3)

        oracle = linucb_trust_feedback.simulate_user_feedback(
            1.0,
            rng,
            mode="oracle",
            high_trust_prob=0.5,
            high_trust=1.0,
            low_trust=0.25,
            high_accuracy=0.9,
            low_accuracy=0.55,
        )
        self.assertEqual(oracle.observed_reward, 1.0)
        self.assertEqual(linucb_trust_feedback.update_weight_for_mode("oracle", oracle), 1.0)

        noisy = linucb_trust_feedback.FeedbackObservation(
            true_reward=1.0,
            observed_reward=1.0,
            trust=0.25,
            user_group="low_trust",
            aligned=True,
        )
        self.assertEqual(linucb_trust_feedback.update_weight_for_mode("equal_noisy", noisy), 1.0)
        self.assertEqual(linucb_trust_feedback.update_weight_for_mode("trust_weighted", noisy), 0.25)
        self.assertEqual(linucb_trust_feedback.memory_reward_for_mode("trust_weighted", noisy), 0.25)

    def test_window_mean_uses_head_and_tail(self):
        values = [0.0, 0.0, 1.0, 1.0]

        self.assertEqual(linucb_trust_feedback._window_mean(values, 2, tail=False), 0.0)
        self.assertEqual(linucb_trust_feedback._window_mean(values, 2, tail=True), 1.0)

    def test_prequential_seed_reports_feedback_evolution_metrics(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        corpus_embeddings = linucb_trust_feedback.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ], dtype=np.float32))
        query_embeddings = linucb_trust_feedback.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))

        result = linucb_trust_feedback.run_prequential_seed(
            corpus,
            queries,
            corpus_embeddings,
            query_embeddings,
            seed=7,
            feedback_mode="trust_weighted",
            epochs=2,
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
            dense_depth=2,
            bm25_depth=2,
            cluster_depth=2,
            dense_weight=2.0,
            bm25_weight=0.8,
            cluster_weight=0.8,
            rrf_k=60,
            dense_floor_k=1,
            high_trust_prob=1.0,
            high_trust=1.0,
            low_trust=0.25,
            high_accuracy=1.0,
            low_accuracy=0.55,
            window_size=2,
        )

        metrics = result["metrics"]
        self.assertEqual(metrics["feedback_mode"], "trust_weighted")
        self.assertEqual(metrics["epochs"], 2)
        self.assertEqual(metrics["num_interactions"], 4)
        self.assertIn("epoch_true_reward_gain", metrics)
        self.assertIn("window_selected_cluster_hit_gain", metrics)
        self.assertEqual(len(metrics["epoch_metrics"]), 2)
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
                {"chunk_id": "c_gamma", "text": "gamma document"},
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
                "gamma document": [-1.0, 0.0],
                "alpha query": [1.0, 0.0],
            })

            rows = linucb_trust_feedback.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                feedback_modes=("none", "trust_weighted"),
                top_k=1,
                ks=(1,),
                batch_size=2,
                seeds=(1,),
                epochs=2,
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
                dense_depth=2,
                bm25_depth=2,
                cluster_depth=2,
                dense_weight=2.0,
                bm25_weight=0.8,
                cluster_weight=0.8,
                rrf_k=60,
                dense_floor_k=1,
                high_trust_prob=1.0,
                high_trust=1.0,
                low_trust=0.25,
                high_accuracy=1.0,
                low_accuracy=0.55,
                window_size=1,
                query_split="test",
            )
            linucb_trust_feedback.update_summary(out_dir / "linucb_trust_summary.csv", rows)
            linucb_trust_feedback.write_markdown_table(
                out_dir / "linucb_trust_summary.csv",
                out_dir / "linucb_trust_tables.md",
            )

            self.assertEqual([row["feedback_mode"] for row in rows], ["none", "trust_weighted"])
            artifact_slug = rows[0]["artifact_slug"]
            self.assertTrue((out_dir / f"linucb_trust_{artifact_slug}_prequential_metrics.json").exists())
            self.assertTrue((out_dir / f"linucb_trust_{artifact_slug}_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_trust_summary.csv").exists())
            self.assertTrue((out_dir / "linucb_trust_tables.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
