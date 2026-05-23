#!/usr/bin/env python3
"""Tests for final context token cost evaluation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "context_token_cost.py"

spec = importlib.util.spec_from_file_location("context_token_cost", MODULE_PATH)
context_token_cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context_token_cost)


class ContextTokenCostTests(unittest.TestCase):
    def test_load_flat_and_nested_ranking_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            flat = tmpdir / "flat.json"
            nested = tmpdir / "nested.json"
            flat.write_text(json.dumps({"q1": ["c1", "c2"]}), encoding="utf-8")
            nested.write_text(json.dumps({"gated": {"13": {"q1": ["c2", "c1"]}}}), encoding="utf-8")

            flat_variants = context_token_cost.load_ranking_variants("dense", flat)
            nested_variants = context_token_cost.load_ranking_variants("linucb", nested)

            self.assertEqual(flat_variants[0].run_id, "dense")
            self.assertEqual(nested_variants[0].run_id, "linucb:gated:seed13")
            self.assertEqual(nested_variants[0].rankings["q1"], ["c2", "c1"])

    def test_context_token_metrics_and_baseline_ratio(self):
        queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["c2"]}]
        chunk_tokens = {"c1": 2, "c2": 3, "c3": 5}
        dense = context_token_cost.RankingVariant("dense", "dense", "dense", "", {"q1": ["c1", "c2"]})
        shorter = context_token_cost.RankingVariant("short", "short", "short", "", {"q1": ["c2"]})

        rows = [
            context_token_cost.evaluate_variant(dense, queries, chunk_tokens, ks=(1, 2), skip_empty_gt=True),
            context_token_cost.evaluate_variant(shorter, queries, chunk_tokens, ks=(1, 2), skip_empty_gt=True),
        ]
        context_token_cost.add_baseline_ratios(rows, "dense", (1, 2))

        self.assertEqual(rows[0]["avg_context_tokens@2"], 5.0)
        self.assertEqual(rows[1]["avg_context_tokens@2"], 3.0)
        self.assertEqual(rows[1]["context_token_ratio_vs_baseline@2"], 0.6)
        self.assertEqual(rows[1]["hit@1"], 1.0)
        self.assertEqual(rows[1]["hit_delta_vs_baseline@1"], 1.0)

    def test_cli_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            corpus = [{"chunk_id": "c1", "text": "alpha beta"}, {"chunk_id": "c2", "text": "gamma"}]
            queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["c2"]}]
            rankings = {"q1": ["c2", "c1"]}
            corpus_path = tmpdir / "corpus.json"
            queries_path = tmpdir / "queries.json"
            rankings_path = tmpdir / "rankings.json"
            csv_path = tmpdir / "out.csv"
            json_path = tmpdir / "out.json"
            md_path = tmpdir / "out.md"
            corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
            queries_path.write_text(json.dumps(queries), encoding="utf-8")
            rankings_path.write_text(json.dumps(rankings), encoding="utf-8")

            rc = context_token_cost.main([
                "--corpus", str(corpus_path),
                "--queries", str(queries_path),
                "--ranking", f"dense={rankings_path}",
                "--ks", "1,2",
                "--tokenizer", "simple",
                "--baseline-run-id", "dense",
                "--output-csv", str(csv_path),
                "--output-json", str(json_path),
                "--output-md", str(md_path),
            ])

            self.assertEqual(rc, 0)
            self.assertTrue(csv_path.exists())
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
