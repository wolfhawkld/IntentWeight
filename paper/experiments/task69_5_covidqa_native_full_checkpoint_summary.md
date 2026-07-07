# Task69.5 CovidQA-RAG Native-Full Checkpoint

Updated: 2026-07-07

## Status

Complete for the native-full CovidQA-RAG common-protocol checkpoint. This row
was added as the biomedical discriminative supplement to PubMedQA: unlike
PubMedQA, Dense is not near ceiling, so the dataset can expose retrieval and
budget-control differences.

The processed RAGBench corpus contains 32,392 sentence chunks and 1,765 queries.
Evaluation skips 39 queries without usable ground-truth evidence, leaving 1,726
evaluated queries.

## Matched Retrieval Results

All rows use MiniLM embeddings and top-10 evaluation.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.4884 | 0.2037 | 0.2702 | 0.1789 |
| Dense | 0.6095 | 0.2598 | 0.3327 | 0.2259 |
| Hybrid RRF | 0.6037 | 0.2586 | 0.3312 | 0.2256 |
| IntentRoute, no feedback | 0.6294 | 0.2696 | 0.3358 | 0.2302 |
| IntentRoute, trust weighted | 0.6300 | 0.2677 | 0.3414 | 0.2320 |

Trust-weighted feedback activates the LinUCB-primary route on 12.41% of
interactions and lowers the Dense invocation rate to 0.8759. The no-feedback
control keeps Dense fallback active for every interaction, with a Dense
invocation rate of 1.0000.

## Five-Fold Context Budget

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 4/5 |
| Mean Hit@10 delta vs Dense | -0.21pp |
| Mean final-context token saving | 8.34% |
| Strict 1pp NI seeds | 0/3 |
| Mean EvidenceRecall@10 delta | -0.49pp |
| Independently calibrated Dense saving | 0.00% |

This row provides a more discriminative biomedical transfer result than
PubMedQA: the selector can reduce final-context tokens while preserving mean
query-level Hit@10 within a small negative delta. It does not satisfy strict
non-inferiority under the 1pp CI rule, so it should be reported as quality-
efficiency trade-off evidence rather than a guaranteed non-inferior result.

## Feedback Recovery Diagnostic

The Task40 recovery diagnostic was run on the cross-fitted budgeted rankings
using `r0.95_m4` as the representative retry budget. Same-query corrective
feedback recovers a subset of budget-induced harmed cases. Calibration-to-test
generalization is mixed, which matches the existing feedback framing: simulated
feedback is mechanism evidence for adaptive correction, not production user
behavior validation.

## Implementation Note

The cost-aware LinUCB runner now writes per-routing-mode/per-seed checkpoints.
This was required for CPU reliability on CovidQA: each seed is saved as soon as
it finishes, and reruns reuse checkpoints only when the parameter signature
matches.

## Artifacts

- `data/raw/covidqa_train.parquet`
- `data/raw/covidqa_validation.parquet`
- `data/raw/covidqa_test.parquet`
- `data/processed/covidqa_corpus.json`
- `data/processed/covidqa_queries.json`
- `results/task69_5_covidqa_dense/`
- `results/task69_5_covidqa_bm25/`
- `results/task69_5_covidqa_hybrid/`
- `results/task69_5_covidqa_linucb/`
- `results/task69_5_covidqa_feedback_none/`
- `results/task69_5_covidqa_cross_fitted_calibration.*`
- `results/task69_5_covidqa_feedback_recovery.*`
