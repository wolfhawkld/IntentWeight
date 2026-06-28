# Task65.5 Calibration-Split Sensitivity Summary

Task65.5 is complete.

## Protocol

The experiment reuses frozen Task37 Dense and IntentRoute rankings at 100k,
200k, 400k, and 638k. For each scale, it evaluates 20 deterministic 30/70
calibration/test partitions, including the original Task38 split. Every split
uses the original zero observed calibration-drop selection rule and the same
budget ratios/minimum-prefix grid. The 20 partitions overlap and are split
sensitivity diagnostics, not additional LinUCB seeds or independent samples.

## Result

| Scale | Eligible splits | Mean test Hit delta | Test Hit range | Mean saving | Test within 1pp |
|---|---:|---:|---:|---:|---:|
| 100k | 12/20 | -0.45pp | [-2.00, +0.72]pp | 10.64% | 70% |
| 200k | 19/20 | +1.53pp | [+0.56, +3.52]pp | 15.25% | 100% |
| 400k | 16/20 | +0.45pp | [-2.08, +2.80]pp | 12.47% | 85% |
| 638k | 19/20 | +0.44pp | [-0.88, +2.24]pp | 14.96% | 100% |

The original split is exactly reproduced. The selected policy is especially
stable at 200k (`r0.85/m4` in 18/20 splits) and 638k (`r0.85/m4` in 14/20).
At 100k, the modal policy is the conservative `r0.95/m4`, but it appears in
only 10/20 splits and more aggressive selections can lose up to `2.00pp` on
their complementary test partitions. The 400k policy varies across eight
actions and retains mixed test behavior.

## Boundary

The audit strengthens the 200k and 638k scale results, but it does not support
split-invariant calibration behavior at 100k or 400k. The original split
remains a valid pre-specified frozen evaluation; the sensitivity audit requires
the paper to describe 100k as conservative but split-sensitive and to retain
400k as diagnostic. Repeated or nested calibration is future work, not a claim
established by overlapping split diagnostics.
