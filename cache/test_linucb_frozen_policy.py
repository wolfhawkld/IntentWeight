#!/usr/bin/env python3
"""Regression tests for frozen-policy unseen-query evaluation."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "linucb_cost_aware_routing.py"
TASK70_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "task70_frozen_policy_generalization.py"

spec = importlib.util.spec_from_file_location("linucb_cost_aware_routing", MODULE_PATH)
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)
task70_spec = importlib.util.spec_from_file_location("task70_frozen_policy_generalization", TASK70_PATH)
task70 = importlib.util.module_from_spec(task70_spec)
task70_spec.loader.exec_module(task70)


def run_seed(corpus, queries, corpus_embeddings, query_embeddings, **overrides):
    params = {
        "seed": 13,
        "routing_mode": "full_multi_route",
        "feedback_mode": "trust_weighted",
        "reward_attribution": "final_fused",
        "confidence_mode": "value",
        "epochs": 1,
        "top_k": 1,
        "ks": (1,),
        "n_clusters": 2,
        "context_dim": 2,
        "candidate_arms": 2,
        "alpha": 1.0,
        "alpha_decay": 0.01,
        "alpha_min": 0.3,
        "arm_neighbor_k": 1,
        "arm_decay_sigma": 0.75,
        "propagation_strength": 0.25,
        "feedback_k": 2,
        "feedback_tau": 0.75,
        "feedback_weight": 0.35,
        "dense_depth": 2,
        "bm25_depth": 2,
        "cluster_depth": 2,
        "dense_weight": 2.0,
        "bm25_weight": 0.8,
        "cluster_weight": 0.8,
        "rrf_k": 60,
        "dense_floor_k": 1,
        "dense_lite_depth": 1,
        "bm25_lite_depth": 1,
        "dense_lite_weight": 0.8,
        "bm25_lite_weight": 0.5,
        "cluster_primary_weight": 2.0,
        "dense_lite_floor_k": 1,
        "high_confidence_threshold": 0.65,
        "mid_confidence_threshold": 0.35,
        "drift_threshold": 1.0,
        "reward_drop_threshold": 0.0,
        "confidence_feedback_floor": 1.0,
        "final_context_policy": "fixed_topk",
        "final_context_high_k": 1,
        "final_context_mid_k": 1,
        "high_trust_prob": 1.0,
        "high_trust": 1.0,
        "low_trust": 0.25,
        "high_accuracy": 1.0,
        "low_accuracy": 0.55,
        "window_size": 1,
        "epsilon_greedy_rate": 0.1,
        "cluster_retrieval_engine": "on_demand",
    }
    params.update(overrides)
    return routing.run_prequential_seed(corpus, queries, corpus_embeddings, query_embeddings, **params)


class FrozenPolicyTests(unittest.TestCase):
    def test_fold_checkpoint_round_trip_requires_complete_query_coverage(self):
        signature = {"seeds": [13]}
        rankings = {
            method: {"13": {"q1": ["c1"]}}
            for method in task70.METHODS
        }
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "fold0.json"
            task70.write_json(
                checkpoint,
                {
                    "signature": signature,
                    "fold": 0,
                    "fold_rows": [{"fold": 0, "method": "dense"}],
                    "rankings": rankings,
                },
            )
            rows, restored = task70.load_fold_checkpoint(
                checkpoint,
                signature=signature,
                expected_query_ids={"q1"},
            )
        self.assertEqual(rows, [{"fold": 0, "method": "dense"}])
        self.assertEqual(restored["learned_full_frozen"]["13"]["q1"], ["c1"])

    def test_score_row_subset_preserves_selected_rows_without_matrix_copy(self):
        matrix = np.arange(20, dtype=np.float32).reshape(4, 5)
        subset = task70.ScoreRowSubset(matrix, [3, 1])
        self.assertEqual(subset.shape, (2, 5))
        np.testing.assert_array_equal(subset[0], matrix[3])
        np.testing.assert_array_equal(subset[1], matrix[1])

    def test_paired_comparison_tracks_query_level_wins_losses_and_intervals(self):
        queries = [
            {"query_id": "q1", "ground_truth_chunk_ids": ["c1"]},
            {"query_id": "q2", "ground_truth_chunk_ids": ["c2"]},
            {"query_id": "q3", "ground_truth_chunk_ids": ["c3"]},
        ]
        comparison = task70.paired_comparison(
            queries=queries,
            method="learned_full_frozen",
            baseline="static_nearest_full",
            seed=13,
            method_rankings={"q1": ["c1"], "q2": ["miss"], "q3": ["c3"]},
            baseline_rankings={"q1": ["miss"], "q2": ["c2"], "q3": ["c3"]},
            n_bootstrap=200,
            bootstrap_seed=17,
        )
        self.assertEqual(comparison["queries"], 3)
        self.assertEqual(comparison["method_only_hits"], 1)
        self.assertEqual(comparison["baseline_only_hits"], 1)
        self.assertEqual(comparison["hit_ties"], 1)
        self.assertAlmostEqual(comparison["hit_delta_mean"], 0.0)
        self.assertLessEqual(comparison["hit_delta_ci_low"], comparison["hit_delta_mean"])
        self.assertGreaterEqual(comparison["hit_delta_ci_high"], comparison["hit_delta_mean"])

    def test_unseen_query_evaluation_does_not_update_history_state(self):
        corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        history = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        test = [
            {"query_id": "q_gamma", "text": "gamma query", "ground_truth_chunk_ids": ["c_gamma"]},
        ]
        corpus_embeddings = routing.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ], dtype=np.float32))
        history_embeddings = routing.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))
        test_embeddings = routing.global_linucb.l2_normalize(np.asarray([
            [-1.0, 0.0],
        ], dtype=np.float32))

        trained = run_seed(
            corpus,
            history,
            corpus_embeddings,
            history_embeddings,
            epochs=2,
            return_state=True,
        )
        state = trained["runtime_state"]
        policy = state["policy"]
        matrices_before = [matrix.copy() for matrix in policy.A]
        vectors_before = [vector.copy() for vector in policy.b]
        pulls_before = list(policy.pull_counts)
        feedback_count_before = len(state["feedback_contexts"])
        reward_sums_before = state["route_reward_sums"].copy()
        pull_sums_before = state["route_pull_counts"].copy()
        observed_count_before = len(state["observed_rewards"])

        evaluated = run_seed(
            corpus,
            test,
            corpus_embeddings,
            test_embeddings,
            initial_state=state,
            freeze_updates=True,
        )

        self.assertEqual(evaluated["metrics"]["num_interactions"], 1)
        self.assertIn("q_gamma", evaluated["rankings"])
        for before, after in zip(matrices_before, policy.A):
            np.testing.assert_array_equal(before, after)
        for before, after in zip(vectors_before, policy.b):
            np.testing.assert_array_equal(before, after)
        self.assertEqual(pulls_before, policy.pull_counts)
        self.assertEqual(feedback_count_before, len(state["feedback_contexts"]))
        np.testing.assert_array_equal(reward_sums_before, state["route_reward_sums"])
        np.testing.assert_array_equal(pull_sums_before, state["route_pull_counts"])
        self.assertEqual(observed_count_before, len(state["observed_rewards"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
