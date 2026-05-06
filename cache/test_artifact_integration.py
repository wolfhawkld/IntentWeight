#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for artifact cache integration in dense_baseline, hybrid_baseline, manifold_diagnostics."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "paper" / "experiments" / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dense_baseline = _load_module("dense_baseline", SCRIPTS_DIR / "dense_baseline.py")
hybrid_baseline = _load_module("hybrid_baseline", SCRIPTS_DIR / "hybrid_baseline.py")
manifold_diagnostics = _load_module("manifold_diagnostics", SCRIPTS_DIR / "manifold_diagnostics.py")
large_scale_artifacts = _load_module("large_scale_artifacts", SCRIPTS_DIR / "large_scale_artifacts.py")


def _make_toy_dataset(tmp_dir: Path):
    """Create minimal processed dataset files for testing."""
    corpus = [
        {"chunk_id": "c1", "text": "alpha beta gamma document about science"},
        {"chunk_id": "c2", "text": "delta epsilon zeta document about history"},
        {"chunk_id": "c3", "text": "eta theta iota document about math"},
        {"chunk_id": "c4", "text": "kappa lambda mu document about physics"},
        {"chunk_id": "c5", "text": "nu xi omicron document about chemistry"},
    ]
    queries = [
        {"query_id": "q1", "text": "science alpha", "ground_truth_chunk_ids": ["c1"], "split": "test"},
        {"query_id": "q2", "text": "history delta", "ground_truth_chunk_ids": ["c2"], "split": "test"},
        {"query_id": "q3", "text": "math theta", "ground_truth_chunk_ids": ["c3"], "split": "test"},
    ]
    data_dir = tmp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
    (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
    return data_dir, corpus, queries


class _FakeEncoder:
    """Deterministic encoder that returns fixed embeddings based on text hash."""

    def encode(self, texts, batch_size=64, normalize_embeddings=False, **kwargs):
        embeddings = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 1000
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(32).astype(np.float32)
            embeddings.append(vec / (np.linalg.norm(vec) + 1e-9))
        return np.array(embeddings, dtype=np.float32)


class DenseBaselineArtifactIntegrationTest(unittest.TestCase):
    def test_artifact_cache_produces_same_results_and_reports_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir, _, _ = _make_toy_dataset(tmp_path)
            output_dir = tmp_path / "results"
            output_dir.mkdir()
            artifact_dir = tmp_path / "artifacts"
            embedding_dir = tmp_path / "embeddings"
            encoder = _FakeEncoder()

            # First run: artifact miss
            m1 = dense_baseline.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", top_k=3, ks=(1, 3), batch_size=8,
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )
            # Second run: artifact hit
            m2 = dense_baseline.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", top_k=3, ks=(1, 3), batch_size=8,
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )

            self.assertTrue(m1["artifact_cache_enabled"])
            self.assertFalse(m1["dense_ranking_cache_hit"])
            self.assertTrue(m2["dense_ranking_cache_hit"])
            # Metrics must be identical
            for key in m1:
                if "@" in key:
                    self.assertAlmostEqual(m1[key], m2[key], places=6, msg=f"Mismatch on {key}")

    def test_no_artifact_cache_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir, _, _ = _make_toy_dataset(tmp_path)
            output_dir = tmp_path / "results"
            output_dir.mkdir()
            encoder = _FakeEncoder()

            m = dense_baseline.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", top_k=3, ks=(1, 3), batch_size=8,
                query_split="test",
                use_embedding_cache=False,
                use_artifact_cache=False,
            )
            self.assertFalse(m["artifact_cache_enabled"])
            self.assertIn("recall@1", m)


class HybridBaselineArtifactIntegrationTest(unittest.TestCase):
    def test_artifact_cache_produces_same_results_and_reports_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir, _, _ = _make_toy_dataset(tmp_path)
            output_dir = tmp_path / "results"
            output_dir.mkdir()
            artifact_dir = tmp_path / "artifacts"
            embedding_dir = tmp_path / "embeddings"
            encoder = _FakeEncoder()

            m1 = hybrid_baseline.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", top_k=3, ks=(1, 3), batch_size=8,
                rrf_k=60, fusion_depth=5,
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )
            m2 = hybrid_baseline.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", top_k=3, ks=(1, 3), batch_size=8,
                rrf_k=60, fusion_depth=5,
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )

            self.assertTrue(m1["artifact_cache_enabled"])
            self.assertFalse(m1["dense_ranking_cache_hit"])
            self.assertFalse(m1["bm25_ranking_cache_hit"])
            self.assertTrue(m2["dense_ranking_cache_hit"])
            self.assertTrue(m2["bm25_ranking_cache_hit"])
            for key in m1:
                if "@" in key:
                    self.assertAlmostEqual(m1[key], m2[key], places=6, msg=f"Mismatch on {key}")


class ManifoldDiagnosticsArtifactIntegrationTest(unittest.TestCase):
    def test_artifact_cache_produces_same_results_and_reports_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir, _, _ = _make_toy_dataset(tmp_path)
            output_dir = tmp_path / "results"
            output_dir.mkdir()
            artifact_dir = tmp_path / "artifacts"
            embedding_dir = tmp_path / "embeddings"
            encoder = _FakeEncoder()

            m1 = manifold_diagnostics.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", batch_size=8,
                n_clusters=2, context_dim=8, seed=13,
                sample_size=3, neighbor_k=2,
                cluster_hit_ks=(1, 3), recall_ks=(1, 3),
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )
            m2 = manifold_diagnostics.run_dataset(
                "toy", data_dir, output_dir, encoder,
                model_name="fake-model", batch_size=8,
                n_clusters=2, context_dim=8, seed=13,
                sample_size=3, neighbor_k=2,
                cluster_hit_ks=(1, 3), recall_ks=(1, 3),
                query_split="test",
                embedding_cache_dir=embedding_dir,
                use_embedding_cache=True,
                force_embedding_cache=False,
                artifact_cache_dir=artifact_dir,
                use_artifact_cache=True,
                force_artifact_cache=False,
            )

            self.assertTrue(m1["artifact_cache_enabled"])
            self.assertFalse(m1["context_cluster_cache_hit"])
            self.assertTrue(m2["context_cluster_cache_hit"])
            # Key diagnostics metrics must match
            for key in ("nearest_cluster_hit@1", "nearest_cluster_hit@3", "context_gt_recall@1", "context_gt_recall@3"):
                if key in m1 and key in m2:
                    self.assertAlmostEqual(m1[key], m2[key], places=6, msg=f"Mismatch on {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
