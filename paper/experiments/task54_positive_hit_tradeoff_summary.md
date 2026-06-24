# Task54 Positive-Hit Trade-Off Summary

Updated: 2026-06-24

## Objective

Test whether the Task53 trade-off can be tuned toward a quality-first operating
point where matched-backbone IntentWeight is slightly above the dense baseline
on Hit@10, while accepting lower token savings than the more aggressive
Task53 full multi-route setting.

## Result

Using BGE-base full multi-route rankings and a conservative token-budget policy
`token_budget_r0.97_m4`, the frozen Task38 held-out split gives:

| Seed | Method Hit@10 | BGE dense Hit@10 | Hit delta | Token saving |
| ---: | ---: | ---: | ---: | ---: |
| 13 | 0.9089 | 0.8993 | +0.96 pp | 8.11% |
| 17 | 0.9065 | 0.8993 | +0.72 pp | 7.07% |
| 19 | 0.9089 | 0.8993 | +0.96 pp | 6.50% |

The policy is calibration-eligible:

- calibration mean Hit@10 delta: `+0.19pp`;
- calibration mean token saving: `12.15%`;
- frozen-test mean Hit@10 delta: `+0.88pp`;
- frozen-test mean token saving: `7.23%`.

This confirms that the BGE matched-backbone frontier can be moved from the
Task53 higher-saving point (`~12%` tokens, near-dense Hit@10) to a
quality-first point (`~7%` tokens, slightly above dense Hit@10).

## E5 Boundary

The same offline policy scan did not find an E5-base full multi-route
token-saving point that is above E5 dense on the Task38 frozen test split. E5
still supports the broader Task53 robustness result as a near-dense
token-saving point, but the positive-Hit operating point is currently BGE-only.

## Artifacts

- Positive-Hit report:
  `paper/experiments/results/task54_bge_base_100k_positive_hit_context_budget.md`
- Paired statistics:
  `paper/experiments/results/task54_bge_base_100k_positive_hit_context_budget.test_paired.csv`
- Rankings:
  `paper/experiments/results/task54_bge_base_100k_positive_hit_context_budget.rankings.json`

## Paper-Use Guidance

Use Task54 as a tunability result, not as the only headline:

> On the BGE backbone, changing the context-budget operating point moves the
> frontier from higher token saving to a quality-first setting that slightly
> exceeds dense Hit@10 while still reducing final context tokens.

Keep the caveat that this positive-Hit setting is currently demonstrated for
BGE at LoTTE technology/search 100k. E5 does not show the same positive-Hit
point under the current frozen split.
