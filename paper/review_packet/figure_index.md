# Figure Index

Updated: 2026-06-27

Draft figure assets are generated from existing experiment artifacts.
They are review assets, not final camera-ready artwork.

| Figure | Purpose | Review asset | Regeneration source |
|---|---|---|---|
| Figure 1 | IntentRoute system diagram | [figure1_system_diagram.svg](../full_draft/figures/figure1_system_diagram.svg) | [figure1_system_diagram.mmd](../full_draft/figures/figure1_system_diagram.mmd) |
| Figure 2 | Token-quality frontier across LoTTE scale | [figure2_token_quality_frontier.svg](../full_draft/figures/figure2_token_quality_frontier.svg) | [figure2_token_quality_frontier_data.csv](../full_draft/figures/figure2_token_quality_frontier_data.csv) |
| Figure 3 | Geometry-to-control diagnostic | [figure3_geometry_to_control.svg](../full_draft/figures/figure3_geometry_to_control.svg) | [figure3_geometry_to_control_data.csv](../full_draft/figures/figure3_geometry_to_control_data.csv) |

Regenerate the draft SVG assets from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```
