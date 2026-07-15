# Task71.3 Literature and Statistical-Framing Audit

Updated: 2026-07-13

## Scope

This audit refreshes positioning and statistical language without changing a
retrieval result, a dataset protocol, or a numerical table. It affects claim
narrative, statistical rigor, citation traceability, and final submission
readiness under `docs/human_validation_criteria.md`.

## Primary-Source Literature Check

The existing draft already cites MBA-RAG as the closest contextual-bandit RAG
comparison. Four peer-reviewed 2025 sources are added to cover adjacent work
that a reviewer may otherwise mistake for the same contribution:

| Work | Directly relevant mechanism | Paper-facing distinction |
|---|---|---|
| SeaKR (ACL 2025) | Activates retrieval from model-internal uncertainty. | IntentRoute routes among corpus-local evidence paths and updates route confidence from controlled repeated feedback; it does not depend on hidden-state uncertainty. |
| LLM-Independent Adaptive RAG (EMNLP 2025) | Uses external query features to decide whether retrieval is needed. | IntentRoute retains Dense as a recall floor and learns among routes over a repeated stream rather than making only a single-query retrieval decision. |
| AttnComp (Findings EMNLP 2025) | Varies compression using language-model attention. | IntentRoute controls upstream evidence routes and a calibrated chunk budget; it does not claim an attention-based compressor. |
| ACC-RAG (Findings EMNLP 2025) | Changes compression rate using input complexity and a hierarchical compressor. | IntentRoute is complementary to downstream context compression and evaluates the route-and-budget layer separately. |

The related-work revision therefore avoids first-use language for adaptive
retrieval or adaptive context budgets while preserving the paper's narrower
contribution: geometry-guided route control, controlled feedback adaptation,
Dense rescue, and independently calibrated final-context budgeting.

## Statistical-Framing Decision

1. The frozen calibration/test and normalized five-fold scale comparisons are
   the primary evidence families. Their query-paired intervals and tests are
   reported per declared condition.
2. The fixed 1pp condition is a strict engineering guardrail for the binary
   `Hit@10` endpoint, not formal statistical equivalence. It is about four
   hits on the 417-query original frozen test split and about six hits on the
   596-query out-of-fold population.
3. Fine-grid selection, overlapping-partition sensitivity, interpolation,
   geometry/arm controls, feedback recovery, transfer rows, and multi-judge
   checks are mechanism, robustness, or boundary analyses. They are not pooled
   as IID replications and cannot support a global unadjusted superiority
   claim.
4. No headline claim relies on a nominal unadjusted significance crossing from
   a secondary analysis. This permits transparent per-condition paired results
   without manufacturing a family-wide pooled p-value.

## Artifacts Changed

- `paper/full_draft/03_related_work.md`
- `paper/full_draft/05_experimental_setup.md`
- `paper/full_draft/08_limitations.md`
- `paper/full_draft/references.bib`
- `paper/experiments/post_task69_submission_readiness_plan.md`

## Completion Record

Completed: 2026-07-13.

The canonical Markdown was migrated to ACL LaTeX and the journal package was
regenerated. The following checks passed after the final bibliography update:

- `task36_9_validate_full_draft.py`: 11 manuscript files, 30 citation keys,
  30 BibTeX entries, and no uncited entries;
- `task36_12_validate_latex.py`: 10 LaTeX inputs, 30 citation keys, 30 BibTeX
  entries, and 37 resolved cross-references;
- `task66_validate_journal_submission.py`: journal package structure,
  manuscript/supplement builds, abstract and highlight limits, and display
  cross-references;
- `task67_validate_paper_evidence.py`: five main tables, two figure-data
  artifacts, and 446 supplementary numeric values traced; and
- `git diff --check`: no whitespace errors.

This task changes positioning and inferential framing only. It introduces no
new numerical result, no pooled significance claim, and no broadened system or
deployment claim.
