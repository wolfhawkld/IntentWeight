#!/usr/bin/env python3
"""Tests for Task16 confidence-gated cost-aware routing."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_cost_aware_routing.py"

spec = importlib.util.spec_from_file_location("linucb_cost_aware_routing", MODULE_PATH)
linucb_cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linucb_cost)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class LinUCBCostAwareRoutingTests(unittest.TestCase):
    def test_parse_list_rejects_unknown_mode(self):
        self.assertEqual(
            linucb_cost.parse_list(
                "full_multi_route,gated_cost_aware,static_nearest_ensemble,static_nearest_gated",
                linucb_cost.ROUTING_MODES,
                label="routing",
            ),
            ("full_multi_route", "gated_cost_aware", "static_nearest_ensemble", "static_nearest_gated"),
        )
        with self.assertRaises(ValueError):
            linucb_cost.parse_list("bad", linucb_cost.ROUTING_MODES, label="routing")

    def test_nearest_centroid_arms_is_stable(self):
        centroids = np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [-1.0, 0.0],
        ], dtype=np.float32)
        context = np.asarray([1.0, 0.0], dtype=np.float32)

        self.assertEqual(linucb_cost.nearest_centroid_arms(context, centroids, candidate_arms=2), [0, 2])
        self.assertEqual(linucb_cost.centroid_similarity_confidence(context, centroids, [0, 2]), 1.0)

    def test_epsilon_greedy_arms_prefers_empirical_reward_after_cold_start(self):
        rng = np.random.default_rng(7)
        rewards = np.asarray([0.1, 2.0, 0.3], dtype=np.float64)
        pulls = np.asarray([1.0, 2.0, 1.0], dtype=np.float64)

        self.assertEqual(
            linucb_cost.epsilon_greedy_arms(rng, rewards, pulls, candidate_arms=2, epsilon=0.0),
            [1, 2],
        )

    def test_route_decision_uses_dense_only_as_needed(self):
        primary = linucb_cost.decide_route(
            "gated_cost_aware",
            confidence=0.9,
            semantic_drift=0.1,
            recent_reward_delta=0.0,
            dense_depth=100,
            bm25_depth=100,
            cluster_depth=100,
            dense_weight=2.0,
            bm25_weight=0.8,
            cluster_weight=0.8,
            dense_floor_k=5,
            dense_lite_depth=20,
            bm25_lite_depth=20,
            dense_lite_weight=0.8,
            bm25_lite_weight=0.5,
            cluster_primary_weight=2.0,
            dense_lite_floor_k=2,
            high_confidence_threshold=0.65,
            mid_confidence_threshold=0.35,
            drift_threshold=1.0,
            reward_drop_threshold=0.0,
        )
        self.assertEqual(primary.route, "linucb_primary")
        self.assertEqual(primary.dense_depth, 0)

        fallback = linucb_cost.decide_route(
            "gated_cost_aware",
            confidence=0.9,
            semantic_drift=1.2,
            recent_reward_delta=0.0,
            dense_depth=100,
            bm25_depth=100,
            cluster_depth=100,
            dense_weight=2.0,
            bm25_weight=0.8,
            cluster_weight=0.8,
            dense_floor_k=5,
            dense_lite_depth=20,
            bm25_lite_depth=20,
            dense_lite_weight=0.8,
            bm25_lite_weight=0.5,
            cluster_primary_weight=2.0,
            dense_lite_floor_k=2,
            high_confidence_threshold=0.65,
            mid_confidence_threshold=0.35,
            drift_threshold=1.0,
            reward_drop_threshold=0.0,
        )
        self.assertEqual(fallback.route, "full_dense_fallback")
        self.assertEqual(fallback.dense_depth, 100)

    def test_policy_confidence_requires_maturity(self):
        policy = linucb_cost.global_linucb.GlobalLinUCBPolicy(n_arms=2, context_dim=2, seed=3)
        context = np.asarray([1.0, 0.0], dtype=np.float32)
        confidence, _, _ = linucb_cost.policy_confidence(
            policy,
            context,
            [0],
            np.zeros(2, dtype=np.float64),
            confidence_feedback_floor=2.0,
        )
        self.assertEqual(confidence, 0.0)

        policy.update(0, context, 1.0)
        policy.update(0, context, 1.0)
        confidence, _, _ = linucb_cost.policy_confidence(
            policy,
            context,
            [0],
            np.zeros(2, dtype=np.float64),
            confidence_feedback_floor=2.0,
        )
        self.assertGreater(confidence, 0.0)

    def test_route_quality_confidence_uses_route_history_and_maturity(self):
        reward_sums = np.asarray([2.0, 0.0, 1.0], dtype=np.float64)
        pulls = np.asarray([2.0, 0.0, 2.0], dtype=np.float64)

        cold_confidence = linucb_cost.route_quality_confidence(
            [1],
            reward_sums,
            pulls,
            confidence_feedback_floor=2.0,
        )
        warm_confidence = linucb_cost.route_quality_confidence(
            [0, 2],
            reward_sums,
            pulls,
            confidence_feedback_floor=2.0,
        )

        self.assertEqual(cold_confidence, 0.0)
        self.assertAlmostEqual(warm_confidence, 0.75)

    def test_final_context_policy_compacts_only_confident_lite_routes(self):
        compact = linucb_cost.decide_final_context(
            "confidence_topk",
            confidence=0.9,
            semantic_drift=0.1,
            route="linucb_primary",
            top_k=10,
            final_context_high_k=4,
            final_context_mid_k=7,
            high_confidence_threshold=0.8,
            mid_confidence_threshold=0.5,
            drift_threshold=1.0,
        )
        fallback = linucb_cost.decide_final_context(
            "confidence_topk",
            confidence=0.9,
            semantic_drift=0.1,
            route="full_dense_fallback",
            top_k=10,
            final_context_high_k=4,
            final_context_mid_k=7,
            high_confidence_threshold=0.8,
            mid_confidence_threshold=0.5,
            drift_threshold=1.0,
        )

        self.assertEqual(compact.final_k, 4)
        self.assertEqual(compact.reason, "high_confidence_compact")
        self.assertEqual(fallback.final_k, 10)

    def test_run_dataset_writes_cost_artifacts(self):
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

            rows = linucb_cost.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                routing_modes=(
                    "full_multi_route",
                    "gated_cost_aware",
                    "static_nearest_ensemble",
                    "static_nearest_gated",
                    "uniform_random_ensemble",
                    "epsilon_greedy_ensemble",
                ),
                feedback_mode="trust_weighted",
                reward_attribution="cluster_only",
                confidence_mode="route_quality",
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
                dense_lite_depth=1,
                bm25_lite_depth=1,
                dense_lite_weight=0.8,
                bm25_lite_weight=0.5,
                cluster_primary_weight=2.0,
                dense_lite_floor_k=1,
                high_confidence_threshold=0.65,
                mid_confidence_threshold=0.35,
                drift_threshold=1.0,
                reward_drop_threshold=0.0,
                confidence_feedback_floor=1.0,
                high_trust_prob=1.0,
                high_trust=1.0,
                low_trust=0.25,
                high_accuracy=1.0,
                low_accuracy=0.55,
                window_size=1,
                query_split="test",
                artifact_cache_dir=tmpdir / "artifacts",
                use_artifact_cache=True,
            )
            linucb_cost.update_summary(out_dir / "linucb_cost_summary.csv", rows)
            linucb_cost.write_markdown_table(out_dir / "linucb_cost_summary.csv", out_dir / "linucb_cost_tables.md")

            self.assertEqual(
                [row["routing_mode"] for row in rows],
                [
                    "full_multi_route",
                    "gated_cost_aware",
                    "static_nearest_ensemble",
                    "static_nearest_gated",
                    "uniform_random_ensemble",
                    "epsilon_greedy_ensemble",
                ],
            )
            self.assertIn("avg_source_candidate_cost_mean", rows[0])
            self.assertEqual(rows[0]["reward_attribution"], "cluster_only")
            self.assertEqual(rows[0]["confidence_mode"], "route_quality")
            self.assertIn("last_epoch_final_true_reward_mean", rows[0])
            self.assertIn("last_epoch_route_true_reward_mean", rows[0])
            self.assertEqual(rows[0]["final_context_policy"], "fixed_topk")
            self.assertIn("avg_final_context_k_mean", rows[0])
            static_row = rows[2]
            self.assertEqual(static_row["total_feedback_updates_mean"], 0.0)
            self.assertEqual(static_row["static_nearest_ensemble_rate_mean"], 1.0)
            static_gated_row = rows[3]
            self.assertEqual(static_gated_row["total_feedback_updates_mean"], 0.0)
            uniform_row = rows[4]
            epsilon_row = rows[5]
            self.assertEqual(uniform_row["simple_bandit_updates_mean"], 0.0)
            self.assertGreater(epsilon_row["simple_bandit_updates_mean"], 0.0)
            self.assertTrue(rows[0]["artifact_cache_enabled"])
            self.assertFalse(rows[0]["dense_ranking_cache_hit"])
            self.assertFalse(rows[0]["bm25_ranking_cache_hit"])
            self.assertEqual(rows[0]["context_cluster_cache_hits"], [False])
            artifact_slug = rows[0]["artifact_slug"]
            self.assertTrue((out_dir / f"linucb_cost_{artifact_slug}_prequential_metrics.json").exists())
            self.assertTrue((out_dir / f"linucb_cost_{artifact_slug}_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_cost_summary.csv").exists())
            self.assertTrue((out_dir / "linucb_cost_tables.md").exists())

    def test_run_dataset_allows_bm25_disabled(self):
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

            rows = linucb_cost.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                routing_modes=("gated_cost_aware",),
                feedback_mode="trust_weighted",
                reward_attribution="cluster_only",
                confidence_mode="value",
                top_k=1,
                ks=(1,),
                batch_size=2,
                seeds=(1,),
                epochs=1,
                n_clusters=2,
                context_dim=2,
                candidate_arms=1,
                alpha=1.0,
                alpha_decay=0.01,
                alpha_min=0.3,
                arm_neighbor_k=2,
                arm_decay_sigma=0.75,
                propagation_strength=0.25,
                feedback_k=2,
                feedback_tau=0.75,
                feedback_weight=0.35,
                dense_depth=1,
                bm25_depth=0,
                cluster_depth=1,
                dense_weight=1.0,
                bm25_weight=0.0,
                cluster_weight=1.0,
                rrf_k=60,
                dense_floor_k=0,
                dense_lite_depth=0,
                bm25_lite_depth=0,
                dense_lite_weight=0.0,
                bm25_lite_weight=0.0,
                cluster_primary_weight=1.0,
                dense_lite_floor_k=0,
                high_confidence_threshold=0.65,
                mid_confidence_threshold=0.35,
                drift_threshold=1.0,
                reward_drop_threshold=0.0,
                confidence_feedback_floor=1.0,
                high_trust_prob=1.0,
                high_trust=1.0,
                low_trust=0.25,
                high_accuracy=1.0,
                low_accuracy=0.55,
                window_size=1,
                query_split="test",
                artifact_cache_dir=tmpdir / "artifacts",
                use_artifact_cache=True,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["bm25_depth"], 0)
            self.assertEqual(rows[0]["bm25_lite_depth"], 0)
            self.assertEqual(rows[0]["avg_bm25_candidates_mean"], 0.0)
            self.assertTrue(rows[0]["artifact_cache_enabled"])
            self.assertFalse(rows[0]["bm25_ranking_cache_hit"])

    def test_run_dataset_can_load_corpus_embeddings_from_scale_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            store_dir = tmpdir / "scale_store"
            data_dir.mkdir()
            store_dir.mkdir()
            corpus = [
                {
                    "chunk_id": "toy_400k_c0",
                    "text": "alpha document",
                    "metadata": {"original_corpus_id": "0"},
                },
                {
                    "chunk_id": "toy_400k_c1",
                    "text": "beta document",
                    "metadata": {"original_corpus_id": "1"},
                },
                {
                    "chunk_id": "toy_400k_c2",
                    "text": "gamma document",
                    "metadata": {"original_corpus_id": "2"},
                },
            ]
            queries = [
                {
                    "query_id": "q_alpha",
                    "text": "alpha query",
                    "ground_truth_chunk_ids": ["toy_400k_c0"],
                    "split": "test",
                },
            ]
            (data_dir / "toy_400k_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_400k_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            np.save(
                store_dir / "canonical_corpus_embeddings.npy",
                np.asarray([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32),
            )
            (store_dir / "canonical_corpus_ids.json").write_text(
                json.dumps({
                    "canonical_ids": ["toy_orig_0", "toy_orig_1", "toy_orig_2"],
                    "text_sha256": ["unused", "unused", "unused"],
                    "source_datasets": [["toy_400k"], ["toy_400k"], ["toy_400k"]],
                }),
                encoding="utf-8",
            )
            encoder = FakeEncoder({"alpha query": [1.0, 0.0]})

            rows = linucb_cost.run_dataset(
                "toy_400k",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                routing_modes=("full_multi_route",),
                feedback_mode="trust_weighted",
                reward_attribution="final_fused",
                confidence_mode="value",
                top_k=1,
                ks=(1,),
                batch_size=2,
                seeds=(1,),
                epochs=1,
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
                dense_lite_depth=1,
                bm25_lite_depth=1,
                dense_lite_weight=0.8,
                bm25_lite_weight=0.5,
                cluster_primary_weight=2.0,
                dense_lite_floor_k=1,
                high_confidence_threshold=0.65,
                mid_confidence_threshold=0.35,
                drift_threshold=1.0,
                reward_drop_threshold=0.0,
                confidence_feedback_floor=1.0,
                high_trust_prob=1.0,
                high_trust=1.0,
                low_trust=0.25,
                high_accuracy=1.0,
                low_accuracy=0.55,
                window_size=1,
                query_split="test",
                artifact_cache_dir=tmpdir / "artifacts",
                use_artifact_cache=True,
                use_scale_store=True,
                scale_store_dir=store_dir,
                scale_store_canonical_name="toy",
            )

            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["scale_store_enabled"])
            self.assertEqual(rows[0]["scale_store_selected_rows"], 3)
            self.assertTrue(rows[0]["corpus_embedding_cache_hit"])
            self.assertTrue((out_dir / f"linucb_cost_{rows[0]['artifact_slug']}_prequential_metrics.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
