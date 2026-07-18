#!/usr/bin/env python3
"""Tests for reusable experiment embedding cache."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "embedding_cache.py"

spec = importlib.util.spec_from_file_location("embedding_cache", MODULE_PATH)
embedding_cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embedding_cache)


class FakeEncoder:
    def __init__(self):
        self.calls = 0

    def encode(self, texts, **kwargs):
        self.calls += 1
        vectors = []
        for text in texts:
            if "alpha" in text:
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return np.asarray(vectors, dtype=np.float32)


class EmbeddingCacheTests(unittest.TestCase):
    def test_load_or_compute_embeddings_reuses_matching_cache(self):
        records = [
            {"chunk_id": "c1", "text": "alpha document"},
            {"chunk_id": "c2", "text": "beta document"},
        ]
        encoder = FakeEncoder()

        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            first, first_info = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                record_kind="corpus",
                encoder=encoder,
                batch_size=2,
                cache_dir=cache_dir,
            )
            second, second_info = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                record_kind="corpus",
                encoder=encoder,
                batch_size=2,
                cache_dir=cache_dir,
            )

            self.assertFalse(first_info["cache_hit"])
            self.assertTrue(second_info["cache_hit"])
            self.assertEqual(encoder.calls, 1)
            self.assertTrue(Path(first_info["embedding_path"]).exists())
            self.assertTrue(Path(first_info["metadata_path"]).exists())
            np.testing.assert_allclose(first, second)
            np.testing.assert_allclose(np.linalg.norm(second, axis=1), [1.0, 1.0])

    def test_records_fingerprint_changes_when_text_changes(self):
        first = [{"query_id": "q1", "text": "alpha"}]
        second = [{"query_id": "q1", "text": "beta"}]

        self.assertNotEqual(
            embedding_cache.records_fingerprint(first, "queries"),
            embedding_cache.records_fingerprint(second, "queries"),
        )

    def test_model_revision_invalidates_same_named_cache(self):
        records = [{"chunk_id": "c1", "text": "alpha document"}]
        encoder = FakeEncoder()

        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            _, first = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )
            _, second = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )
            _, third = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-b",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )

            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertFalse(third["cache_hit"])
            self.assertEqual(third["model_revision"], "revision-b")
            self.assertEqual(encoder.calls, 2)

    def test_corrupted_embedding_content_is_recomputed(self):
        records = [{"chunk_id": "c1", "text": "alpha document"}]
        encoder = FakeEncoder()

        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            expected, first = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )
            corrupted = np.load(first["embedding_path"], mmap_mode="r+")
            corrupted[0, 0] = np.float32(0.25)
            corrupted.flush()
            del corrupted

            repaired, repaired_info = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )

            self.assertFalse(repaired_info["cache_hit"])
            self.assertEqual(encoder.calls, 2)
            np.testing.assert_array_equal(repaired, expected)
            metadata = json.loads(Path(repaired_info["metadata_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(metadata["embedding_content_fingerprint"]), 64)

    def test_truncated_embedding_file_is_recomputed(self):
        records = [{"chunk_id": "c1", "text": "alpha document"}]
        encoder = FakeEncoder()

        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            expected, first = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )
            Path(first["embedding_path"]).write_bytes(b"truncated")

            repaired, repaired_info = embedding_cache.load_or_compute_embeddings(
                records,
                dataset="toy",
                model_name="fake-model",
                model_revision="revision-a",
                record_kind="corpus",
                encoder=encoder,
                batch_size=1,
                cache_dir=cache_dir,
            )

            self.assertFalse(repaired_info["cache_hit"])
            self.assertEqual(encoder.calls, 2)
            np.testing.assert_array_equal(repaired, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
