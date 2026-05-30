# Task36.5 Main-Text Table Alignment

Updated: 2026-05-31

## Purpose

This task aligns the current full draft with the table and figure placement
plan. It does not add new experiments. The goal is to make the draft easier to
convert into a formal paper by making main-paper tables, appendix-facing
tables, and claim boundaries explicit.

## Files Updated

- `paper/full_draft/05_experimental_setup.md`
- `paper/full_draft/06_results.md`
- `paper/full_draft/11_table_figure_plan.md`
- `paper/experiments/task_paper_use_status.md`

## Changes

- Added a paper-facing caption for Table 1 in the experimental setup.
- Added captions for the main result tables:
  - Table 2: LoTTE token-quality frontier;
  - Table 3: LoTTE 100k component ablation;
  - Table 4: feedback self-evolution summary;
  - Table 5: LoTTE geometry diagnostics.
- Added a compact feedback self-evolution table to make route-policy learning
  visible without relying only on prose.
- Marked seed stability, secondary dataset evidence, encoder robustness, and
  downstream generation smoke as appendix-facing in a conference-length
  version.
- Updated the placement plan so its table labels match the current draft.

## Paper-Facing Decision

The main paper should retain Table 2 and Table 3 under almost any target venue.
Table 4 is important for the feedback-learning contribution. Table 5 should be
kept in the main paper if space permits; otherwise the geometry trend can be
shown as a figure and the numeric table can move to the appendix.

Appendix-facing tables are still valuable evidence. They should not be deleted,
but they should not crowd out the main quality-token frontier, component
ablation, and feedback self-evolution story.
