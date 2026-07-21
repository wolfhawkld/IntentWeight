# Draft Figure Assets

Updated: 2026-07-17

These assets are paper figures generated from tracked experiment artifacts.
Figure 1 remains an author-owned structural placeholder; Figures 2 and 3 are
deterministic vector data figures.

## Files

- `figure1_system_diagram.svg`: method/system diagram.
- `figure1_system_diagram.mmd`: Mermaid source for the system diagram.
- `figure2_token_quality_frontier.svg`: paired Pareto-style quality-context map
  connecting Dense adaptive truncation to IntentRoute for each displayed LoTTE
  domain/scale point.
- `figure2_token_quality_frontier_data.csv`: source data for Figure 2.
- `figure3_geometry_to_control.svg`: three-panel main-paper geometry-to-control
  figure covering scale diagnostics, random-route attribution, and arm
  granularity/fallback.
- `figure3_geometry_to_control_data.csv`: panel-keyed source data for Figure 3.

The geometry scale trend and feedback-adaptation assets are retained as
supplementary review material:

- `figure3_geometry_diagnostics.svg` and its source CSV;
- `figure5_feedback_adaptation.svg` and its source CSV.

## Regeneration

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```

The script uses only the Python standard library.
