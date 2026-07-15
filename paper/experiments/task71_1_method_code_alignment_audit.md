# Task71.1 Method-to-Code Alignment Audit

Updated: 2026-07-13

## Scope and Decision

This audit aligns paper-facing method claims with the evaluated implementation.
It changes documentation and generated manuscript artifacts only; no retrieval
algorithm, result artifact, or experimental protocol is rerun or reinterpreted.
The affected validation categories are claim narrative, experimental protocol
fairness, statistical interpretation, reproducibility, and submission
readiness.

## Line-Level Alignment Record

| Paper-facing item | Verified implementation | Resolution |
|---|---|---|
| LinUCB context | `linucb_online_baseline.py:81-89` fits PCA on corpus embeddings, transforms query embeddings, and L2-normalizes the resulting controller vectors; `linucb_cost_aware_routing.py:544-566` reuses that context. | Method Section 3.5 now describes a normalized PCA-projected query vector only. Dense/BM25 strength, route overlap, feedback summaries, and budget state are not claimed as concatenated LinUCB inputs. |
| Route confidence and drift | `linucb_cost_aware_routing.py:690-735` selects arms from the controller context, then computes policy confidence and centroid-based drift before `decide_route`. | The draft now calls these separate gating signals rather than controller-vector feature groups. |
| Feedback reward | `linucb_cost_aware_routing.py:860-894` uses observed simulated evidence reward with trust/propagation update weights; no candidate-cost term enters `policy.update`. | The unimplemented $r_t=g_t-\lambda c_t$ equation is removed. Cost is measured separately through routing diagnostics and calibrated final-context budgeting. |
| Reward attribution | `linucb_cost_aware_routing.py:860` supports `cluster_only` and `final_fused`; `task69_common_protocol.json` specifies final-fused for common rows. | The draft identifies `final_fused` as the common Task69/Task70 attribution and reserves `cluster_only` for mechanism diagnostics. |
| Budget operator | `task37_context_budget_search.py:72-92` keeps a mandatory prefix, skips non-fitting later chunks, and can retain lower-ranked smaller chunks. | The draft now calls this an order-preserving budgeted subset, not a longest contiguous prefix. |
| Epoch and protocol scope | `task69_common_protocol.json` specifies eight prequential epochs, while the CLI retains a historical default of three. | The common protocol is described as eight epochs; deviations are delegated to Supplementary Table S29. |
| Feedback generalization | Task70 formal artifacts use five history/test folds, three seeds, eight history epochs, and zero held-out feedback updates. | Results, limitations, conclusion, and the protocol registry now disclose that learned feedback does not beat matched static/cold full routing on unseen first-pass queries and that frozen gating is unsafe. |

## Regeneration and Validation Requirements

After source edits, regenerate the ACL migration and journal package, then run:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
.venv/bin/python paper/experiments/scripts/task36_12_migrate_latex.py
.venv/bin/python paper/experiments/scripts/task36_12_generate_latex_figures.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
.venv/bin/python paper/experiments/scripts/task66_build_journal_submission.py
.venv/bin/python paper/experiments/scripts/task66_validate_journal_submission.py
.venv/bin/python paper/experiments/scripts/task67_validate_paper_evidence.py
make -C paper/latex audit
git diff --check
```

## Completion Record

Completed: 2026-07-13.

- The full-draft validator, ACL migration/LaTeX validator, ACL PDF audit,
  table/figure data audit, paper-evidence validator, and journal-submission
  validator passed after regeneration.
- The CAS journal package initially fell back to bitmap EC fonts, creating
  Type 3 fonts in its main and supplementary PDFs. Both CAS entry points now
  load the already-installed Latin Modern package; recompilation confirms that
  the anonymous manuscript, supplement, title page, and figure PDFs contain no
  Type 3 fonts.
- `git diff --check` passed. No retrieval artifact or numerical result was
  regenerated or changed by this documentation-alignment task.

## Claim Boundary After Alignment

The aligned manuscript retains the central chain:

`local geometry -> adaptive route selection -> controlled feedback correction -> independently calibrated context budget -> bounded quality-context-cost trade-off`

It does not claim a cost-penalized LinUCB reward, direct confidence-to-compression
prediction, real-user RLHF, transferable first-pass feedback superiority, or
unmeasured end-to-end system efficiency.
