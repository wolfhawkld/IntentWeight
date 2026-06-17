# Task44 Figure Evidence Upgrade

Updated: 2026-06-16

Task44 improves the manuscript's paper-facing visual evidence. It does not add
new retrieval experiments. It derives new vector figure assets from existing
audited artifacts so that the main paper can present the evidence chain with
figures rather than relying primarily on dense tables.

## Scope

The local scope is figure/table presentation only:

- no new LoTTE domain experiments on this device;
- no GPU/BGE embedding experiments on this device;
- no change to the underlying experiment results;
- all new figure data are derived from existing CSV/JSON artifacts.

## New Figure 4: Geometry-to-Gain Diagnostic

Files:

- `paper/full_draft/figures/figure4_geometry_to_gain_data.csv`
- `paper/full_draft/figures/figure4_geometry_to_gain.svg`
- `paper/latex/figures/figure4_geometry_to_gain.pdf`

Purpose:

Figure 4 connects geometry diagnostics to the observed calibrated quality-cost
frontier. It uses `ContextRetention@10` as the x-axis and plots:

- IntentWeight Hit@10 delta vs dense;
- final context-token saving.

The source joins:

- Figure 2 calibrated token-quality data;
- Figure 3 geometry diagnostic data.

Important interpretation:

The science/search points use the same budgeted policy values used by Figure 2,
not the fixed top-10 ranking deltas in the cross-domain table. This keeps the
figure focused on the compression frontier. Geometry is treated as an
explanatory and calibration signal, not as a deterministic predictor or theorem.

## New Figure 5: Feedback Adaptation Curve

Files:

- `paper/full_draft/figures/figure5_feedback_adaptation_data.csv`
- `paper/full_draft/figures/figure5_feedback_adaptation.svg`
- `paper/latex/figures/figure5_feedback_adaptation.pdf`

Purpose:

Figure 5 visualizes feedback-driven self-improvement in the route-policy field.
It plots:

- selected-cluster hit;
- last true reward;
- dense rate;
- LinUCB rate;
- final context token ratio.

The source combines:

- `task33_3_clean_ablation_table.csv` for the main feedback settings;
- `task33_2_feedback_trust_strong/linucb_cost_summary.csv` and
  `task33_2_feedback_sensitivity_context_tokens.csv` for the strong-noise
  failure boundary.

Interpretation:

Trust-weighted and mild feedback improve route-policy metrics and reduce dense
reliance under controlled simulation. Strong-noise feedback is intentionally
shown as a boundary case, and oracle feedback is shown as an upper bound.

## Manuscript Integration

The LaTeX manuscript now references the two new figures:

- Figure 4 is introduced in the geometry diagnostics discussion.
- Figure 5 is introduced in the feedback-driven adaptation section.

This shifts part of the manuscript from table-heavy evidence presentation to a
more figure-led argument:

1. Figure 2: quality-cost frontier.
2. Figure 3: geometry diagnostics across scale/domain.
3. Figure 4: geometry-to-gain diagnostic relation.
4. Figure 5: feedback-driven route adaptation.

## Next Checks

The next validation step should run:

```bash
.venv/bin/python paper/experiments/scripts/task43_audit_manuscript_tables_figures.py
make -C paper/latex audit
git diff --check
```

The audit script has been extended to check Figure 4 and Figure 5 data
consistency against their source artifacts.
