# Task69.3 LoTTE Science/Search 400k Checkpoint

Updated: 2026-07-12

## Status

The 400k core endpoint is complete on the nested 400,902-chunk LoTTE
science/search corpus. It uses the same 596 test queries, MiniLM backbone,
KMeans `K=32`, route seeds `13/17/19`, eight prequential epochs, and frozen
five-fold budget protocol as the 100k and 200k scale rows. The exact cached
score backend was validated against the legacy backend at 100k before this run.

The matched Dense, BM25, hybrid, trust-weighted, and no-feedback route outputs
are complete. The Task40-style feedback-recovery endpoint has also been run on
the frozen rankings, so this is a complete common-protocol scale-boundary row.

## Matched Retrieval Results

All rows use the 400,902-chunk corpus, 596 queries, full GT query coverage,
MiniLM embeddings, and top-10 evaluation.

| Method | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 0.7114 | 0.5241 | 0.5171 | 0.4512 |
| Dense | 0.8238 | 0.6469 | 0.6525 | 0.5856 |
| Hybrid RRF | 0.8305 | 0.6475 | 0.6464 | 0.5750 |
| IntentRoute, no feedback | 0.8484 | 0.6717 | 0.6561 | 0.5961 |
| IntentRoute, trust-weighted full | 0.8490 | 0.6745 | 0.6564 | 0.5982 |
| IntentRoute, trust-weighted gated | 0.8249 | 0.6065 | 0.6606 | 0.5624 |

The no-feedback control leaves the dense route active for every query, so its
full and gated outputs are identical. Trust-weighted feedback changes the gated
route: it reduces dense invocation to 0.7043 and source-candidate cost from
300.0 to 173.4 chunks, but its fixed-top-10 Hit@10 is 2.35 percentage points
below the no-feedback/dense-rescue result. This is a route-control boundary,
not a final-context token-saving claim.

## Five-Fold Context Budget

The cross-fitted evaluation reuses frozen Dense and trust-weighted gated-route
rankings. Four folds select the policy and every query is evaluated out of fold
once.

| Endpoint | Result |
|---|---:|
| Eligible IntentRoute folds | 1/5 |
| Mean Hit@10 delta vs Dense | -0.67pp |
| Mean final-context token saving | 3.15% |
| Strict 1pp NI seeds | 0/3 |
| Mean EvidenceRecall@10 delta | -1.12pp |
| Independently calibrated Dense saving | 0.00% |

Only one fold selects `token_budget_r0.88_m4`; that held-out fold loses 3.36
percentage points of Hit@10 while saving 15.76% context tokens. The other four
folds fall back to Dense top-10. Therefore the 400k row is a conservative
scale-boundary result: it does not support robust lossless compression or
strict non-inferiority at this scale.

## Feedback-Recovery Endpoint

The recovery analysis reuses the frozen cross-fitted rankings and the same
`r0.88_m4` action. Its token and hit accounting explicitly truncates Dense
artifact caches to the evaluated top-10, so a cached top-100 tail cannot inflate
the affected set or the token denominator.

- affected queries: 6, 3, and 5 for seeds 13, 17, and 19;
- same-query arm boosts recover 5, 2, and 4 respectively;
- all-query recovery restores Dense Hit@10 for seeds 13/17 and remains -0.17pp
  for seed 19, with 2.91-3.46% final-context token saving;
- calibration-to-test boosts operate on only 1-3 learned query arms per seed.

This closes the common-protocol recovery endpoint, but it is deliberately kept
as small-sample boundary evidence. It does not change the OOF conclusion that
science/search 400k is not robust lossless-compression support.

## Artifacts

- `results/task69_3_science_400k_dense/`
- `results/task69_3_science_400k_bm25/`
- `results/task69_3_science_400k_hybrid/`
- `results/task69_3_science_400k_linucb_cached_exact/`
- `results/task69_3_science_400k_feedback_none_cached_exact/`
- `results/task69_3_science_400k_cross_fitted_calibration.*`
- `results/task69_3_science_400k_feedback_recovery.*`

The reusable local inputs are the nested science scale store and exact static
score artifact under `data/scale_store/lotte_science_search/` and
`data/retrieval_artifacts/`; both remain Git ignored because they are local
regenerable caches.
