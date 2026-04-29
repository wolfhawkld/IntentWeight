#!/usr/bin/env python3
"""Tests for soft-routed manifold LinUCB retrieval."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_soft_routing.py"

spec = importlib.util.spec_from_file_location("linucb_soft_routing", MODULE_PATH)
linucb_soft_routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linucb_soft_routing)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class LinUCBSoftRoutingTests(unittest.TestCase):
    def test_weighted_rrf_rewards_cross_source_agreement(self):
        ranking = linucb_soft_routing.weighted_reciprocal_rank_fusion(
            (
                (["dense_a", "shared"], 2.0),
                (["bm25_a", "shared"], 0.5),
            ),
            rrf_k=10,
            top_k=3,
        )

        self.assertEqual(ranking[0], "shared")
        self.assertIn("dense_a", ranking)
        self.assertIn("shared", ranking)

    def test_stable_top_k_prefix_is_depth_independent_for_ties(self):
        scores = np.asarray([1.0, 1.0, 1.0, 0.5, 0.5], dtype=np.float32)

        top_2 = linucb_soft_routing.stable_top_k_indices(scores, 2)
        top_4 = linucb_soft_routing.stable_top_k_indices(scores, 4)

        self.assertEqual(top_2, [0, 1])
        self.assertEqual(top_4[:2], top_2)

    def test_gt_cluster_hit_detects_hard_pruning_miss(self):
        labels_by_chunk = {"c_alpha": 0, "c_beta": 1}

        self.assertTrue(linucb_soft_routing.gt_cluster_hit([0], {"c_alpha"}, labels_by_chunk))
        self.assertFalse(linucb_soft_routing.gt_cluster_hit([0], {"c_beta"}, labels_by_chunk))

    def test_dense_floor_protects_dense_candidates(self):
        ranking = linucb_soft_routing.apply_dense_floor(
            ["bm25_a", "cluster_a", "dense_b"],
            ["dense_a", "dense_b", "dense_c"],
            dense_floor_k=2,
            top_k=3,
        )

        self.assertEqual(ranking, ["dense_a", "dense_b", "bm25_a"])

    def test_prequential_seed_returns_soft_and_pruning_metrics(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        corpus_embeddings = linucb_soft_routing.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ], dtype=np.float32))
        query_embeddings = linucb_soft_routing.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))

        result = linucb_soft_routing.run_prequential_seed(
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
            dense_depth=2,
            bm25_depth=2,
            cluster_depth=2,
            dense_weight=2.0,
            bm25_weight=0.8,
            cluster_weight=0.8,
            rrf_k=60,
            dense_floor_k=1,
        )

        metrics = result["metrics"]
        self.assertEqual(metrics["seed"], 7)
        self.assertEqual(metrics["num_queries"], 2)
        self.assertIn("selected_cluster_hit_rate", metrics)
        self.assertIn("dense_fallback_hit_rate", metrics)
        self.assertIn("soft_rescue_on_cluster_miss_rate", metrics)
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

            metrics = linucb_soft_routing.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                top_k=1,
                ks=(1,),
                batch_size=2,
                seeds=(1,),
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
                query_split="test",
            )
            linucb_soft_routing.update_summary(out_dir / "linucb_soft_summary.csv", [metrics])

            self.assertEqual(metrics["method"], "linucb_soft_manifold")
            self.assertEqual(metrics["protocol"], "prequential")
            self.assertEqual(metrics["query_split"], "test")
            self.assertEqual(metrics["num_seeds"], 1)
            self.assertTrue((out_dir / "linucb_soft_toy_prequential_metrics.json").exists())
            self.assertTrue((out_dir / "linucb_soft_toy_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_soft_summary.csv").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
