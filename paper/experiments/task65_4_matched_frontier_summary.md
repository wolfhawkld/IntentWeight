# Task65.4 Independently Calibrated Matched Frontier Summary

Task65.4 is complete.

## Protocol

The experiment reuses the exact Task65.3 LoTTE technology/search 100k Dense
and dynamic IntentRoute rankings. Both methods receive the same
`tiktoken/cl100k_base` accounting, the original Task38 179/417
calibration/test split, and a dense budget grid covering ratios `1.00` through
`0.80` in `0.01` increments with `min_keep` in `4..8`.

Unlike the original same-action comparison, Dense and IntentRoute independently
select their actions on calibration queries. The audit reports:

- maximum saving under matched calibration Hit-loss constraints;
- calibration-targeted saving actions and their frozen-test drift;
- a post-hoc same-saving interpolation over the complete held-out Pareto curve;
- query-paired bootstrap intervals for independently selected actions.

## Result

Under the zero observed calibration-drop constraint, IntentRoute selects
`r0.95/m4` and obtains `6.18%` frozen-test saving with mean Hit delta `0.00pp`.
Dense selects `r1.00/m4`, meaning no compression and `0.00%` saving. The mean
Hit values are equal, but strict seed-level non-inferiority is not established
for IntentRoute (`0/3`), so this is a mean operating-point result rather than a
universal no-loss guarantee.

At a `1pp` calibration margin, IntentRoute selects `r0.84/m4`, yielding
`17.13%` test saving and `-1.28pp` mean Hit delta. Dense still selects no
compression under that calibration split. At a `2pp` margin, both methods
compress aggressively: IntentRoute gives `20.90%/-1.60pp`, while Dense gives
`25.22%/-2.40pp`.

The post-hoc held-out frontier interpolation estimates the IntentRoute-minus-
Dense Hit difference at equal test saving as `+0.47pp`, `+0.04pp`, `+0.22pp`,
and `-0.01pp` at 5%, 10%, 15%, and 20% saving. These descriptive differences
are small and are not calibration-selected significance claims.

## Boundary

Task65.4 closes the missing independent-Dense-selection comparison. It supports
a bounded claim that the routed ranking can expose a conservative nonzero
calibration-eligible saving where Dense does not on the pre-specified 100k
split. It does not establish strict non-inferiority, universal Pareto dominance,
or a large same-saving quality advantage.
