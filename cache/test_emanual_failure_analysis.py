import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "paper" / "experiments" / "scripts" / "emanual_failure_analysis.py"
spec = importlib.util.spec_from_file_location("emanual_failure_analysis", SCRIPT_PATH)
emanual_failure_analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emanual_failure_analysis)


class TestEManualFailureAnalysis(unittest.TestCase):
    def test_text_equivalent_metrics_credit_duplicate_text(self):
        corpus = [
            {"chunk_id": "c1", "text": "Open the menu.", "metadata": {"record_id": "r1"}},
            {"chunk_id": "c2", "text": "  open   the MENU. ", "metadata": {"record_id": "r2"}},
            {"chunk_id": "c3", "text": "Close the menu.", "metadata": {"record_id": "r3"}},
        ]
        queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["c1"]}]
        chunk_by_id = {chunk["chunk_id"]: chunk for chunk in corpus}
        rankings = {"q1": ["c2", "c3"]}

        strict = emanual_failure_analysis.retrieval_metrics.evaluate_rankings(queries, rankings, ks=(1, 2))
        text_equiv = emanual_failure_analysis.evaluate_text_equivalent_rankings(
            queries,
            rankings,
            chunk_by_id,
            ks=(1, 2),
        )

        self.assertEqual(strict["recall@1"], 0.0)
        self.assertEqual(text_equiv["recall@1"], 1.0)
        self.assertEqual(text_equiv["mrr@1"], 1.0)

    def test_deduplicate_corpus_remaps_ground_truth_to_text_id(self):
        corpus = [
            {"chunk_id": "c1", "text": "Power on the device.", "metadata": {"record_id": "r1"}},
            {"chunk_id": "c2", "text": "power on the device.", "metadata": {"record_id": "r2"}},
            {"chunk_id": "c3", "text": "Pair the remote.", "metadata": {"record_id": "r3"}},
        ]
        queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["c1", "c2"]}]

        dedup_corpus, dedup_queries, mapping = emanual_failure_analysis.deduplicate_corpus_and_queries(corpus, queries)

        self.assertEqual(len(dedup_corpus), 2)
        self.assertEqual(mapping["c1"], mapping["c2"])
        self.assertEqual(len(dedup_queries[0]["ground_truth_chunk_ids"]), 1)
        duplicate_counts = {chunk["chunk_id"]: chunk["metadata"]["duplicate_count"] for chunk in dedup_corpus}
        self.assertEqual(duplicate_counts[mapping["c1"]], 2)

    def test_load_seed_nested_rankings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rankings.json"
            path.write_text(json.dumps({"13": {"q1": ["c1"]}, "17": {"q1": ["c2"]}}), encoding="utf-8")

            rankings = emanual_failure_analysis.load_ranking_sets(path)

        self.assertEqual(set(rankings), {"13", "17"})
        self.assertEqual(rankings["13"]["q1"], ["c1"])

    def test_duplicate_text_stats_reports_gt_duplicate_counts(self):
        corpus = [
            {"chunk_id": "c1", "text": "A", "metadata": {"record_id": "r1"}},
            {"chunk_id": "c2", "text": "A", "metadata": {"record_id": "r2"}},
            {"chunk_id": "c3", "text": "B", "metadata": {"record_id": "r2"}},
        ]
        queries = [{"query_id": "q1", "ground_truth_chunk_ids": ["c1"]}]

        stats = emanual_failure_analysis.duplicate_text_stats(corpus, queries, random_neighbor_k=1)

        self.assertEqual(stats["num_unique_texts"], 2)
        self.assertEqual(stats["gt_refs_with_duplicate_text"], 1)
        self.assertEqual(stats["gt_ref_duplicate_count_mean"], 2.0)


if __name__ == "__main__":
    unittest.main()
