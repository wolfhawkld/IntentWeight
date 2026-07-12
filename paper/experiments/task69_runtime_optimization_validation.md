# Task69 Runtime Optimization Validation

Date: 2026-07-11

## Purpose

Validate that the exact cached-score retrieval backend accelerates Task69
routing without changing its deterministic retrieval, routing, feedback, or
reported evaluation results.

## Protocol

- Dataset: LoTTE technology/search 100k held-out test split.
- Corpus: 101,311 chunks; queries: 596; ground-truth coverage: 100%.
- Model: `sentence-transformers/all-MiniLM-L6-v2` on CPU for the routing
  phase. Embedding construction is not part of this timing comparison.
- Seeds: `13`, `17`, `19`; epochs: 8.
- Routing modes: `full_multi_route`, `gated_cost_aware`.
- Feedback: `trust_weighted` and `none`; reward attribution: `final_fused`.
- Candidate depths: dense 100, BM25 100, cluster 100; final context top-k 10.
- Comparison: legacy `on_demand` cluster retrieval versus
  `cached_exact_scores`.

The cached engine stores deterministic static query-to-corpus float32 score
rows locally, selects the same arm rows, and applies the legacy candidate
union, `argpartition`, and score/index tie-break ranking logic unchanged.

## Equivalence Result

For each feedback setting, both engines completed all 6 planned runs
(2 routing modes x 3 seeds).

- Final per-query rankings were exactly equal for every routing mode and seed.
- After recursively excluding runtime/backend artifact metadata, all metrics,
  per-seed metrics, epoch metrics, route counts, costs, confidences, and
  retrieval metrics were exactly equal.
- No paper-facing result changed. This is an execution optimization only.

## Runtime Result

The elapsed time is the wall-clock value recorded after both routing modes
completed under each engine and feedback setting. The cached timings use an
already materialized static score artifact; score-cache construction is a
separate one-time setup cost for a new corpus scale.

| Feedback | Legacy `on_demand` | `cached_exact_scores` | Relative speed |
|---|---:|---:|---:|
| `trust_weighted` | 461.806 s | 133.777 s | 3.452x |
| `none` | 1022.613 s | 95.128 s | 10.750x |

The cached engine therefore reduced the full 100k trust-weighted validation
runtime by 71.0% and the no-feedback validation runtime by 90.7%, while
preserving each result exactly. The larger no-feedback difference occurs
because that configuration still computes legacy cluster candidates before its
dense fallback; the exact cache removes this redundant repeated embedding
scoring.

## Scope And Next Run

This validation covers both configurations pending for the 400k Task69.3
science/search run. The 100k exact-equivalence gate is complete for the
trust-weighted and no-feedback conditions. No optimized 400k routing job has
been launched yet.

The 400k exact score cache is local and Git ignored. It is approximately 1 GiB
and will be generated once before the next optimized 400k route run.
