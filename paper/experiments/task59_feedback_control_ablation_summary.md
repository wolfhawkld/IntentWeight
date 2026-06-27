# Task59 Feedback-Control Ablation Summary

Updated: 2026-06-25

## Objective

Task59 isolates what feedback-updated LinUCB contributes beyond static geometry
and no-feedback controls. The experiment uses LoTTE technology/search 100k,
MiniLM embeddings, fixed seeds `13,17,19`, and the same Task38-style
calibration/test budget protocol under the `task59_100k` split.

This task is a component-attribution and claim-boundary experiment. It is not
intended to replace the main Task38/53/54 quality-cost frontier.

## Artifacts

- Trust-weighted route run:
  `paper/experiments/results/task59_feedback_control_100k_trust/`
- No-feedback route run:
  `paper/experiments/results/task59_feedback_control_100k_none/`
- Budget evaluations:
  `paper/experiments/results/task59_*_100k_context_budget.*`
- Summary script:
  `paper/experiments/scripts/task59_feedback_control_summary.py`
- Aggregate summary:
  `paper/experiments/results/task59_feedback_control_summary.md`

## Main Result

| Setting | Route reward | Selected cluster hit | Dense rate | Primary rate | Test Hit delta | Token saving |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | 0.0000 | -1.68 pp | 17.86% |
| Learned gated cost-aware | 0.6790 | 0.5766 | 0.7377 | 0.2623 | -5.20 pp | 11.83% |
| Static nearest gated | 0.8563 | 0.8870 | 0.9586 | 0.0414 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | 0.0000 | -1.60 pp | 16.56% |
| Static nearest ensemble | 0.8563 | 0.8870 | 1.0000 | 0.0000 | -1.68 pp | 18.14% |
| Uniform random ensemble | 0.1499 | 0.1577 | 1.0000 | 0.0000 | -1.44 pp | 18.39% |

All rows use the same 179-query calibration split and 417-query frozen test
split for final-context budget selection. Query-level paired non-inferiority is
not established for these Task59 operating points (`0/3` seeds for all rows).

## Interpretation

The no-feedback gated control has high final Hit@10 because it falls back to
the full dense/BM25 surface. It has dense rate `1.0000`, LinUCB primary rate
`0.0000`, and low route reward (`0.1504`). This prevents the paper from
attributing fallback quality to feedback learning.

Static-nearest geometry remains a strong route prior. It gives route reward
`0.8563` and selected-cluster hit `0.8870`, both much higher than random and
no-feedback controls. This strengthens the Task58 conclusion that geometry is
an effective route-control signal.

Learned LinUCB feedback improves route quality over no-feedback/random controls
(`0.6790` route reward versus about `0.15`) and can reduce retrieval-stage
dense usage in the gated setting. However, the current learned-gated thresholds
trade too much final Hit@10 for dense-call savings, so this row should be
reported as cost-aggressive boundary evidence rather than a main
quality-preserving result.

## Paper-Use Guidance

Use Task59 to defend the component story:

> Feedback-updated LinUCB provides an adaptive route-confidence/control
> mechanism. It should not be described as the sole source of final fused
> Hit@10, because dense/BM25 rescue paths and static geometry priors remain
> important.

Do not write:

> LinUCB feedback alone outperforms static geometry or fully explains the final
> retrieval gains.
