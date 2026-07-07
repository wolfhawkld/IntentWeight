# Task69.4 PubMedQA Native-Full Checkpoint

Updated: 2026-07-07

## Status

Complete for the native-full PubMedQA common-protocol checkpoint. This is a
small non-LoTTE evidence-retrieval transfer row, not a large-scale LoTTE row.
The run uses the 4,348-chunk native corpus and all 1,000 queries.

## Matched Retrieval Results

All rows use MiniLM embeddings and top-10 evaluation.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.9770 | 0.7152 | 0.8273 | 0.6648 |
| Dense | 0.9930 | 0.8138 | 0.8468 | 0.7396 |
| Hybrid RRF | 0.9890 | 0.7924 | 0.8443 | 0.7230 |
| IntentRoute, no feedback | 0.9937 | 0.8138 | 0.8468 | 0.7398 |
| IntentRoute, trust weighted | 0.9917 | 0.7788 | 0.8467 | 0.7174 |

The no-feedback controller keeps Dense fallback active for every query
(`dense_rate=1.0000`, `primary_rate=0.0000`). Trust-weighted feedback activates
the LinUCB-primary route on 54.48% of queries and lowers the Dense invocation
rate to 0.4552, but this does not translate into a cross-fitted context-budget
gain because Dense is already near saturation on PubMedQA.

## Five-Fold Context Budget

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 0/5 |
| Mean Hit@10 delta vs Dense | +0.00pp |
| Mean final-context token saving | 0.00% |
| Strict 1pp NI seeds | 3/3 |
| Mean EvidenceRecall@10 delta | +0.00pp |
| Independently calibrated Dense saving | 0.00% |

This is a safety-preserving transfer row. Under the frozen selection rule, all
folds fall back to Dense top-10, so the method does not force compression where
the calibration evidence does not support it.

## Feedback Recovery Endpoint

The recovery endpoint is evaluated as not applicable for PubMedQA under the
five-fold common protocol: no fold selects a compressed IntentRoute budget, so
there is no budget-induced harmed-query set to recover. This is recorded as a
valid no-op recovery endpoint rather than as positive recovery evidence.

## Artifacts

- `results/task69_4_pubmedqa_dense/`
- `results/task69_4_pubmedqa_bm25/`
- `results/task69_4_pubmedqa_hybrid/`
- `results/task69_4_pubmedqa_linucb/`
- `results/task69_4_pubmedqa_feedback_none/`
- `results/task69_4_pubmedqa_cross_fitted_calibration.*`
- `results/task69_4_pubmedqa_feedback_recovery_not_applicable.*`
