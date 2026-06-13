# Task36.6 Main Figure Assets

Updated: 2026-06-14

## Purpose

This task creates regenerable draft assets for the three main paper figures.
The figures are generated from experiment artifacts and are intended for
writing, review, and later conversion into camera-ready venue artwork.
The 2026-06-14 refresh adds LoTTE science/search to Figure 2 and Figure 3 using
Task39 token-budget artifacts and the Task43 science/search geometry diagnostic.
The figure x-axis uses corpus chunk count; domain is retained only as a
line-style distinction.

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
  - Uses LoTTE technology/search 100k-638k and LoTTE science/search 20k/q200
    and 100k final evidence-context token validation.
  - X-axis is corpus chunk count, not a domain/category axis.
  - Shows IntentWeight budgeted policies versus dense-only adaptive truncation
    on $\mathrm{Hit@10}$ delta and final context-token saving.
  - Caption boundary: science/search 100k is a calibration-boundary point; the
    ranking-side gain transfers, but aggressive compression can introduce small
    frozen-test hit loss.
- Figure 3: geometry diagnostic trend.
  - Uses LoTTE technology/search and science/search diagnostics for
    $\mathrm{NearestClusterHit@3}$, $\mathrm{ContextRetention@10}$, and
    $\mathrm{PCAvar@64}$.
  - X-axis is corpus chunk count, not a domain/category axis.
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
