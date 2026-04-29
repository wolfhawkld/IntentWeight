#!/usr/bin/env python3
"""Tests for paper-ready retrieval baseline table generation."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "summarize_retrieval_baselines.py"

spec = importlib.util.spec_from_file_location("summarize_retrieval_baselines", MODULE_PATH)
summarize_retrieval_baselines = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_retrieval_baselines)


class SummarizeRetrievalBaselinesTests(unittest.TestCase):
    def test_main_evidence_table_excludes_smoke_and_intent_proxy_rows(self):
        rows = [
            {
                "dataset": "pubmedqa",
                "method": "bm25",
                "task_type": "evidence_retrieval",
                "scope": "full",
                "corpus_scope": "full",
                "is_comparable": "true",
            },
            {
                "dataset": "cuad",
                "method": "bm25",
                "task_type": "evidence_retrieval",
                "scope": "smoke_only",
                "corpus_scope": "first_10000",
                "is_comparable": "true",
            },
            {
                "dataset": "banking77",
                "method": "bm25",
                "task_type": "intent_retrieval_proxy",
                "scope": "heldout_test",
                "corpus_scope": "full",
                "is_comparable": "true",
            },
            {
                "dataset": "emanual",
                "method": "dense",
                "task_type": "evidence_retrieval",
                "scope": "heldout_test",
                "corpus_scope": "full",
                "is_comparable": "false",
            },
        ]

        selected = summarize_retrieval_baselines.select_main_evidence_rows(rows)

        self.assertEqual([row["dataset"] for row in selected], ["pubmedqa"])

    def test_build_tables_writes_main_proxy_smoke_and_markdown_outputs(self):
        fieldnames = [
            "dataset",
            "task_type",
            "method",
            "scope",
            "query_split",
            "corpus_scope",
            "is_comparable",
            "num_corpus_chunks",
            "num_queries",
            "num_skipped_no_gt",
            "recall@1",
            "recall@5",
            "recall@10",
            "mrr@10",
            "ndcg@10",
            "elapsed_sec",
            "notes",
        ]
        rows = [
            {
                "dataset": "emanual",
                "task_type": "evidence_retrieval",
                "method": "dense",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "is_comparable": "true",
                "num_corpus_chunks": "10",
                "num_queries": "3",
                "num_skipped_no_gt": "0",
                "recall@1": "0.1",
                "recall@5": "0.2",
                "recall@10": "0.3",
                "mrr@10": "0.4",
                "ndcg@10": "0.5",
                "elapsed_sec": "1.2345",
                "notes": "Dense encoder is all-MiniLM-L6-v2.",
            },
            {
                "dataset": "banking77",
                "task_type": "intent_retrieval_proxy",
                "method": "bm25",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "is_comparable": "true",
            },
            {
                "dataset": "cuad",
                "task_type": "evidence_retrieval",
                "method": "hybrid_rrf",
                "scope": "smoke_only",
                "query_split": "test",
                "corpus_scope": "first_10000",
                "is_comparable": "true",
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            comparison = tmpdir / "comparison.csv"
            with comparison.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)

            tables = summarize_retrieval_baselines.build_tables(comparison, tmpdir)

            self.assertEqual(len(tables["main"]), 1)
            self.assertEqual(len(tables["intent_proxy"]), 1)
            self.assertEqual(len(tables["smoke"]), 1)
            self.assertTrue((tmpdir / "retrieval_baseline_main_table.csv").exists())
            self.assertTrue((tmpdir / "retrieval_baseline_intent_proxy_table.csv").exists())
            self.assertTrue((tmpdir / "retrieval_baseline_smoke_table.csv").exists())
            markdown = (tmpdir / "retrieval_baseline_tables.md").read_text(encoding="utf-8")
            self.assertIn("Evidence Retrieval Main Table", markdown)
            self.assertIn("CUAD is reported only as a smoke/sample result", markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
