#!/usr/bin/env python3
"""Tests for global vs manifold-local LinUCB comparison tables."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "compare_linucb_variants.py"

spec = importlib.util.spec_from_file_location("compare_linucb_variants", MODULE_PATH)
compare_linucb_variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_linucb_variants)


class CompareLinUCBVariantsTests(unittest.TestCase):
    def _row(self, dataset, method, recall10, mrr10, *, task_type="evidence_retrieval", scope="full"):
        return {
            "dataset": dataset,
            "method": method,
            "task_type": task_type,
            "scope": scope,
            "query_split": "test",
            "corpus_scope": "full",
            "top_k": "10",
            "metric_ks": "1,5,10",
            "num_queries": "10",
            "num_skipped_no_gt": "0",
            "gt_query_coverage": "1.0",
            "num_seeds": "3",
            "recall@1_mean": "0.1",
            "recall@5_mean": "0.3",
            "recall@10_mean": str(recall10),
            "mrr@10_mean": str(mrr10),
            "ndcg@10_mean": "0.2",
            "avg_feedback_reward_mean": str(recall10),
            "avg_local_boost_norm_mean": "0.05",
            "cross_arm_update_weight_mean": "12.0",
            "notes": "",
        }

    def test_compare_rows_computes_delta_and_winner(self):
        global_rows = [self._row("demo", "linucb_global", 0.4, 0.2)]
        manifold_rows = [self._row("demo", "linucb_manifold_local", 0.5, 0.25)]

        rows = compare_linucb_variants.compare_rows(global_rows, manifold_rows)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["delta_recall@10_mean"], "0.1000")
        self.assertEqual(rows[0]["relative_recall@10_pct"], "25.00")
        self.assertEqual(rows[0]["winner_recall@10"], "manifold_local")
        self.assertIn("improves", rows[0]["interpretation"])

    def test_compare_rows_skips_non_matching_protocol_scope(self):
        global_rows = [self._row("demo", "linucb_global", 0.4, 0.2)]
        manifold = self._row("demo", "linucb_manifold_local", 0.5, 0.25)
        manifold["corpus_scope"] = "first_100"

        rows = compare_linucb_variants.compare_rows(global_rows, [manifold])

        self.assertEqual(rows, [])

    def test_build_comparison_writes_csv_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            global_summary = tmpdir / "global.csv"
            manifold_summary = tmpdir / "manifold.csv"
            fieldnames = sorted(set(self._row("demo", "linucb_global", 0.4, 0.2)))
            with global_summary.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerow(self._row("demo", "linucb_global", 0.4, 0.2))
            with manifold_summary.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerow(self._row("demo", "linucb_manifold_local", 0.3, 0.15))

            rows = compare_linucb_variants.build_comparison(
                global_summary,
                manifold_summary,
                tmpdir / "comparison.csv",
                tmpdir / "comparison.md",
            )

            self.assertEqual(len(rows), 1)
            self.assertTrue((tmpdir / "comparison.csv").exists())
            markdown = (tmpdir / "comparison.md").read_text(encoding="utf-8")
            self.assertIn("LinUCB Variant Comparison", markdown)
            self.assertIn("global remains stronger", markdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
