# Draft Figure Assets

Updated: 2026-06-14

These assets are draft paper figures generated from existing experiment
artifacts. They are intended for writing and review, not as final camera-ready
venue artwork.

## Files

- `figure1_system_diagram.svg`: method/system diagram.
- `figure1_system_diagram.mmd`: Mermaid source for the system diagram.
- `figure2_token_quality_frontier.svg`: LoTTE technology/search and
  science/search Hit@10 and final context-token frontier plotted by corpus
  chunk count.
- `figure2_token_quality_frontier_data.csv`: source data for Figure 2.
- `figure3_geometry_diagnostics.svg`: LoTTE technology/search and
  science/search geometry diagnostic trend plotted by corpus chunk count.
- `figure3_geometry_diagnostics_data.csv`: source data for Figure 3.

## Regeneration

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```

The script uses only the Python standard library.
