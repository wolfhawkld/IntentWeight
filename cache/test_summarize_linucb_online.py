#!/usr/bin/env python3
"""Tests for global LinUCB online table generation."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "summarize_linucb_online.py"

spec = importlib.util.spec_from_file_location("summarize_linucb_online", MODULE_PATH)
summarize_linucb_online = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_linucb_online)


class SummarizeLinUCBOnlineTests(unittest.TestCase):
    def test_main_table_excludes_proxy_and_smoke_rows(self):
        rows = [
            {"dataset": "pubmedqa", "task_type": "evidence_retrieval", "scope": "full", "corpus_scope": "full"},
            {"dataset": "cuad", "task_type": "evidence_retrieval", "scope": "smoke_only", "corpus_scope": "first_10000"},
            {"dataset": "banking77", "task_type": "intent_retrieval_proxy", "scope": "heldout_test", "corpus_scope": "full"},
        ]

        selected = summarize_linucb_online.select_main_evidence_rows(rows)

        self.assertEqual([row["dataset"] for row in selected], ["pubmedqa"])

    def test_build_tables_writes_outputs(self):
        fieldnames = [
            "dataset",
            "method",
            "protocol",
            "task_type",
            "scope",
            "query_split",
            "corpus_scope",
            "num_queries",
            "num_skipped_no_gt",
            "num_seeds",
            "recall@10_mean",
            "mrr@10_mean",
            "ndcg@10_mean",
            "notes",
        ]
        rows = [
            {
                "dataset": "emanual",
                "method": "linucb_global",
                "protocol": "prequential",
                "task_type": "evidence_retrieval",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "num_queries": "2",
                "num_skipped_no_gt": "0",
                "num_seeds": "3",
                "recall@10_mean": "0.25",
                "mrr@10_mean": "0.125",
                "ndcg@10_mean": "0.1",
                "notes": "",
            },
            {
                "dataset": "banking77",
                "task_type": "intent_retrieval_proxy",
                "scope": "heldout_test",
                "corpus_scope": "full",
            },
            {
                "dataset": "cuad",
                "task_type": "evidence_retrieval",
                "scope": "smoke_only",
                "corpus_scope": "first_10000",
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            summary = tmpdir / "linucb_online_summary.csv"
            with summary.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)

            tables = summarize_linucb_online.build_tables(summary, tmpdir)

            self.assertEqual(len(tables["main"]), 1)
            self.assertEqual(len(tables["intent_proxy"]), 1)
            self.assertEqual(len(tables["smoke"]), 1)
            self.assertTrue((tmpdir / "linucb_online_main_table.csv").exists())
            self.assertTrue((tmpdir / "linucb_online_intent_proxy_table.csv").exists())
            self.assertTrue((tmpdir / "linucb_online_smoke_table.csv").exists())
            markdown = (tmpdir / "linucb_online_tables.md").read_text(encoding="utf-8")
            self.assertIn("prequential", markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
