# Task65.2 Factorial Safe-Compression Attribution Summary

Task65.2 is complete.

## Protocol

The experiment uses LoTTE technology/search 100k, MiniLM, seeds `13,17,19`,
the existing 179-query calibration / 417-query frozen-test split, and the same
token-budget grid for every condition. All final compression policies operate
on exactly the same dense top-10 candidate ranking. Route experiments provide
only a query-level selector score and cannot change the evidence pool.

The controlled conditions are:

- geometry + feedback: contextual LinUCB confidence over geometry-derived arms;
- geometry + no feedback: static nearest-centroid similarity;
- random partition + feedback: the same contextual LinUCB estimator after a
  deterministic permutation of cluster membership;
- random partition + no feedback: static nearest-centroid similarity on that
  permuted partition;
- dense budget-only: the same compression action applied to every query.

The audit reports quality-constrained and matched-saving frontiers, fixed-action
AUROC/AUPRC, Brier score, ECE, risk-coverage curves, and query-level paired
bootstrap intervals. The fixed failure-prediction action is
`token_budget_r0.85_m4`.

## Main Results

The fixed action is safe for `97.8%` of dense-hit test queries, so AUPRC and
calibration errors are dominated by class imbalance. Mean AUROC is `0.434` for
geometry + feedback, `0.201` for geometry without feedback, `0.573` for random
partition + feedback, `0.381` for random partition without feedback, and
`0.500` for budget-only. The per-seed intervals are wide; the experiment does
not establish a safe-compression discrimination advantage for geometry or
feedback.

At the approximately `10%` token-saving target:

| Condition | Test Hit delta | Test token saving |
|---|---:|---:|
| Geometry + feedback | -0.96 pp | 9.51% |
| Geometry + no feedback | -2.48 pp | 10.14% |
| Random partition + feedback | -1.04 pp | 10.59% |
| Random partition + no feedback | -1.04 pp | 8.98% |
| Dense budget-only | -0.96 pp | 10.05% |

Geometry + feedback differs from random partition + feedback by only
`+0.08 pp` at this target, and all three seed-level bootstrap intervals include
zero. Geometry + feedback exceeds geometry without feedback by `+1.52 pp`, but
only one of three seed-level intervals excludes zero. The feedback effect under
the random partition is `0.00 pp`. No condition passes strict zero-margin
query-bootstrap non-inferiority against dense at the calibration-selected
quality operating points.

## Route Versus Compression Boundary

The negative compression-attribution result does not erase the route-control
result. Static geometry reaches route reward about `0.856`, whereas the
random-partition static control reaches about `0.267`. Feedback raises the
random-partition learned route reward to about `0.564`, but this improvement
does not translate into superior identification of dense queries that tolerate
token truncation.

The supported interpretation is therefore:

1. geometry and feedback affect route construction and route quality;
2. they are not demonstrated direct predictors of per-query safe compression;
3. final context saving comes from the selected evidence pool plus a separately
   calibrated length budget.
