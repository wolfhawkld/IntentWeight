#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for paper/experiments/scripts/preprocess_ragbench.py.

Run from repo root:
    .venv/bin/python cache/test_preprocess_ragbench.py
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "preprocess_ragbench.py"


def load_module():
    spec = importlib.util.spec_from_file_location("preprocess_ragbench", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreprocessRagbenchTests(unittest.TestCase):
    def test_process_dataset_maps_relevant_sentence_keys_to_chunk_ids(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            raw = tmp / "raw"
            processed = tmp / "processed"
            raw.mkdir()
            processed.mkdir()

            df = pd.DataFrame([
                {
                    "id": "demo_001",
                    "question": "How do I enable ambient mode?",
                    "response": "Press the Ambient Mode button.",
                    "documents_sentences": [
                        [["0a", "Ambient mode overview."], ["0b", "Press the Ambient Mode button."]],
                        [["1a", "Use Settings for display options."]],
                    ],
                    "all_relevant_sentence_keys": ["0b", "1a"],
                    "all_utilized_sentence_keys": ["0b"],
                    "relevance_score": 0.5,
                    "utilization_score": 0.25,
                    "completeness_score": 1.0,
                    "ragas_faithfulness": 0.8,
                    "ragas_context_relevance": 0.4,
                }
            ])
            (raw / "demo_train.parquet").write_bytes(b"dummy parquet path; pandas.read_parquet is patched")

            with patch.object(module, "RAW_DIR", str(raw)), \
                 patch.object(module, "PROCESSED_DIR", str(processed)), \
                 patch.object(module, "DATASET_FILES", {"demo": {"train": "demo_train.parquet"}}), \
                 patch.object(module.pd, "read_parquet", return_value=df):
                stats = module.process_dataset("demo")

            self.assertEqual(stats["corpus_chunks"], 3)
            self.assertEqual(stats["queries"], 1)
            self.assertEqual(stats["queries_with_gt"], 1)

            corpus = json.loads((processed / "demo_corpus.json").read_text(encoding="utf-8"))
            queries = json.loads((processed / "demo_queries.json").read_text(encoding="utf-8"))

            self.assertEqual(len(corpus), 3)
            self.assertEqual(len(queries), 1)
            query = queries[0]
            self.assertEqual(query["text"], "How do I enable ambient mode?")
            self.assertEqual(query["answer"], "Press the Ambient Mode button.")
            self.assertEqual(set(query["ground_truth_chunk_ids"]), {"demo_demo_001_0b", "demo_demo_001_1a"})
            self.assertEqual(query["metadata"]["source"], "demo")
            self.assertEqual(query["metadata"]["split"], "train")

            chunk_by_id = {c["chunk_id"]: c for c in corpus}
            self.assertEqual(chunk_by_id["demo_demo_001_0b"]["text"], "Press the Ambient Mode button.")
            self.assertEqual(chunk_by_id["demo_demo_001_0b"]["metadata"]["sentence_key"], "0b")
            self.assertEqual(chunk_by_id["demo_demo_001_0b"]["metadata"]["doc_index"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
