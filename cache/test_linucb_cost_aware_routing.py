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
            linucb_cost.parse_list("full_multi_route,gated_cost_aware", linucb_cost.ROUTING_MODES, label="routing"),
            ("full_multi_route", "gated_cost_aware"),
        )
        with self.assertRaises(ValueError):
            linucb_cost.parse_list("bad", linucb_cost.ROUTING_MODES, label="routing")

    def test_route_decision_uses_dense_only_as_needed(self):
        primary = linucb_cost.decide_route(
            "gated_cost_aware",
            confidence=0.9,
            semantic_drift=0.1,
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
        )
        self.assertEqual(primary.route, "linucb_primary")
        self.assertEqual(primary.dense_depth, 0)

        fallback = linucb_cost.decide_route(
            "gated_cost_aware",
            confidence=0.9,
            semantic_drift=1.2,
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
                routing_modes=("full_multi_route", "gated_cost_aware"),
                feedback_mode="trust_weighted",
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
                confidence_feedback_floor=1.0,
                high_trust_prob=1.0,
                high_trust=1.0,
                low_trust=0.25,
                high_accuracy=1.0,
                low_accuracy=0.55,
                window_size=1,
                query_split="test",
            )
            linucb_cost.update_summary(out_dir / "linucb_cost_summary.csv", rows)
            linucb_cost.write_markdown_table(out_dir / "linucb_cost_summary.csv", out_dir / "linucb_cost_tables.md")

            self.assertEqual([row["routing_mode"] for row in rows], ["full_multi_route", "gated_cost_aware"])
            self.assertIn("avg_source_candidate_cost_mean", rows[0])
            artifact_slug = rows[0]["artifact_slug"]
            self.assertTrue((out_dir / f"linucb_cost_{artifact_slug}_prequential_metrics.json").exists())
            self.assertTrue((out_dir / f"linucb_cost_{artifact_slug}_prequential_rankings.json").exists())
            self.assertTrue((out_dir / "linucb_cost_summary.csv").exists())
            self.assertTrue((out_dir / "linucb_cost_tables.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
