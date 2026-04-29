# Retrieval Baseline Tables

## Evidence Retrieval Main Table

| dataset | method | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | recall@1 | recall@5 | recall@10 | mrr@10 | ndcg@10 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| emanual | BM25 | heldout_test | test | full | 130 | 2 | 130 | 1.0 | 0.0000 | 0.0615 | 0.1154 | 0.0244 | 0.0256 |  |
| emanual | Dense | heldout_test | test | full | 130 | 2 | 130 | 1.0 | 0.0000 | 0.0846 | 0.3231 | 0.0551 | 0.0526 | Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |
| emanual | Hybrid RRF | heldout_test | test | full | 130 | 2 | 130 | 1.0 | 0.0000 | 0.0769 | 0.1692 | 0.0366 | 0.0287 | Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |
| pubmedqa | BM25 | full | train | full | 1000 | 0 | 1000 | 1.0 | 0.6910 | 0.9730 | 0.9770 | 0.8273 | 0.6648 | GT is abstract context section-level, not strict answer-supporting sentence evidence. |
| pubmedqa | Dense | full | train | full | 1000 | 0 | 1000 | 1.0 | 0.7090 | 0.9870 | 0.9930 | 0.8468 | 0.7396 | GT is abstract context section-level, not strict answer-supporting sentence evidence. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |
| pubmedqa | Hybrid RRF | full | train | full | 1000 | 0 | 1000 | 1.0 | 0.7070 | 0.9830 | 0.9890 | 0.8443 | 0.7230 | GT is abstract context section-level, not strict answer-supporting sentence evidence. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |

## Intent Retrieval Proxy

| dataset | method | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | recall@1 | recall@5 | recall@10 | mrr@10 | ndcg@10 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | BM25 | heldout_test | test | full | 3080 | 0 | 3080 | 1.0 | 0.8019 | 0.9370 | 0.9698 | 0.8604 | 0.6762 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. |
| banking77 | Dense | heldout_test | test | full | 3080 | 0 | 3080 | 1.0 | 0.9205 | 0.9701 | 0.9805 | 0.9416 | 0.8797 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |
| banking77 | Hybrid RRF | heldout_test | test | full | 3080 | 0 | 3080 | 1.0 | 0.9136 | 0.9721 | 0.9851 | 0.9394 | 0.8504 | Intent retrieval proxy/domain routing; do not mix with evidence retrieval conclusions. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |

## Smoke / Sample Results

| dataset | method | scope | query_split | corpus_scope | num_queries | num_skipped_no_gt | num_queries_with_gt_in_corpus | gt_query_coverage | recall@1 | recall@5 | recall@10 | mrr@10 | ndcg@10 | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cuad | BM25 | smoke_only | test | gt_anchored_10000 | 79 | 21 | 79 | 1.0 | 0.0127 | 0.0253 | 0.0506 | 0.0232 | 0.0209 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. |
| cuad | Dense | smoke_only | test | gt_anchored_10000 | 79 | 21 | 79 | 1.0 | 0.0253 | 0.0380 | 0.0759 | 0.0334 | 0.0349 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |
| cuad | Hybrid RRF | smoke_only | test | gt_anchored_10000 | 79 | 21 | 79 | 1.0 | 0.0127 | 0.0506 | 0.0633 | 0.0254 | 0.0259 | Sampled query/corpus scope; use only with matching comparison group. CUAD smoke/sample result; not a full-corpus held-out result. Corpus sample is GT-anchored: selected query GT chunks plus sampled distractors. Dense encoder is all-MiniLM-L6-v2 CPU exact cosine, not BGE-large. |

## Notes

- Main evidence table excludes `smoke_only`, non-comparable, and intent proxy rows.
- CUAD is reported only as a smoke/sample result; sampled CUAD corpora must pass GT-in-corpus coverage.
- Dense rows use `sentence-transformers/all-MiniLM-L6-v2` CPU exact cosine unless noted otherwise.
