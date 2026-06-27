# Task61 Geometry-To-Control / Geometry-To-Gain Analysis

Updated: 2026-06-26

## Objective

Task61 connects the existing geometry diagnostics to route-control outcomes
without making a theorem-level manifold claim. The task uses existing
artifacts only:

- Task30 technology/search geometry diagnostics;
- Task43 science/search geometry diagnostics;
- Task58 geometry-vs-random route control;
- Task60 arm-count sensitivity;
- Figure 4 geometry-to-gain diagnostic data.

## Artifacts

- Script: `paper/experiments/scripts/task61_geometry_to_control_analysis.py`
- Result report: `paper/experiments/results/task61_geometry_to_control_analysis.md`
- Correlation CSV: `paper/experiments/results/task61_geometry_to_control_analysis.csv`
- Observation CSV: `paper/experiments/results/task61_geometry_to_control_points.csv`
- JSON payload: `paper/experiments/results/task61_geometry_to_control_analysis.json`

## Main Interpretation

The evidence is strongest at the route-control layer. Task58 shows that
static geometry strongly outperforms uniform random route selection on
route reward and selected-cluster hit. Task60 shows that learned route
reward and cluster hit fall as K becomes too fine, and the gated controller
responds by increasing dense fallback.

The cross-scale Figure 4 correlations are mixed and small-N. That result is
useful: it keeps the paper from overclaiming that geometry alone determines
final Hit@10 or token saving. Final quality-cost behavior is produced by
the full controller: geometry-defined arms, feedback-updated LinUCB route
confidence, dense/BM25 rescue, and calibrated final-context budgeting.

## Paper-Use Guidance

Write:

> Geometry diagnostics provide explanatory and design-guiding signals for
> structured route control, while final quality-cost gains arise from the
> calibrated multi-route controller.

Do not write:

> The manifold hypothesis is proven, or geometry alone explains final Hit@10.
