#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for paper/experiments/scripts/validate_processed.py.

Run from repo root:
    .venv/bin/python cache/test_validate_processed.py
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "validate_processed.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_processed", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateProcessedTests(unittest.TestCase):
    def test_validate_dataset_reports_counts_and_missing_gt_refs(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            processed = Path(tmpdir)
            corpus = [
                {"chunk_id": "c1", "text": "First chunk."},
                {"chunk_id": "c2", "text": "Second chunk."},
            ]
            queries = [
                {"query_id": "q1", "text": "known", "ground_truth_chunk_ids": ["c1"]},
                {"query_id": "q2", "text": "missing", "ground_truth_chunk_ids": ["missing"]},
                {"query_id": "q3", "text": "empty", "ground_truth_chunk_ids": []},
            ]
            (processed / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (processed / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")

            with patch.object(module, "PROCESSED_DIR", str(processed)):
                summary = module.validate_dataset("toy")

            self.assertEqual(summary["dataset"], "toy")
            self.assertEqual(summary["corpus_chunks"], 2)
            self.assertEqual(summary["queries"], 3)
            self.assertEqual(summary["queries_with_gt"], 2)
            self.assertEqual(summary["missing_gt_chunk_refs"], 1)
            self.assertFalse(summary["valid"])
            self.assertIn("missing_gt_chunk_refs", summary["errors"][0])

    def test_validate_dataset_marks_valid_data(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            processed = Path(tmpdir)
            corpus = [{"chunk_id": "c1", "text": "First chunk."}]
            queries = [{"query_id": "q1", "text": "known", "ground_truth_chunk_ids": ["c1"]}]
            (processed / "toy_corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
            (processed / "toy_queries.json").write_text(json.dumps(queries), encoding="utf-8")

            with patch.object(module, "PROCESSED_DIR", str(processed)):
                summary = module.validate_dataset("toy")

            self.assertTrue(summary["valid"])
            self.assertEqual(summary["gt_coverage"], 1.0)
            self.assertEqual(summary["missing_gt_chunk_refs"], 0)
            self.assertEqual(summary["errors"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
