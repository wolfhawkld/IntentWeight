# Task69.4 eManual Deduplicated Native-Full Checkpoint

Updated: 2026-07-07

## Status

Complete for the corrected eManual native-full common-protocol checkpoint. The
row uses the text-deduplicated corpus introduced in the eManual failure
analysis: 1,729 unique text chunks and 132 test queries, of which 130 have
usable ground-truth evidence.

## Matched Retrieval Results

All rows use MiniLM embeddings and top-10 evaluation. Metrics skip the two
queries without usable ground-truth evidence.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.7308 | 0.3336 | 0.4218 | 0.3000 |
| Dense | 0.8615 | 0.4178 | 0.5736 | 0.3807 |
| Hybrid RRF | 0.8615 | 0.4314 | 0.5903 | 0.3956 |
| IntentRoute, no feedback | 0.8769 | 0.4248 | 0.5771 | 0.3844 |
| IntentRoute, trust weighted | 0.8846 | 0.4204 | 0.6258 | 0.4004 |

The no-feedback controller keeps Dense fallback active for every query
(`dense_rate=1.0000`, `primary_rate=0.0000`). Trust-weighted feedback activates
the LinUCB-primary route on 43.18% of queries and lowers the Dense invocation
rate to 0.5682.

## Five-Fold Context Budget

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 5/5 |
| Mean Hit@10 delta vs Dense | -0.26pp |
| Mean final-context token saving | 16.20% |
| Strict 1pp NI seeds | 0/3 |
| Mean EvidenceRecall@10 delta | -3.07pp |
| Independently calibrated Dense saving | 0.00% |

This row supports a corrected-boundary trade-off result: after duplicate text is
collapsed, the route policy can reduce final-context tokens with only a modest
query-level Hit@10 change. It does not establish complete evidence preservation.

## Feedback Recovery Endpoint

The Task40 recovery diagnostic was run on the cross-fitted budgeted rankings.
Same-query retry can recover a subset of affected cases, while calibration-to-
test recovery remains mixed. This is mechanism evidence only and should not be
used as the headline token-saving number.

## Artifacts

- `scripts/task69_build_emanual_deduplicated.py`
- `results/task69_4_emanual_dedup_dense/`
- `results/task69_4_emanual_dedup_bm25/`
- `results/task69_4_emanual_dedup_hybrid/`
- `results/task69_4_emanual_dedup_linucb/`
- `results/task69_4_emanual_dedup_feedback_none/`
- `results/task69_4_emanual_dedup_cross_fitted_calibration.*`
- `results/task69_4_emanual_dedup_feedback_recovery.*`
