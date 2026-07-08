# Task69.8 Mechanism And Boundary Summary

This CPU-only summary reads existing artifacts for rows that are useful
mechanism or boundary evidence, but are not pooled with the common
evidence-retrieval matrix.

## Main Summary

| Dataset | Role | Dense Hit@10 | Trust Hit@10 | Delta pp | No-feedback Hit@10 | Delta vs no-feedback pp | Last cluster hit | Cluster gain pp | Last true reward | Reward gain | NearestClusterHit@3 | Caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Banking77 | intent-routing mechanism | 0.9805 | 0.9844 | +0.39 | 0.9855 | -0.11 | 0.9983 | +55.93 | 0.9805 | +0.8145 | 0.9968 | intent proxy, not evidence retrieval |
| CUAD GT-anchored | sparse-GT boundary | 0.0759 | 0.0886 | +1.27 | 0.0675 | +2.11 | 0.2900 | +4.67 | 0.0233 | +0.0100 | 0.6076 | GT-anchored 10k sample; 79 evaluated queries |

## Static Baselines

| Dataset | Method | Hit@10 | MRR@10 | nDCG@10 |
|---|---|---|---|---|
| Banking77 | BM25 | 0.9698 | 0.8604 | 0.6762 |
| Banking77 | Dense | 0.9805 | 0.9416 | 0.8797 |
| Banking77 | Hybrid RRF | 0.9851 | 0.9394 | 0.8504 |
| CUAD GT-anchored | BM25 | 0.0506 | 0.0232 | 0.0209 |
| CUAD GT-anchored | Dense | 0.0759 | 0.0334 | 0.0349 |
| CUAD GT-anchored | Hybrid RRF | 0.0633 | 0.0254 | 0.0259 |

## Interpretation

- These rows are intentionally not averaged: Banking77 and CUAD have incompatible tasks, label semantics, and evaluation scopes.
- Banking77 supports route-learning and feedback behavior under an intent-routing proxy. The trust-weighted route has much higher last-epoch cluster hit and true reward than no-feedback, but fused Hit@10 is near ceiling and does not dominate no-feedback or hybrid retrieval.
- CUAD remains a sparse-GT, GT-anchored boundary sample. Its low absolute scores and small evaluated-query count prevent pooling with LoTTE/PubMedQA/CovidQA/eManual.
- The relevant paper-facing claim is mechanism and boundary support, not universal quality-efficiency replication.

## Traceability

- Banking77 dense: `paper/experiments/results/dense_banking77_metrics.json`
- Banking77 trust/feedback: `paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json`
- Banking77 geometry: `paper/experiments/results/manifold_diagnostics_banking77.json`
- CUAD GT-anchored dense: `paper/experiments/results/dense_cuad_metrics.json`
- CUAD GT-anchored trust/feedback: `paper/experiments/results/linucb_trust_cuad_prequential_metrics.json`
- CUAD GT-anchored geometry: `paper/experiments/results/manifold_diagnostics_cuad.json`
