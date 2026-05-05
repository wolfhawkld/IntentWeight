#!/usr/bin/env python3
"""Tests for reusable experiment embedding cache."""
import importlib.util
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
