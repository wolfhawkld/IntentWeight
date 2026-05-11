#!/usr/bin/env python3
"""Tests for LoTTE canonical scale store construction."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "paper" / "experiments" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


embedding_cache = load_module("embedding_cache", SCRIPT_DIR / "embedding_cache.py")
lotte_scale_store = load_module("lotte_scale_store", SCRIPT_DIR / "lotte_scale_store.py")


class FakeEncoder:
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            if "alpha" in text:
                vectors.append([1.0, 0.0])
            elif "beta" in text:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([1.0, 1.0])
        return np.asarray(vectors, dtype=np.float32)


class LotteScaleStoreTests(unittest.TestCase):
    def test_build_scale_store_reuses_original_corpus_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "processed"
            cache_dir = root / "embeddings"
            store_dir = root / "scale_store"
            data_dir.mkdir()

            d100 = [
                {
                    "chunk_id": "lotte_100k_c0",
                    "text": "alpha document",
                    "metadata": {"original_corpus_id": "0"},
                },
                {
                    "chunk_id": "lotte_100k_c1",
                    "text": "beta document",
                    "metadata": {"original_corpus_id": "1"},
                },
            ]
            d200 = [
                {
                    "chunk_id": "lotte_200k_c0",
                    "text": "alpha document",
                    "metadata": {"original_corpus_id": "0"},
                },
                {
                    "chunk_id": "lotte_200k_c1",
                    "text": "beta document",
                    "metadata": {"original_corpus_id": "1"},
                },
                {
                    "chunk_id": "lotte_200k_c2",
                    "text": "gamma document",
                    "metadata": {"original_corpus_id": "2"},
                },
            ]
            q100 = [{"query_id": "q1", "text": "alpha", "ground_truth_chunk_ids": ["lotte_100k_c0"]}]
            q200 = [{"query_id": "q1", "text": "alpha", "ground_truth_chunk_ids": ["lotte_200k_c0"]}]

            for dataset, corpus, queries in [
                ("lotte_technology_search_100k", d100, q100),
                ("lotte_technology_search_200k", d200, q200),
            ]:
                (data_dir / f"{dataset}_corpus.json").write_text(
                    json.dumps(corpus),
                    encoding="utf-8",
                )
                (data_dir / f"{dataset}_queries.json").write_text(
                    json.dumps(queries),
                    encoding="utf-8",
                )
                embedding_cache.load_or_compute_embeddings(
                    corpus,
                    dataset=dataset,
                    model_name="fake-model",
                    record_kind="corpus",
                    encoder=FakeEncoder(),
                    batch_size=2,
                    cache_dir=cache_dir,
                )

            summary = lotte_scale_store.build_scale_store(
                ["lotte_technology_search_100k", "lotte_technology_search_200k"],
                canonical_name="lotte_technology_search",
                model_name="fake-model",
                data_dir=data_dir,
                embedding_cache_dir=cache_dir,
                store_dir=store_dir,
            )

            self.assertEqual(summary["canonical_count"], 3)
            self.assertEqual(summary["embedding_shape"], [3, 2])
            rows_100 = np.load(store_dir / "lotte_technology_search_100k__row_indices.npy")
            rows_200 = np.load(store_dir / "lotte_technology_search_200k__row_indices.npy")
            np.testing.assert_array_equal(rows_100, [0, 1])
            np.testing.assert_array_equal(rows_200, [0, 1, 2])

            ids = json.loads((store_dir / "canonical_corpus_ids.json").read_text(encoding="utf-8"))
            self.assertEqual(
                ids["canonical_ids"],
                [
                    "lotte_technology_search_orig_0",
                    "lotte_technology_search_orig_1",
                    "lotte_technology_search_orig_2",
                ],
            )
            manifest_200 = json.loads(
                (store_dir / "lotte_technology_search_200k__manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest_200["new_canonical_rows"], 1)
            self.assertEqual(manifest_200["reused_canonical_rows"], 2)

    def test_append_existing_store_encodes_only_missing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "processed"
            cache_dir = root / "embeddings"
            store_dir = root / "scale_store"
            data_dir.mkdir()

            d100 = [
                {"chunk_id": "s100_c0", "text": "alpha document", "metadata": {"original_corpus_id": "0"}},
                {"chunk_id": "s100_c1", "text": "beta document", "metadata": {"original_corpus_id": "1"}},
            ]
            d400 = [
                {"chunk_id": "s400_c0", "text": "alpha document", "metadata": {"original_corpus_id": "0"}},
                {"chunk_id": "s400_c1", "text": "beta document", "metadata": {"original_corpus_id": "1"}},
                {"chunk_id": "s400_c2", "text": "gamma document", "metadata": {"original_corpus_id": "2"}},
            ]
            queries = [{"query_id": "q1", "text": "alpha", "ground_truth_chunk_ids": ["s100_c0"]}]
            for dataset, corpus in [
                ("lotte_technology_search_100k", d100),
                ("lotte_technology_search_400k", d400),
            ]:
                (data_dir / f"{dataset}_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
                (data_dir / f"{dataset}_queries.json").write_text(json.dumps(queries), encoding="utf-8")

            embedding_cache.load_or_compute_embeddings(
                d100,
                dataset="lotte_technology_search_100k",
                model_name="fake-model",
                record_kind="corpus",
                encoder=FakeEncoder(),
                batch_size=2,
                cache_dir=cache_dir,
            )
            first = lotte_scale_store.build_scale_store(
                ["lotte_technology_search_100k"],
                canonical_name="lotte_technology_search",
                model_name="fake-model",
                data_dir=data_dir,
                embedding_cache_dir=cache_dir,
                store_dir=store_dir,
            )
            self.assertEqual(first["canonical_count"], 2)

            appended = lotte_scale_store.build_scale_store(
                ["lotte_technology_search_400k"],
                canonical_name="lotte_technology_search",
                model_name="fake-model",
                data_dir=data_dir,
                embedding_cache_dir=cache_dir,
                store_dir=store_dir,
                append_existing_store=True,
                compute_missing=True,
                encoder=FakeEncoder(),
                batch_size=2,
            )

            self.assertEqual(appended["initial_canonical_count"], 2)
            self.assertEqual(appended["canonical_count"], 3)
            self.assertEqual(appended["new_canonical_rows"], 1)
            manifest = json.loads(
                (store_dir / "lotte_technology_search_400k__manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(manifest["dataset_embedding_cache_hit"])
            self.assertEqual(manifest["reused_canonical_rows"], 2)
            self.assertEqual(manifest["encoded_missing_rows"], 1)
            rows_400 = np.load(store_dir / "lotte_technology_search_400k__row_indices.npy")
            np.testing.assert_array_equal(rows_400, [0, 1, 2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
