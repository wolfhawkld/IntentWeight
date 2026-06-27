# Task60 Arm-Count Sensitivity Summary

Updated: 2026-06-25

## Objective

Task60 stress-tests the fixed `n_clusters=32` design choice. The goal is not to
prove that 32 is theoretically optimal. The goal is to show whether KMeans arms
are a reasonable engineering surface for route control, and where the
feedback/gated controller becomes sensitive to arm granularity.

The experiment uses LoTTE technology/search 100k, MiniLM embeddings, fixed
seeds `13,17,19`, and `K in {8,16,32,64,128}`. For each K, it evaluates:

- `static_nearest_ensemble`: static geometry route prior;
- `full_multi_route`: feedback-updated LinUCB under the full dense/BM25 rescue
  surface;
- `gated_cost_aware`: retrieval-stage dense-saving boundary.

Final-context token results use the same Task38-style calibration/test protocol
under the `task60_100k` split.

## Artifacts

- Route runs:
  `paper/experiments/results/task60_arm_count_k*_100k/`
- Budget evaluations:
  `paper/experiments/results/task60_k*_100k_context_budget.*`
- Summary script:
  `paper/experiments/scripts/task60_arm_count_sensitivity_summary.py`
- Aggregate summary:
  `paper/experiments/results/task60_arm_count_sensitivity_summary.md`

## Main Result

| K | Static route reward | Full Hit@10 | Full test delta | Full token saving | Gated dense rate | Gated test delta | Gated token saving |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 0.9128 | 0.8837 | +1.44 pp | 6.23% | 0.4083 | -1.84 pp | 16.90% |
| 16 | 0.8826 | 0.8809 | +0.80 pp | 10.49% | 0.6089 | -1.68 pp | 11.95% |
| 32 | 0.8563 | 0.8775 | +0.56 pp | 4.68% | 0.7377 | -4.48 pp | 18.00% |
| 64 | 0.8272 | 0.8792 | +0.40 pp | 11.19% | 0.8986 | -3.76 pp | 12.47% |
| 128 | 0.8479 | 0.8837 | +1.20 pp | 10.23% | 0.9502 | -3.12 pp | 15.64% |

## Interpretation

Static-nearest geometry is robust across the arm-count grid. Route reward stays
between `0.8272` and `0.9128`, and selected-cluster hit stays high
(`0.8496-0.9480`). This supports the bounded claim that local geometry provides
a useful route-control surface.

Full multi-route retrieval is stable at the fused-ranking level. Full Hit@10
stays between `0.8775` and `0.8837`, and frozen-test budgeted rows show positive
mean Hit@10 deltas while saving final context tokens. This is the appropriate
place to claim robustness to reasonable arm-count changes.

Retrieval-stage gated routing is sensitive to K. Smaller K values allow much
more dense-call reduction (`dense rate=0.4083` at K=8), but all gated rows still
show negative frozen-test Hit@10 deltas. Larger K values dilute feedback over
too many arms and push the controller back toward dense fallback. This supports
treating learned gated retrieval as a cost-aggressive boundary setting, not as
the main quality-preserving result.

## Paper-Use Guidance

Use Task60 to defend the design choice:

> KMeans arm count is a reproducible engineering parameter, not a theoretical
> manifold optimum. The full multi-route controller is robust across reasonable
> arm counts, while retrieval-stage dense-saving gates require separate tuning.

Do not write:

> `n_clusters=32` is optimal, or arm count has no effect on feedback learning.
