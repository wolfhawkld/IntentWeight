# Task78 CovidQA Canonical Rerun

Status: **PASS_CONCLUSIONS_STABLE_CANONICAL_READY**

The historical processed corpus and query records are unchanged. The canonical branch pins the MiniLM model revision, rebuilds embeddings on ROCm in an isolated cache, and runs every downstream retrieval, routing, budget, and feedback diagnostic from those fixed embeddings.

## Historical Versus Canonical

| Method | Seed | Historical Hit@10 | Canonical Hit@10 | Delta | ID members equal | Text members equal | McNemar p | 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | - | 0.4884 | 0.4884 | +0.00 pp | 1764/1765 | 1764/1765 | 1 | [+0.00, +0.00] pp |
| dense | - | 0.6095 | 0.6112 | +0.17 pp | 1181/1765 | 1765/1765 | 0.6636 | [-0.35, +0.70] pp |
| hybrid_rrf | - | 0.6037 | 0.6049 | +0.12 pp | 1211/1765 | 1635/1765 | 0.8238 | [-0.41, +0.64] pp |
| intentroute_trust | 13 | 0.6315 | 0.6327 | +0.12 pp | 504/1765 | 849/1765 | 0.9188 | [-0.98, +1.22] pp |
| intentroute_trust | 17 | 0.6286 | 0.6292 | +0.06 pp | 519/1765 | 864/1765 | 1 | [-1.04, +1.16] pp |
| intentroute_trust | 19 | 0.6298 | 0.6292 | -0.06 pp | 467/1765 | 784/1765 | 1 | [-1.22, +1.10] pp |
| intentroute_none | 13 | 0.6275 | 0.6304 | +0.29 pp | 974/1765 | 1676/1765 | 0.5224 | [-0.41, +0.98] pp |
| intentroute_none | 17 | 0.6292 | 0.6344 | +0.52 pp | 980/1765 | 1689/1765 | 0.1496 | [-0.12, +1.16] pp |
| intentroute_none | 19 | 0.6315 | 0.6350 | +0.35 pp | 995/1765 | 1681/1765 | 0.3616 | [-0.29, +0.98] pp |
| intentroute_crossfit | 13 | 0.6054 | 0.6089 | +0.35 pp | 262/1765 | 470/1765 | 0.6368 | [-0.81, +1.56] pp |
| intentroute_crossfit | 17 | 0.6066 | 0.6101 | +0.35 pp | 287/1765 | 473/1765 | 0.6241 | [-0.81, +1.51] pp |
| intentroute_crossfit | 19 | 0.6101 | 0.6083 | -0.17 pp | 264/1765 | 449/1765 | 0.8509 | [-1.33, +1.04] pp |

## Budgeted Frozen-Ranking Result

| Version | Eligible folds | Hit delta vs Dense | Token saving | Strict 1pp NI seeds |
|---|---:|---:|---:|---:|
| Historical | 4/5 | -0.21 pp | 8.34% | 0/3 |
| Canonical | 4/5 | -0.21 pp | 9.00% | 0/3 |

## Interpretation

- BM25 metrics remain exact; one non-GT ranking tie changes its top-10 membership. Embedding-dependent rankings move at duplicate-text boundaries and through downstream KMeans assignments.
- All 584 Dense member-set changes replace chunks with identical normalized text, and every changed candidate score span is at most 4.77e-7. ID-based metrics are retained as the official protocol; text-equivalent diagnostics identify the source of the instability without changing labels post hoc.
- A second ROCm encoding and cached-exact ranking run is byte-identical. CPU BLAS and the alternate direct Top-K path choose different IDs among these near-tied duplicate sentences, so exact handoff starts from the fixed canonical rankings and score cache.
- No paired Hit@10 comparison is significant at 0.05. The trust-weighted route rate and Dense invocation rate remain effectively unchanged.
- The cross-fitted quality delta is unchanged while the selected policies increase mean token saving. Strict non-inferiority remains unsupported, exactly as in the historical interpretation.
- Same-query feedback still recovers a subset of harmed queries with no regressions in that diagnostic. Calibration-to-test feedback remains mixed and is not promoted to production-feedback evidence.

The canonical branch should replace historical CovidQA point estimates as one internally coherent reproducible checkpoint. Historical artifacts remain archived for provenance and must not be mixed with canonical embeddings or rankings.
