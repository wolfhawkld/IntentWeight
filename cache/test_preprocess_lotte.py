#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the LoTTE preprocessing helpers.

Run from repo root:
    .venv/bin/python cache/test_preprocess_lotte.py
"""
import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "preprocess_lotte.py"


def load_module():
    spec = importlib.util.spec_from_file_location("preprocess_lotte", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreprocessLoTTETests(unittest.TestCase):
    def test_lotte_ids_and_text_are_stable(self):
        module = load_module()

        self.assertEqual(module.dataset_name("Technology", "Search"), "lotte_technology_search")
        self.assertEqual(module.hf_config("technology", "search", "qrels"), "technology_search-qrels")
        self.assertEqual(module.processed_corpus_id("lotte_technology_search", "101"), "lotte_technology_search_c101")
        self.assertEqual(module.processed_query_id("lotte_technology_search", "7"), "lotte_technology_search_q7")
        self.assertEqual(module.combine_title_text("Title", "Body"), "Title\nBody")
        self.assertEqual(module.combine_title_text("", "Body"), "Body")

    def test_positive_qrels_groups_and_deduplicates(self):
        module = load_module()
        rows = [
            {"query-id": "2", "corpus-id": "9", "score": 1},
            {"query-id": "2", "corpus-id": "9", "score": 1},
            {"query-id": "2", "corpus-id": "10", "score": 1},
            {"query-id": "3", "corpus-id": "11", "score": 0},
        ]

        grouped = module.positive_qrels(rows)

        self.assertEqual(grouped, {"2": ["9", "10"]})
        self.assertEqual(module.select_query_ids(grouped, max_queries=1), ["2"])

    def test_record_builders_preserve_gt_mapping(self):
        module = load_module()
        name = "lotte_technology_search"
        corpus = module.build_corpus_records(
            [{"_id": "9", "title": "", "text": "relevant chunk"}],
            name=name,
            domain="technology",
            mode="search",
            split="test",
        )
        queries = module.build_query_records(
            {"2": {"_id": "2", "text": "sample query"}},
            selected_query_ids=["2"],
            qrels_by_query={"2": ["9"]},
            name=name,
            domain="technology",
            mode="search",
            split="test",
        )

        self.assertEqual(corpus[0]["chunk_id"], "lotte_technology_search_c9")
        self.assertEqual(queries[0]["query_id"], "lotte_technology_search_q2")
        self.assertEqual(queries[0]["ground_truth_chunk_ids"], ["lotte_technology_search_c9"])
        self.assertEqual(queries[0]["split"], "test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
