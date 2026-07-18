# Task69.5 CovidQA-RAG Native-Full Checkpoint

Updated: 2026-07-18

## Status

Complete for the provenance-pinned native-full CovidQA-RAG common-protocol
checkpoint. This row
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
| Dense | 0.6112 | 0.2601 | 0.3333 | 0.2253 |
| Hybrid RRF | 0.6049 | 0.2586 | 0.3322 | 0.2248 |
| IntentRoute, no feedback | 0.6333 | 0.2714 | 0.3365 | 0.2300 |
| IntentRoute, trust weighted | 0.6304 | 0.2664 | 0.3418 | 0.2304 |

Trust-weighted feedback activates the LinUCB-primary route on 12.43% of
interactions and lowers the Dense invocation rate to 0.8757. The no-feedback
control keeps Dense fallback active for every interaction, with a Dense
invocation rate of 1.0000.

## Five-Fold Context Budget

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 4/5 |
| Mean Hit@10 delta vs Dense | -0.21pp |
| Mean final-context token saving | 9.00% |
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

## Canonical Refresh And Numerical Boundary

The original Task69 embedding cache was unavailable. The replacement branch
pins MiniLM revision `c9745ed1d9f207416be6d2e6f8de32d1f16199bf`, rebuilds
embeddings on the RX 9070 XT ROCm path, and regenerates every downstream
CovidQA result in one isolated generation. A second ROCm run reproduces the
embeddings and cached-exact Dense rankings byte for byte.

Historical-versus-canonical paired Hit@10 changes are non-significant. All 584
Dense top-10 member-set changes replace chunk IDs with identical normalized
text, with canonical score spans no larger than `4.77e-7`. The paper retains
the official chunk-ID metric rather than relabeling after inspection. Exact
cross-machine reproduction starts from the fixed canonical rankings and score
cache because CPU BLAS can select different IDs among these tied duplicate
sentences. See `results/task78_covidqa_canonical/comparison.md`.

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
- `results/task78_covidqa_canonical/dense/`
- `results/task78_covidqa_canonical/bm25/`
- `results/task78_covidqa_canonical/hybrid/`
- `results/task78_covidqa_canonical/linucb_trust/`
- `results/task78_covidqa_canonical/linucb_none/`
- `results/task78_covidqa_canonical/cross_fitted_calibration.*`
- `results/task78_covidqa_canonical/feedback_recovery.*`
- `results/task78_covidqa_canonical/comparison.{json,csv,md}`
