# Task69.3 LoTTE Science/Search 100k Checkpoint

Updated: 2026-07-06

## Status

Complete for the 100k cross-domain checkpoint. Larger science/search scales and
additional LoTTE domains remain pending.

## Matched Retrieval Results

All rows use the 101,187-chunk corpus, 596 queries, full GT query coverage,
MiniLM embeddings, and top-10 evaluation.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.7886 | 0.6076 | 0.6016 | 0.5342 |
| Dense | 0.8926 | 0.7328 | 0.7357 | 0.6685 |
| Hybrid RRF | 0.8943 | 0.7223 | 0.7321 | 0.6559 |
| IntentRoute, no feedback | 0.9066 | 0.7453 | 0.7378 | 0.6734 |
| IntentRoute, trust weighted | 0.9077 | 0.7277 | 0.7429 | 0.6609 |

The no-feedback controller falls back to Dense for every query. Trust-weighted
feedback raises last-epoch route reward from 0.1314 to 0.8484, activates the
LinUCB-primary route on 30.08% of queries, and lowers the Dense invocation rate
from 1.0000 to 0.6992. Aggregate Hit@10 changes only slightly because Dense
fallback protects both variants. EvidenceRecall is mixed and must not be hidden.

## Five-Fold Context Budget

The cross-fitted evaluation reuses frozen Dense and trust-weighted IntentRoute
rankings. Four folds select the policy and every query is evaluated out of fold
once.

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 5/5 |
| Mean Hit@10 delta vs Dense | -0.11pp |
| Mean final-context token saving | 16.88% |
| Strict 1pp NI seeds | 0/3 |
| Mean EvidenceRecall@10 delta | -2.86pp |
| Independently calibrated Dense saving | 2.41% |

This supports a quality-efficiency trade-off for query-level sufficient
evidence. It does not establish strict non-inferiority or complete-evidence
preservation.

## Artifacts

- `results/task69_3_science_100k_bm25/`
- `results/task69_3_science_100k_hybrid/`
- `results/task69_3_science_100k_feedback_none/`
- `results/task69_3_science_100k_cross_fitted_calibration.*`

The trust-weighted route source is the existing Task39 science/search 100k
artifact. Embeddings and deterministic Dense/BM25 retrieval artifacts were
reused; final fold selection and paired statistics were recomputed.
