# Task65.6 Cross-Scale Cross-Fitted Calibration Summary

Task65.6 is complete.

## Protocol

The follow-up reuses frozen Task37 Dense and IntentRoute rankings at 100k,
200k, 400k, and 638k. The same 596 canonical LoTTE source queries are assigned
to the same five balanced, disjoint folds at every scale. For each outer fold,
the remaining four folds select a final-context policy from the original
Task38 grid under the unchanged zero-observed-Hit-drop rule. Dense and
IntentRoute select independently. If no policy is eligible, the declared
action is Dense top-10 fallback.

Each query is evaluated out of fold exactly once. The audit reports paired
bootstrap intervals, exact McNemar tests, final-context token saving, and
one-percentage-point non-inferiority separately for seeds 13, 17, and 19.

## Result

| Scale | Eligible folds | OOF Hit delta | Context-token saving | Strict NI seeds | IntentRoute policies | Dense compressed policies |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 2/5 | -1.06pp | 4.16% | 0/3 | 2 | 0 |
| 200k | 5/5 | +1.40pp | 16.07% | 2/3 | 1 | 0 |
| 400k | 5/5 | +0.00pp | 14.50% | 0/3 | 5 | 0 |
| 638k | 5/5 | +0.28pp | 15.23% | 0/3 | 3 | 0 |

Under the strict zero-drop calibration gate, independently calibrated Dense
cannot select a nonzero-compression policy in any fold at any scale and
therefore uses Dense top-10 fallback. IntentRoute selects a compressed policy
in all 200k, 400k, and 638k folds. This indicates that route-level quality can
create calibration headroom for final-context reduction that prefix-only Dense
truncation does not provide under the same rule.

The 400k follow-up closes the missing normalized calibration check: all five
folds are eligible, the out-of-fold mean Hit delta is effectively zero, and
mean final-context saving is 14.50%. However, the five folds select five
different policies, fold-level Hit deltas range from -3.64pp to +4.44pp, and
strict seed-level non-inferiority remains 0/3. The correct interpretation is a
positive average cross-fitted trade-off with material policy and partition
sensitivity, not a stable or universally non-inferior 400k operating point.

The 100k result is also informative: three folds fall back to Dense and the
two compressed folds lose enough held-out Hit to produce a -1.06pp aggregate
delta. This reinforces the existing claim that calibration behavior is
scale- and partition-dependent.

## Artifact Validation

- 20 fold selections and 16 paired comparison rows are present.
- Each scale contains 596 out-of-fold rankings per IntentRoute seed and 596
  independently calibrated Dense rankings.
- Canonical fold assignments are identical across all four scales.
- SHA-256 hashes for every frozen ranking and query input were verified.
- The experiment reuses intermediate rankings, not prior calibration or test
  statistics.

## Claim Boundary

This is a post-hoc robustness follow-up and does not erase the original 400k
calibration failure. It strengthens the evidence that calibrated IntentRoute
can trade final-context tokens for evidence quality at 400k, while explicitly
retaining the lack of strict non-inferiority and the observed policy
instability.
