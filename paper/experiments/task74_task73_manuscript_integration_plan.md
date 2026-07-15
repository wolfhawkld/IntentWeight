# Task74 Task73 Evidence Integration Plan

Status: completed 2026-07-16

## Objective

Integrate the preregistered Task73 LoTTE recreation/search and writing/search
100k results into the canonical manuscript and generated submission packages
without changing the tested method, rerunning the experiment, or broadening the
claim beyond the source artifacts.

## Fixed Evidence Boundary

Task74 must preserve the following distinctions:

- both added domains exhibit usable cluster-local route signal;
- writing/no-feedback provides the useful Task73 frontier: `+0.12pp` mean
  Hit@10 change with `10.09%` final-context-token saving and strict
  non-inferiority in `2/3` route seeds;
- recreation/no-feedback is a boundary result: `-0.76pp` mean Hit@10 change
  with `5.42%` saving and strict non-inferiority in `0/3` seeds;
- trust-weighted calibration falls back to Dense in all folds in both domains;
- the preregistered lexicality ordering was reversed and cannot explain the
  frontier contrast;
- geometry structures a route signal, feedback supports conditional
  post-failure recovery, and the final token budget is calibrated separately.
  None is presented as a direct causal guarantee of safe compression.

The two domains remain separate comparison families. Their queries, folds,
seeds, or results must not be pooled into a global superiority statistic.

## Manuscript Changes

1. Update the benchmark scope from seven settings/six domain areas to nine
   settings/eight domain areas.
2. Add the Task73 external-validity design to Experimental Setup.
3. Add a compact Task73 result paragraph to the cross-domain Results section.
4. Update Discussion, Limitations, and Conclusion with the observed
   domain-dependent frontier and Dense-fallback boundary.
5. Extend the supplementary protocol registry and add one compact,
   source-derived Task73 table covering domain properties, geometry, budget
   outcomes, and strict seed-level non-inferiority.
6. Register Task73 as paper evidence and update the manuscript README and
   table/figure placement plan.

## Traceability And Validation

- Source results:
  `paper/experiments/results/task73_lotte_domain_expansion.{json,csv,md}`.
- Protocol and interpretation:
  `paper/experiments/task73_lotte_domain_expansion_{plan,summary}.md`.
- Add an automated Task74 manuscript-integration validator that derives all
  displayed Task73 values from the machine-readable result artifact.
- Regenerate the review packet, ACL-style LaTeX, figures, and IP&M submission
  package from `paper/full_draft/`.
- Run full-draft, paper-evidence, table/figure, LaTeX, PDF, anonymity, and
  journal-submission checks.

## Completion Gate

Task74 is complete only when every Task73 manuscript value is source-derived,
all generated packages are synchronized, all repository-controlled validators
pass, and the remaining blockers are limited to the already declared
author-produced Figure 1 and author/submission metadata.
