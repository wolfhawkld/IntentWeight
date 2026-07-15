#!/usr/bin/env python3
"""Tests for manifold diagnostics."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "manifold_diagnostics.py"

spec = importlib.util.spec_from_file_location("manifold_diagnostics", MODULE_PATH)
manifold_diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifold_diagnostics)


class FakeEncoder:
    def __init__(self, vectors):
        self.vectors = {text: np.asarray(vector, dtype=np.float32) for text, vector in vectors.items()}

    def encode(self, texts, **kwargs):
        return np.vstack([self.vectors[text] for text in texts]).astype(np.float32)


class ManifoldDiagnosticsTests(unittest.TestCase):
    def test_pca_spectrum_reports_low_dimensional_concentration(self):
        embeddings = np.asarray([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [-1.0, 0.0, 0.0],
            [-0.9, -0.1, 0.0],
        ], dtype=np.float32)

        metrics = manifold_diagnostics.pca_spectrum_metrics(embeddings, dims=(1, 2))

        self.assertGreater(metrics["pca_var@1"], 0.9)
        self.assertLessEqual(metrics["pca_dim_for_90pct"], 1)
        self.assertGreater(metrics["pca_participation_ratio_dim"], 0)

    def test_label_alignment_and_neighborhood_purity(self):
        labels = np.asarray([0, 0, 1, 1], dtype=np.int32)
        corpus_labels = ["a", "a", "b", "b"]
        vectors = manifold_diagnostics.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.9, 0.1],
            [0.0, 1.0],
            [0.1, 0.9],
        ], dtype=np.float32))

        alignment = manifold_diagnostics.label_alignment_metrics(labels, corpus_labels)
        local = manifold_diagnostics.local_label_purity(
            vectors,
            corpus_labels,
            neighbor_k=1,
            sample_size=4,
            seed=1,
        )

        self.assertEqual(alignment["cluster_label_purity"], 1.0)
        self.assertAlmostEqual(local["local_label_purity"], 1.0)

    def test_lotte_does_not_infer_source_as_label(self):
        record = {
            "chunk_id": "c1",
            "text": "sample",
            "metadata": {"source": "lotte", "domain": "technology"},
        }

        self.assertIsNone(manifold_diagnostics.infer_label(record, "lotte_technology_search_100k"))

    def test_query_gt_manifold_metrics_reports_nearest_cluster_hits(self):
        corpus = [
            {"chunk_id": "c_a", "text": "alpha", "metadata": {"record_id": "a"}},
            {"chunk_id": "c_b", "text": "beta", "metadata": {"record_id": "b"}},
        ]
        queries = [
            {"query_id": "q_a", "text": "alpha query", "ground_truth_chunk_ids": ["c_a"]},
        ]
        corpus_embeddings = manifold_diagnostics.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
            [0.0, 1.0],
        ], dtype=np.float32))
        query_embeddings = manifold_diagnostics.global_linucb.l2_normalize(np.asarray([
            [1.0, 0.0],
        ], dtype=np.float32))
        labels = np.asarray([0, 1], dtype=np.int32)

        metrics = manifold_diagnostics.query_gt_manifold_metrics(
            queries,
            query_embeddings,
            corpus_embeddings,
            query_embeddings,
            corpus_embeddings,
            labels,
            chunk_ids=[item["chunk_id"] for item in corpus],
            cluster_hit_ks=(1, 2),
            recall_ks=(1,),
        )

        self.assertEqual(metrics["num_gt_eval_queries"], 1)
        self.assertEqual(metrics["nearest_cluster_hit@1"], 1.0)
        self.assertEqual(metrics["context_gt_recall@1"], 1.0)

    def test_run_dataset_writes_metrics_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            data_dir.mkdir()
            corpus = [
                {"chunk_id": "c_alpha", "text": "alpha document", "metadata": {"record_id": "alpha"}},
                {"chunk_id": "c_beta", "text": "beta document", "metadata": {"record_id": "beta"}},
                {"chunk_id": "c_gamma", "text": "gamma document", "metadata": {"record_id": "gamma"}},
            ]
            queries = [
                {
                    "query_id": "q_alpha",
                    "text": "alpha query",
                    "ground_truth_chunk_ids": ["c_alpha"],
                    "split": "test",
                }
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            encoder = FakeEncoder({
                "alpha document": [1.0, 0.0],
                "beta document": [0.0, 1.0],
                "gamma document": [-1.0, 0.0],
                "alpha query": [1.0, 0.0],
            })

            metrics = manifold_diagnostics.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                batch_size=2,
                n_clusters=2,
                context_dim=2,
                seed=1,
                sample_size=3,
                neighbor_k=1,
                cluster_hit_ks=(1, 2),
                recall_ks=(1,),
                query_split="test",
            )
            manifold_diagnostics.update_summary(out_dir / "manifold_diagnostics_summary.csv", [metrics])

            self.assertEqual(metrics["method"], "manifold_diagnostics")
            self.assertEqual(metrics["query_split"], "test")
            self.assertTrue((out_dir / "manifold_diagnostics_toy.json").exists())
            self.assertTrue((out_dir / "manifold_diagnostics_summary.csv").exists())

    def test_run_dataset_can_reuse_embedding_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            out_dir = tmpdir / "results"
            cache_dir = tmpdir / "embeddings"
            data_dir.mkdir()
            corpus = [
                {"chunk_id": "c_alpha", "text": "alpha document", "metadata": {"record_id": "alpha"}},
                {"chunk_id": "c_beta", "text": "beta document", "metadata": {"record_id": "beta"}},
                {"chunk_id": "c_gamma", "text": "gamma document", "metadata": {"record_id": "gamma"}},
            ]
            queries = [
                {
                    "query_id": "q_alpha",
                    "text": "alpha query",
                    "ground_truth_chunk_ids": ["c_alpha"],
                    "split": "test",
                }
            ]
            (data_dir / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            encoder = FakeEncoder({
                "alpha document": [1.0, 0.0],
                "beta document": [0.0, 1.0],
                "gamma document": [-1.0, 0.0],
                "alpha query": [1.0, 0.0],
            })

            first = manifold_diagnostics.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                batch_size=2,
                n_clusters=2,
                context_dim=2,
                seed=1,
                sample_size=3,
                neighbor_k=1,
                cluster_hit_ks=(1, 2),
                recall_ks=(1,),
                query_split="test",
                embedding_cache_dir=cache_dir,
                use_embedding_cache=True,
            )
            second = manifold_diagnostics.run_dataset(
                "toy",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                batch_size=2,
                n_clusters=2,
                context_dim=2,
                seed=1,
                sample_size=3,
                neighbor_k=1,
                cluster_hit_ks=(1, 2),
                recall_ks=(1,),
                query_split="test",
                embedding_cache_dir=cache_dir,
                use_embedding_cache=True,
            )

            self.assertFalse(first["corpus_embedding_cache_hit"])
            self.assertFalse(first["query_embedding_cache_hit"])
            self.assertTrue(second["corpus_embedding_cache_hit"])
            self.assertTrue(second["query_embedding_cache_hit"])

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
                    "chunk_id": "toy_100k_c0",
                    "text": "alpha document",
                    "metadata": {"original_corpus_id": "0"},
                },
                {
                    "chunk_id": "toy_100k_c1",
                    "text": "beta document",
                    "metadata": {"original_corpus_id": "1"},
                },
                {
                    "chunk_id": "toy_100k_c2",
                    "text": "gamma document",
                    "metadata": {"original_corpus_id": "2"},
                },
            ]
            queries = [
                {
                    "query_id": "q_alpha",
                    "text": "alpha query",
                    "ground_truth_chunk_ids": ["toy_100k_c0"],
                    "split": "test",
                }
            ]
            (data_dir / "toy_100k_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (data_dir / "toy_100k_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            np.save(
                store_dir / "canonical_corpus_embeddings.npy",
                np.asarray([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32),
            )
            (store_dir / "canonical_corpus_ids.json").write_text(
                json.dumps({
                    "canonical_ids": ["toy_orig_0", "toy_orig_1", "toy_orig_2"],
                    "text_sha256": ["unused", "unused", "unused"],
                    "source_datasets": [["toy_100k"], ["toy_100k"], ["toy_100k"]],
                }),
                encoding="utf-8",
            )
            encoder = FakeEncoder({"alpha query": [1.0, 0.0]})

            metrics = manifold_diagnostics.run_dataset(
                "toy_100k",
                data_dir,
                out_dir,
                encoder,
                model_name="fake-model",
                batch_size=1,
                n_clusters=2,
                context_dim=2,
                seed=13,
                sample_size=3,
                neighbor_k=1,
                cluster_hit_ks=(1, 2),
                recall_ks=(1,),
                query_split="test",
                use_scale_store=True,
                scale_store_dir=store_dir,
                scale_store_canonical_name="toy",
            )

            self.assertTrue(metrics["scale_store_enabled"])
            self.assertEqual(metrics["scale_store_selected_rows"], 3)
            self.assertEqual(metrics["scale_store_canonical_count"], 3)
            self.assertTrue(metrics["corpus_embedding_cache_hit"])
            self.assertAlmostEqual(metrics["dense_gt_recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
