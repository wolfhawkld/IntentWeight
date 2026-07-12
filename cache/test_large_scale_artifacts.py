#!/usr/bin/env python3
"""Tests for shared large-scale retrieval artifacts."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "large_scale_artifacts.py"

spec = importlib.util.spec_from_file_location("large_scale_artifacts", MODULE_PATH)
large_scale_artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(large_scale_artifacts)


class LargeScaleArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.corpus = [
            {"chunk_id": "c_alpha", "text": "alpha document"},
            {"chunk_id": "c_beta", "text": "beta document"},
            {"chunk_id": "c_gamma", "text": "gamma document"},
        ]
        self.queries = [
            {"query_id": "q_alpha", "text": "alpha query", "ground_truth_chunk_ids": ["c_alpha"]},
            {"query_id": "q_beta", "text": "beta query", "ground_truth_chunk_ids": ["c_beta"]},
        ]
        self.corpus_embeddings = np.asarray(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [-1.0, 0.0],
            ],
            dtype=np.float32,
        )
        self.query_embeddings = np.asarray(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
            dtype=np.float32,
        )

    def test_dense_rankings_are_cached_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            first, first_info = large_scale_artifacts.load_or_compute_dense_rankings(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                depth=2,
                cache_dir=cache_dir,
                batch_size=1,
            )
            second, second_info = large_scale_artifacts.load_or_compute_dense_rankings(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                depth=2,
                cache_dir=cache_dir,
                batch_size=1,
            )

            self.assertFalse(first_info["cache_hit"])
            self.assertTrue(second_info["cache_hit"])
            self.assertEqual(first, second)
            self.assertEqual(first["q_alpha"][0], "c_alpha")
            self.assertTrue(Path(first_info["artifact_path"]).exists())

    def test_bm25_rankings_are_cached_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            first, first_info = large_scale_artifacts.load_or_compute_bm25_rankings(
                self.corpus,
                self.queries,
                dataset="toy",
                depth=2,
                cache_dir=cache_dir,
            )
            second, second_info = large_scale_artifacts.load_or_compute_bm25_rankings(
                self.corpus,
                self.queries,
                dataset="toy",
                depth=2,
                cache_dir=cache_dir,
            )

            self.assertFalse(first_info["cache_hit"])
            self.assertTrue(second_info["cache_hit"])
            self.assertEqual(first, second)
            self.assertEqual(first["q_beta"][0], "c_beta")

    def test_context_clusters_are_cached_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            first, first_info = large_scale_artifacts.load_or_compute_context_clusters(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                context_dim=2,
                n_clusters=2,
                seed=13,
                cache_dir=cache_dir,
            )
            second, second_info = large_scale_artifacts.load_or_compute_context_clusters(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                context_dim=2,
                n_clusters=2,
                seed=13,
                cache_dir=cache_dir,
            )

            self.assertFalse(first_info["cache_hit"])
            self.assertTrue(second_info["cache_hit"])
            self.assertEqual(first["corpus_context"].shape, (3, 2))
            self.assertEqual(first["query_context"].shape, (2, 2))
            np.testing.assert_allclose(first["centroids"], second["centroids"])
            np.testing.assert_array_equal(first["arm_labels"], second["arm_labels"])

    def test_query_corpus_scores_are_cached_and_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            first, first_info = large_scale_artifacts.load_or_compute_query_corpus_scores(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                cache_dir=cache_dir,
                progress_every=10,
            )
            second, second_info = large_scale_artifacts.load_or_compute_query_corpus_scores(
                self.corpus,
                self.queries,
                self.corpus_embeddings,
                self.query_embeddings,
                dataset="toy",
                model_name="fake-model",
                cache_dir=cache_dir,
                progress_every=10,
            )

            expected = np.vstack([
                self.corpus_embeddings @ self.query_embeddings[0],
                self.corpus_embeddings @ self.query_embeddings[1],
            ])
            self.assertFalse(first_info["cache_hit"])
            self.assertTrue(second_info["cache_hit"])
            self.assertEqual(first.shape, expected.shape)
            np.testing.assert_array_equal(first, expected)
            np.testing.assert_array_equal(second, expected)
            self.assertTrue(Path(first_info["artifact_path"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
