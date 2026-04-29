#!/usr/bin/env python3
"""Tests for retrieval experiment protocol guardrails."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "paper" / "experiments" / "scripts" / "experiment_guardrails.py"

spec = importlib.util.spec_from_file_location("experiment_guardrails", MODULE_PATH)
experiment_guardrails = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment_guardrails)


class ExperimentGuardrailsTests(unittest.TestCase):
    def test_query_split_filtering_happens_before_sampling(self):
        queries = [
            {"query_id": "q_train", "split": "train"},
            {"query_id": "q_test_1", "split": "test"},
            {"query_id": "q_test_2", "metadata": {"split": "test"}},
        ]

        selected = experiment_guardrails.apply_query_controls(queries, query_split="test", max_queries=1)

        self.assertEqual([query["query_id"] for query in selected], ["q_test_1"])
        self.assertEqual(experiment_guardrails.describe_query_split(selected), "test")

    def test_metadata_marks_cuad_sample_as_smoke_only(self):
        queries = [{"query_id": "q1", "split": "train", "ground_truth_chunk_ids": ["c1"]}]
        corpus = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]

        metadata = experiment_guardrails.build_run_metadata(
            dataset="cuad",
            queries=queries,
            all_queries=queries,
            corpus=corpus[:1],
            all_corpus=corpus,
            max_queries=1,
            max_corpus=1,
            requested_query_split="train",
            top_k=10,
            ks=(1, 5, 10),
        )

        self.assertEqual(metadata["task_type"], "evidence_retrieval")
        self.assertEqual(metadata["scope"], "smoke_only")
        self.assertEqual(metadata["query_split"], "train")
        self.assertEqual(metadata["corpus_scope"], "first_1")
        self.assertEqual(metadata["gt_corpus_guardrail"], "pass")
        self.assertIn("CUAD smoke/sample", metadata["notes"])

    def test_gt_anchored_corpus_sampling_keeps_selected_query_gt(self):
        corpus = [
            {"chunk_id": "d1"},
            {"chunk_id": "d2"},
            {"chunk_id": "gt_b"},
            {"chunk_id": "d3"},
            {"chunk_id": "gt_a"},
        ]
        queries = [
            {"query_id": "q1", "ground_truth_chunk_ids": ["gt_a"]},
            {"query_id": "q2", "ground_truth_chunk_ids": ["gt_b"]},
        ]

        selected = experiment_guardrails.apply_corpus_controls(
            corpus,
            max_corpus=4,
            queries=queries,
            corpus_sampling="gt_anchored",
            random_seed=7,
        )
        selected_ids = {chunk["chunk_id"] for chunk in selected}
        coverage = experiment_guardrails.gt_corpus_coverage(queries, selected)

        self.assertIn("gt_a", selected_ids)
        self.assertIn("gt_b", selected_ids)
        self.assertEqual(len(selected), 4)
        self.assertEqual(coverage["num_queries_with_gt_in_corpus"], 2)
        self.assertEqual(coverage["gt_corpus_guardrail"], "pass")

    def test_gt_corpus_guardrail_fails_when_selected_corpus_excludes_gt(self):
        queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["gt"]}]
        corpus = [{"chunk_id": "d1"}, {"chunk_id": "d2"}]

        with self.assertRaisesRegex(ValueError, "GT corpus coverage guardrail failed"):
            experiment_guardrails.assert_gt_corpus_coverage(queries, corpus)

    def test_comparison_guardrails_require_matching_method_triple(self):
        shared = {
            "dataset": "emanual",
            "query_scope": "split_test",
            "corpus_scope": "full",
            "top_k": 10,
            "metric_ks": "1,5,10",
            "scope": "heldout_test",
            "query_split": "test",
        }
        rows = [
            {**shared, "method": "bm25", "comparable_group": experiment_guardrails.comparable_group(shared)},
            {**shared, "method": "dense", "comparable_group": experiment_guardrails.comparable_group(shared)},
            {**shared, "method": "hybrid_rrf", "comparable_group": experiment_guardrails.comparable_group(shared)},
            {
                **shared,
                "method": "dense",
                "corpus_scope": "first_100",
                "comparable_group": "different",
            },
        ]

        guarded = experiment_guardrails.apply_comparison_guardrails(rows)

        comparable = [row for row in guarded if row["comparable_group"] == experiment_guardrails.comparable_group(shared)]
        self.assertTrue(all(row["is_comparable"] == "true" for row in comparable))
        non_comparable = [row for row in guarded if row["comparable_group"] == "different"]
        self.assertEqual(non_comparable[0]["is_comparable"], "false")
        self.assertIn("missing", non_comparable[0]["notes"])

    def test_build_comparison_enriches_legacy_metrics_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            data_dir = tmpdir / "processed"
            results_dir = tmpdir / "results"
            data_dir.mkdir()
            results_dir.mkdir()
            queries = [
                {"query_id": "q_train", "split": "train", "ground_truth_chunk_ids": ["c1"]},
                {"query_id": "q_test", "split": "test", "ground_truth_chunk_ids": ["c2"]},
            ]
            (data_dir / "emanual_queries.json").write_text(json.dumps(queries), encoding="utf-8")
            for method in ("bm25", "dense", "hybrid_rrf"):
                metrics = {
                    "dataset": "emanual",
                    "method": method,
                    "model": "fake-model" if method != "bm25" else "",
                    "top_k": 10,
                    "ks": [1, 5, 10],
                    "num_queries": 2,
                    "num_corpus_chunks": 3,
                    "num_total_corpus_chunks": 3,
                    "num_total_queries": 2,
                    "recall@1": 1.0,
                }
                prefix = "hybrid" if method == "hybrid_rrf" else method
                (results_dir / f"{prefix}_emanual_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

            output_path = results_dir / "comparison.csv"
            rows = experiment_guardrails.build_comparison(results_dir, data_dir, output_path)

            self.assertEqual(len(rows), 3)
            self.assertTrue(output_path.exists())
            with output_path.open("r", encoding="utf-8", newline="") as f:
                csv_rows = list(csv.DictReader(f))
            self.assertEqual({row["query_split"] for row in csv_rows}, {"mixed"})
            self.assertEqual({row["is_comparable"] for row in csv_rows}, {"true"})
            self.assertTrue(all(row["task_type"] == "evidence_retrieval" for row in csv_rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
