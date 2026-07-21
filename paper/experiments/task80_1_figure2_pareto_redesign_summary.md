# Task80.1 Figure 2 Paired Trade-off Redesign

Status: complete

Date: 2026-07-21

## Objective

Redesign Figure 2 so that the relationship between final evidence-context
tokens and query-level retrieval quality is visible in one paper-facing view.
This is a presentation revision: no experiment was rerun and no value in
`figure2_token_quality_frontier_data.csv` was changed.

## Design

The former two-panel scale plot is replaced by a paired quality-context map:

- the horizontal axis is final evidence-context token saving relative to Dense
  top-10;
- the vertical axis is the Hit@10 difference relative to Dense top-10;
- each arrow starts at a Dense adaptive-truncation result and ends at the
  matched IntentRoute result for the same domain and scale;
- color distinguishes the two methods, while marker shape distinguishes
  LoTTE technology/search and science/search;
- the technology/search 400k pair remains hollow and uses a dashed arrow to
  preserve its ineligible-primary-calibration diagnostic status;
- the Dense top-10 reference is shown at the origin.

All six source pairs are retained: technology/search at 100k, 200k, 400k, and
638k, plus science/search at 20k/q200 and 100k. In these observed pairs,
IntentRoute gives up part of the more aggressive Dense-truncation saving while
recovering Hit@10. The figure and caption explicitly avoid a universal Pareto
dominance claim.

## Generated Artifacts

- `paper/full_draft/figures/figure2_token_quality_frontier.svg`
- `paper/latex/figures/figure2_token_quality_frontier.pdf`
- `paper/journal_submission/latex/figures/figure2_token_quality_frontier.pdf`
- synchronized ACL/CAS manuscript sections and review-packet mirrors

The submission PDF figure is 190 mm by 76 mm, embeds a Type 0/TrueType font,
and contains no Type 3 font. It was visually checked in both the ACL-style and
Elsevier CAS page layouts at normal reading scale; labels, legend, axes, arrows,
and the hollow 400k diagnostic point remain readable without overlap.

## Validation

- full-draft citation audit: PASS (`32/32` citation keys covered);
- manuscript table/figure audit: `128/128` PASS;
- experiment-artifact audit: `921/921` PASS;
- paper-evidence audit: PASS;
- Task79 local gate: `14/14`, `PASS_COMPLETE`;
- ACL-style PDF audit: PASS, 34 pages;
- CAS submission validation: PASS, 26-page anonymous manuscript;
- Task80 final submission-control audit: `20/20` PASS.

## Claim Effect

The redesign makes the measured quality-efficiency trade-off easier to inspect
without changing its scientific boundary. It supports the paper's bounded
claim that adaptive route selection can recover query-level evidence hits
relative to aggressive dense-only truncation while retaining some final-context
token saving. It does not establish strict non-inferiority, complete evidence
collection, universal Pareto dominance, or end-to-end serving-cost reduction.
