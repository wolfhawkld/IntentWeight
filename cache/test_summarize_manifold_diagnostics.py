#!/usr/bin/env python3
"""Tests for manifold diagnostics comparison tables."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "summarize_manifold_diagnostics.py"

spec = importlib.util.spec_from_file_location("summarize_manifold_diagnostics", MODULE_PATH)
summarize_manifold_diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize_manifold_diagnostics)


class SummarizeManifoldDiagnosticsTests(unittest.TestCase):
    def test_build_comparison_joins_dense_and_soft_gain(self):
        diagnostics = [{
            "dataset": "pubmedqa",
            "task_type": "evidence_retrieval",
            "scope": "full",
            "query_split": "train",
            "corpus_scope": "full",
            "nearest_cluster_hit@3": "0.8",
            "local_label_purity": "0.7",
            "context_recall_retention@10": "0.9",
        }]
        dense = [{
            "dataset": "pubmedqa",
            "scope": "full",
            "query_split": "train",
            "corpus_scope": "full",
            "recall@10": "0.9",
        }]
        soft = [{
            "dataset": "pubmedqa",
            "scope": "full",
            "query_split": "train",
            "corpus_scope": "full",
            "recall@10_mean": "0.95",
            "selected_cluster_hit_rate_mean": "0.7",
        }]

        rows = summarize_manifold_diagnostics.build_comparison(diagnostics, dense, soft)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["soft_minus_dense_recall@10"], "0.0500")
        self.assertEqual(rows[0]["soft_selected_cluster_hit_rate"], "0.7000")
        self.assertIn("local routing", rows[0]["interpretation"])

    def test_build_tables_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            diagnostics_path = tmpdir / "diag.csv"
            dense_path = tmpdir / "dense.csv"
            soft_path = tmpdir / "soft.csv"
            output_csv = tmpdir / "out.csv"
            output_md = tmpdir / "out.md"

            def write(path, rows):
                with path.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
                    writer.writeheader()
                    writer.writerows(rows)

            write(diagnostics_path, [{
                "dataset": "emanual",
                "task_type": "evidence_retrieval",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "nearest_cluster_hit@3": "0.2",
                "context_recall_retention@10": "0.5",
            }])
            write(dense_path, [{
                "dataset": "emanual",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "recall@10": "0.3",
            }])
            write(soft_path, [{
                "dataset": "emanual",
                "scope": "heldout_test",
                "query_split": "test",
                "corpus_scope": "full",
                "recall@10_mean": "0.2",
            }])

            rows = summarize_manifold_diagnostics.build_tables(
                diagnostics_path,
                dense_path,
                soft_path,
                output_csv,
                output_md,
            )

            self.assertEqual(len(rows), 1)
            self.assertTrue(output_csv.exists())
            self.assertTrue(output_md.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
