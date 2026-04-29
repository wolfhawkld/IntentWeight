#!/usr/bin/env python3
"""Tests for manifold-local LinUCB table generation."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "summarize_linucb_manifold.py"

spec = importlib.util.spec_from_file_location("summarize_linucb_manifold", MODULE_PATH)
summarize_linucb_manifold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_linucb_manifold)


class SummarizeManifoldLinUCBTests(unittest.TestCase):
    def _write_summary(self, path: Path):
        rows = [
            {"dataset": "pubmedqa", "task_type": "evidence_retrieval", "scope": "full", "corpus_scope": "full"},
            {"dataset": "banking77", "task_type": "intent_retrieval_proxy", "scope": "heldout_test", "corpus_scope": "full"},
            {"dataset": "cuad", "task_type": "evidence_retrieval", "scope": "smoke_only", "corpus_scope": "gt_anchored_10000"},
        ]
        for row in rows:
            row.update({
                "method": "linucb_manifold_local",
                "protocol": "prequential",
                "query_split": "test",
                "num_queries": "10",
                "num_skipped_no_gt": "0",
                "gt_query_coverage": "1.0",
                "num_seeds": "2",
                "recall@1_mean": "0.1",
                "recall@10_mean": "0.5",
                "mrr@10_mean": "0.2",
                "avg_local_boost_norm_mean": "0.03",
                "cross_arm_update_weight_mean": "12.0",
                "notes": "",
            })
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sorted({key for row in rows for key in row}), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_build_tables_splits_main_proxy_and_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            summary = tmpdir / "linucb_manifold_summary.csv"
            self._write_summary(summary)

            tables = summarize_linucb_manifold.build_tables(summary, tmpdir)

            self.assertEqual(len(tables["main"]), 1)
            self.assertEqual(len(tables["intent_proxy"]), 1)
            self.assertEqual(len(tables["smoke"]), 1)
            self.assertTrue((tmpdir / "linucb_manifold_tables.md").exists())
            markdown = (tmpdir / "linucb_manifold_tables.md").read_text(encoding="utf-8")
            self.assertIn("Manifold-Local LinUCB", markdown)
            self.assertIn("cross_arm_update_weight_mean", markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
