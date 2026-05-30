# Task36.6 Main Figure Assets

Updated: 2026-05-31

## Purpose

This task creates regenerable draft assets for the three main paper figures.
It does not add new experiments or new claims. The figures are generated from
existing experiment artifacts and are intended for writing, review, and later
conversion into camera-ready venue artwork.

## Files Added

- `paper/experiments/scripts/task36_6_generate_main_figures.py`
- `paper/full_draft/figures/README.md`
- `paper/full_draft/figures/figure1_system_diagram.svg`
- `paper/full_draft/figures/figure1_system_diagram.mmd`
- `paper/full_draft/figures/figure2_token_quality_frontier.svg`
- `paper/full_draft/figures/figure2_token_quality_frontier_data.csv`
- `paper/full_draft/figures/figure3_geometry_diagnostics.svg`
- `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv`

## Files Updated

- `paper/full_draft/04_method.md`
- `paper/full_draft/06_results.md`
- `paper/full_draft/11_table_figure_plan.md`
- `paper/full_draft/README.md`
- `paper/experiments/task_paper_use_status.md`

## Figure Mapping

- Figure 1: IntentWeight system diagram.
  - Shows query/context features, LinUCB route policy, dense fallback, BM25,
    cluster-local retrieval, final context budgeting, generation, and
    trust-weighted feedback.
  - Caption boundary: dense is a recall floor, not a removed component.
- Figure 2: token-quality frontier across LoTTE scale.
  - Uses the LoTTE 100k-638k final context-token frontier.
  - Shows dense versus conservative-policy $\mathrm{Hit@10}$ and final
    context token ratio.
  - Caption boundary: above-dense means are descriptive at current seed counts.
- Figure 3: geometry diagnostic trend.
  - Uses LoTTE scale diagnostics for $\mathrm{NearestClusterHit@3}$,
    $\mathrm{ContextRetention@10}$, and $\mathrm{PCAvar@64}$.
  - Caption boundary: diagnostics support local-structure routing but are not
    theorem-level manifold proof.

## Regeneration Command

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```

The script uses only the Python standard library.

## Validation

The generated SVG files are non-empty and parse as XML. The figure source CSVs
match the current paper-facing LoTTE token-quality and geometry tables.
