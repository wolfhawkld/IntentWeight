# Task80.2 Citation and Figure 3 Layout Revision

Status: complete

Date: 2026-07-21

## Objective

Improve publication readability without changing the paper's evidence,
experimental values, or claim boundary. The revision is limited to compact
author-year citations and removal of Figure 3 legend/data collisions.

## Citation Revision

The Elsevier CAS manuscript retains the IP&M-compatible author-year
configuration and `cas-model2-names` bibliography style. The optional natbib
`longnamesfirst` flag was removed from both the anonymous manuscript and the
supplementary-material entry point. First citations with three or more authors
therefore use the compact `FirstAuthor et al. (Year)` form rather than expanding
the complete author list.

Reference-list content, citation keys, bibliography entries, hyperlink color,
and bibliography ordering were not changed.

## Figure 3 Layout Revision

Figure 3 retains the same three panels and the unchanged
`figure3_geometry_to_control_data.csv` source:

- Panel A moves the metric legend below the plotting region and states the
  technology/science line-style encoding in the axis-label band;
- Panel B moves the grouped-bar legend below the plotting region while keeping
  direct bar-value labels;
- Panel C replaces the in-plot legend with endpoint labels for static route
  reward, gated Dense rate, and gated Hit delta;
- the submission asset remains 190 mm by 88 mm, with a 7 pt minimum text size.

The standalone vector asset and the complete CAS page were visually inspected.
No legend, endpoint label, axis title, plotted point, or caption overlaps another
data-bearing element at normal PDF reading scale.

## Explicitly Deferred

- Table-value bolding remains author-directed and was not added.
- The CAS `fleqn` equation alignment remains unchanged.
- Table captions remain above tables and figure captions remain below figures.
- No figure data, table data, metric, experiment, or claim was changed.

## Validation

- Figure generator syntax and execution: PASS;
- ACL-style LaTeX validation and 34-page PDF audit: PASS;
- Elsevier CAS build and submission validation: PASS;
- CAS anonymous manuscript: 26 pages;
- experiment-artifact audit: `921/921` PASS;
- manuscript table/figure audit: `128/128` PASS;
- paper-evidence audit: PASS.

## Claim Effect

Task80.2 has no scientific claim effect. It makes related-work citations easier
to scan and makes the geometry-to-route-control evidence readable without
concealing mixed or boundary behavior. Geometry remains diagnostic support,
feedback remains controlled simulation, Dense remains the recall floor, and
efficiency remains final evidence-context input tokens rather than total
serving cost.
