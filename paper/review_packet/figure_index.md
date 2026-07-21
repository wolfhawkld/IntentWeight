# Figure Index

Updated: 2026-07-17

Data figures are generated deterministically from experiment artifacts.
Figure 1 remains an author-owned placeholder and must be replaced from its specification.

| Figure | Purpose | Review asset | Regeneration source |
|---|---|---|---|
| Figure 1 | IntentRoute system diagram | [figure1_system_diagram.svg](../full_draft/figures/figure1_system_diagram.svg) | [figure1_author_spec.md](../full_draft/figures/figure1_author_spec.md) |
| Figure 2 | Paired quality-context trade-offs across LoTTE scales | [figure2_token_quality_frontier.svg](../full_draft/figures/figure2_token_quality_frontier.svg) | [figure2_token_quality_frontier_data.csv](../full_draft/figures/figure2_token_quality_frontier_data.csv) |
| Figure 3 | Local geometry to route-control behavior | [figure3_geometry_to_control.svg](../full_draft/figures/figure3_geometry_to_control.svg) | [figure3_geometry_to_control_data.csv](../full_draft/figures/figure3_geometry_to_control_data.csv) |

Regenerate deterministic data-figure review assets from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_6_generate_main_figures.py
```
