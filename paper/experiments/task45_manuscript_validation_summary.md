# Task45 Manuscript Validation and Claim Alignment

Updated: 2026-06-17

Task45 aligned the manuscript with the current human validation criteria. This
was a manuscript, LaTeX, and evidence-chain cleanup task; it did not introduce
new experiment results.

## Scope

The revision touched all five validation categories:

1. claim and manuscript narrative;
2. experimental evidence and baseline fairness;
3. statistical and analytical rigor;
4. presentation, reproducibility, and artifact traceability;
5. human-AI workflow and final submission readiness.

The preserved research chain is:

`local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`

Final-context budget control is now framed as the measurable efficiency
endpoint, not as the whole contribution. LinUCB is described as an adaptive
route-confidence learner rather than a new bandit algorithm, and simulated
feedback is framed as controlled correction evidence rather than production
RLHF validation.

## Completed Changes

- Reframed the title, abstract, introduction, discussion, limitations, and
  conclusion around feedback-adaptive evidence selection under local structure.
- Added calibration/test protocol wording for calibration-eligible context
  budgets and paired non-inferiority checks.
- Marked the 400k setting as diagnostic and pending follow-up instead of
  treating it as fully calibration-eligible.
- Added method details for route confidence, feature groups, and reproducible
  operating parameters without overloading the method section with
  implementation-log tables.
- Updated the main result table and appendix summary to include calibration
  eligibility and non-inferiority seed coverage.
- Updated the manuscript/table audit script so the generated checks match the
  revised paper-facing result format.
- Regenerated the LaTeX manuscript sections and verified the PDF audit.

## Evidence Anchors

The current paper-facing claims are backed by these artifact families:

- calibrated final-context budget results from the Task38 line of experiments;
- paired statistical checks from the Task37 line of experiments;
- final-context token accounting and LLM-input-cost framing from the Task29 and
  later manuscript revisions;
- harmed-query feedback recovery evidence from Task40;
- strong compression and reranker baseline coverage from Task46, Task47, and
  Task48;
- table and figure traceability audit from Task43;
- LaTeX migration and PDF build audit from Task36/Task43 tooling.

## Remaining Caveats

- The 400k point still needs a supplemental calibration follow-up before it can
  be presented as a full calibration-eligible headline setting.
- Seed-level non-inferiority is scale-dependent and should not be overstated.
- Feedback results remain simulated or controlled, not real-user deployment
  evidence.
- `Hit@10` supports "at least one usable evidence chunk" and does not prove
  complete evidence collection.
- Same-budget MMR, compressor-normalized, and cross-encoder reranker baselines
  have now been run as Task46, Task48, and Task47; answer-level validation
  remains the larger remaining evidence gap.

## Verification

Commands completed with the project virtual environment:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
.venv/bin/python paper/experiments/scripts/task36_12_migrate_latex.py
.venv/bin/python paper/experiments/scripts/task36_12_generate_latex_figures.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
.venv/bin/python paper/experiments/scripts/task43_audit_manuscript_tables_figures.py
make -C paper/latex audit
```

The final audit status was:

- full draft validation: passed;
- LaTeX validation: passed;
- table/figure audit: `238/238` checks passed;
- PDF audit: passed with `critical_log_lines=0`.

## Next Recommended Task

Task46 is completed in `task46_sentence_mmr_same_budget_summary.md`, Task48
extends it with the compressor-normalized comparison in
`task48_compressor_normalized_summary.md`, and Task47 adds the heavier
cross-encoder reranker baseline in `task47_cross_encoder_reranker_summary.md`.
Together, these results support the route-and-budget controller framing:
IntentWeight can be stacked with a shared final-context compressor and remains
competitive under a strong reranker baseline, but it should not be presented as
dominating compression or reranking.

Task49 has now completed the manuscript framing pass around the strong-baseline
evidence; see `task49_strong_baseline_reframing_summary.md`.

The next paper task is a venue-specific cut: reduce the current full draft to
the target submission length while preserving the route-and-budget controller
framing. A larger answer-level evaluation remains a separate follow-up.
