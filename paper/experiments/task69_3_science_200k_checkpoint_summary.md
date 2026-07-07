# Task69.3 LoTTE Science/Search 200k Checkpoint

Updated: 2026-07-07

## Status

Complete for the 200k cross-domain scale checkpoint. The run extends the same
LoTTE science/search canonical scale-store used by the 100k checkpoint and
therefore reuses the first 101,187 canonical corpus rows while encoding 99,911
new rows. Larger science/search scales and additional LoTTE domains remain
pending.

## Matched Retrieval Results

All rows use the 201,098-chunk corpus, 596 queries, full GT query coverage,
MiniLM embeddings, and top-10 evaluation.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.7550 | 0.5722 | 0.5631 | 0.4957 |
| Dense | 0.8574 | 0.6908 | 0.6995 | 0.6308 |
| Hybrid RRF | 0.8708 | 0.6904 | 0.6946 | 0.6195 |
| IntentRoute, no feedback | 0.8842 | 0.7118 | 0.7034 | 0.6400 |
| IntentRoute, trust weighted | 0.8680 | 0.6725 | 0.7075 | 0.6200 |

The no-feedback controller keeps Dense fallback active for every query
(`dense_rate=1.0000`, `primary_rate=0.0000`) and therefore does not produce an
efficiency endpoint. Trust-weighted feedback activates the LinUCB-primary route
on 38.06% of queries and lowers the Dense invocation rate to 0.6194. The full
multi-route upper reference reaches Hit@10 0.8853, but the cost-aware gated
route is the paper-facing efficiency endpoint.

## Five-Fold Context Budget

The cross-fitted evaluation reuses frozen Dense and trust-weighted IntentRoute
rankings. Four folds select the policy and every query is evaluated out of fold
once.

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 4/5 |
| Mean Hit@10 delta vs Dense | -0.67pp |
| Mean final-context token saving | 10.75% |
| Strict 1pp NI seeds | 0/3 |
| Mean EvidenceRecall@10 delta | -2.97pp |
| Independently calibrated Dense saving | 0.00% |

This row strengthens the cross-domain scale evidence for final-context token
reduction under a modest query-level Hit@10 trade-off. It does not establish
strict non-inferiority or complete-evidence preservation.

## Artifacts

- `results/task69_3_science_200k_dense/`
- `results/task69_3_science_200k_bm25/`
- `results/task69_3_science_200k_hybrid/`
- `results/task69_3_science_200k_linucb/`
- `results/task69_3_science_200k_feedback_none/`
- `results/task69_3_science_200k_cross_fitted_calibration.*`

The ignored intermediate data artifacts are regenerated from local LoTTE Arrow
cache and the shared scale-store path:

- `data/processed/lotte_science_search_200k_*.json`
- `data/scale_store/lotte_science_search/`
- `data/retrieval_artifacts/lotte_science_search_200k*`
