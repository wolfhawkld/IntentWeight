#!/usr/bin/env python3
"""Tests for soft-routed manifold LinUCB table builder."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "summarize_linucb_soft.py"

spec = importlib.util.spec_from_file_location("summarize_linucb_soft", MODULE_PATH)
summarize_linucb_soft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_linucb_soft)


class SummarizeLinUCBSoftTests(unittest.TestCase):
    def test_row_selection_and_compaction(self):
        rows = [
            {
                "dataset": "pubmedqa",
                "method": "linucb_soft_manifold",
                "task_type": "evidence_retrieval",
                "scope": "heldout_test",
                "corpus_scope": "full",
                "recall@10_mean": "0.95123",
                "selected_cluster_hit_rate_mean": "0.451",
            },
            {
                "dataset": "banking77",
                "method": "linucb_soft_manifold",
                "task_type": "intent_retrieval_proxy",
                "scope": "heldout_test",
                "corpus_scope": "full",
            },
            {
                "dataset": "cuad",
                "method": "linucb_soft_manifold",
                "task_type": "evidence_retrieval",
                "scope": "smoke_only",
                "corpus_scope": "gt_anchored_10000",
            },
        ]

        main_rows = summarize_linucb_soft.select_main_evidence_rows(rows)
        intent_rows = summarize_linucb_soft.select_intent_proxy_rows(rows)
        smoke_rows = summarize_linucb_soft.select_smoke_rows(rows)
        compact = summarize_linucb_soft.compact_row(main_rows[0])

        self.assertEqual([row["dataset"] for row in main_rows], ["pubmedqa"])
        self.assertEqual([row["dataset"] for row in intent_rows], ["banking77"])
        self.assertEqual([row["dataset"] for row in smoke_rows], ["cuad"])
        self.assertEqual(compact["method"], "Soft-Routed Manifold LinUCB")
        self.assertEqual(compact["recall@10_mean"], "0.9512")

    def test_build_tables_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            summary = tmpdir / "summary.csv"
            output_dir = tmpdir / "out"
            rows = [
                {
                    "dataset": "pubmedqa",
                    "method": "linucb_soft_manifold",
                    "protocol": "prequential",
                    "task_type": "evidence_retrieval",
                    "scope": "heldout_test",
                    "query_split": "test",
                    "corpus_scope": "full",
                    "recall@10_mean": "0.9",
                    "mrr@10_mean": "0.8",
                    "selected_cluster_hit_rate_mean": "0.4",
                    "soft_rescue_on_cluster_miss_rate_mean": "0.7",
                }
            ]
            with summary.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)

            tables = summarize_linucb_soft.build_tables(summary, output_dir)

            self.assertEqual(len(tables["main"]), 1)
            self.assertTrue((output_dir / "linucb_soft_main_table.csv").exists())
            self.assertTrue((output_dir / "linucb_soft_intent_proxy_table.csv").exists())
            self.assertTrue((output_dir / "linucb_soft_smoke_table.csv").exists())
            self.assertTrue((output_dir / "linucb_soft_tables.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
