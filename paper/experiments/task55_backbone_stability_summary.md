# Task55 Backbone Stability Summary

Updated: 2026-06-24

## Objective

Summarize seed-level stability for the completed MiniLM, BGE, and E5
matched-backbone experiments without rerunning retrieval. This task uses the
existing Task38, Task53, and Task54 artifacts for the fixed seeds `13,17,19`.

The goal is not to find the best seed. The seeds are fixed replicate
conditions used to check whether the paper claims are stable and statistically
testable under random clustering, query order, and simulated feedback
variation.

## Artifacts

- Summary script:
  `paper/experiments/scripts/task55_backbone_stability_summary.py`
- Aggregate table:
  `paper/experiments/results/task55_backbone_stability_summary.csv`
- Per-seed table:
  `paper/experiments/results/task55_backbone_stability_summary.per_seed.csv`
- JSON summary:
  `paper/experiments/results/task55_backbone_stability_summary.json`
- Markdown report:
  `paper/experiments/results/task55_backbone_stability_summary.md`

## Main Result

| Setting | Policy | Mean Hit Delta | Seed SD | Seed 95% CI | Mean Token Saving |
| --- | --- | ---: | ---: | ---: | ---: |
| MiniLM gated | `token_budget_r0.95_m4` | +0.00 pp | 0.63 pp | [-1.58, +1.58] pp | 6.18% |
| BGE full | `token_budget_r0.92_m4` | -0.08 pp | 0.37 pp | [-0.99, +0.83] pp | 11.99% |
| BGE gated | `token_budget_r0.88_m4` | -2.48 pp | 0.50 pp | [-3.72, -1.24] pp | 16.21% |
| E5 full | `token_budget_r0.88_m7` | -0.64 pp | 0.14 pp | [-0.98, -0.30] pp | 12.20% |
| E5 gated | `token_budget_r0.95_m4` | -3.44 pp | 0.91 pp | [-5.69, -1.18] pp | 6.83% |
| BGE positive | `token_budget_r0.97_m4` | +0.88 pp | 0.14 pp | [+0.54, +1.22] pp | 7.23% |

## Interpretation

The three-seed variance check supports the current paper framing:

- BGE full is a stable near-dense token-saving operating point.
- BGE positive is a stable quality-first point that exceeds BGE dense while
  still saving final context tokens.
- E5 full is stable but slightly below its dense baseline, so it supports
  near-dense token-saving robustness rather than positive-Hit tuning.
- BGE/E5 gated variants are consistently below dense and should be written as
  cost-aggressive boundary evidence.

Use paired query-level bootstrap confidence intervals and McNemar tests from
the source artifacts as the primary statistical checks. Use this seed-level
summary as a stability supplement, not as a large repeated-random-trial claim.

## Paper-Use Guidance

A safe paper-facing statement is:

> Across fixed seeds `13,17,19`, the matched-backbone route-and-budget results
> show low seed-level variance for the BGE and E5 full multi-route settings.
> The BGE quality-first operating point remains above dense on all three seeds,
> while the gated-cost variants consistently lose Hit@10, supporting their use
> as boundary cases rather than headline settings.

