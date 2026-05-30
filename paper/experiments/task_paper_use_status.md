# Task Paper-Use Status

Updated: 2026-05-28

This file marks which internal task summaries should be used when writing the
paper. It prevents historical or superseded experiment notes from being
accidentally promoted into paper-facing claims.

## Status Labels

- **Main evidence**: can support main paper claims.
- **Supporting evidence**: can support ablations, robustness, protocol defense,
  or boundary discussion.
- **Boundary/negative evidence**: useful because it limits overclaiming; do not
  present as positive main evidence.
- **Historical/superseded**: kept for provenance only; do not cite as current
  evidence unless the newer correction is also cited.
- **Internal handoff/backlog**: not paper evidence.

## Main Evidence

| File | Status | Use in paper |
|---|---|---|
| `task29_2_token_quality_frontier.md` | Main evidence | Main token-quality frontier for the conservative confidence-based context policy. |
| `task29_confidence_context_policy_summary.md` | Main evidence | Defines the final context compaction policy and its LoTTE scale-up results. |
| `task30_lotte_geometry_scale_validation.md` | Main evidence | Geometry diagnostics supporting the piecewise relevance-manifold framing. |
| `task31_paper_evidence_package.md` | Main evidence package | Aggregated evidence source; use together with the later consistency audit and full draft. |
| `task33_3_clean_ablation_table.md` | Main/supporting evidence | Clean LoTTE 100k ablation table for dense floor, feedback, trust weighting, and final policy. |
| `task33_6_additional_seeds_summary.md` | Supporting evidence | Five-seed stability check for LoTTE 100k; do not claim statistical superiority. |

## Supporting Evidence

| File | Status | Use in paper |
|---|---|---|
| `task24_audit_fixes_summary.md` | Supporting evidence | Audit fixes, naming corrections, and guardrails. |
| `task25_credit_assignment_summary.md` | Supporting evidence | Route-level credit assignment and LinUCB self-evolution evidence. Cost columns are source-candidate proxies only. |
| `task28_1_context_token_backfill_summary.md` | Supporting guardrail | Backfilled final context token correction for historical runs. |
| `task28_context_token_cost_summary.md` | Supporting guardrail | Shows candidate-cost savings did not imply final context token savings under fixed top-10. |
| `task33_1_embedding_model_selection.md` | Supporting rationale | Explains CPU-friendly embedding model choice. |
| `task33_1a_multiqa_minilm_robustness_summary.md` | Supporting evidence | Same-resource-class encoder robustness check. |
| `task33_2_feedback_sensitivity_summary.md` | Supporting evidence | Feedback-noise sensitivity and trust-weighting behavior. |
| `task33_4_protocol_defense.md` | Supporting defense | Prequential simulated-feedback protocol defense. |
| `task33_5_llm_generation_smoke_summary.md` | Supporting sanity check | Small downstream generation smoke test; not a full human evaluation. |
| `task33_7_pre_writing_consistency_audit.md` | Supporting guardrail | Pre-writing claim consistency audit. |
| `task34_review_defense_revision_plan.md` | Supporting guardrail | Review-defense revision checklist incorporated into the draft. |
| `task36_1_geometry_formula_definitions.md` | Supporting writing revision | Paper-facing geometry diagnostic formulas; no new experiment. |
| `task36_2_secondary_dataset_evidence.md` | Supporting writing revision | Integrates PubMedQA, Banking77, eManual, and CUAD as supporting/boundary evidence; no new experiment. |

## Boundary Or Negative Evidence

| File | Status | Use in paper |
|---|---|---|
| `task26_low_cost_routing_summary.md` | Boundary/negative evidence | Candidate-cost trade-off only; does not prove final token savings. |
| `task27_dense_linucb_tradeoff_summary.md` | Boundary/negative evidence | Two-route dense-vs-LinUCB boundary test; sub-dense candidate cost loses quality and does not prove token savings. |

## Historical Or Superseded

| File | Status | Replacement |
|---|---|---|
| `task21_paper_ready_summary.md` | Historical/superseded | Use `task31_paper_evidence_package.md`, `task33_7_pre_writing_consistency_audit.md`, and `paper/full_draft/` instead. |
| `task23_lotte_scaleup_summary.md` | Partially superseded | Use only for historical scale-up provenance. For paper-facing token-cost results, use `task29_2_token_quality_frontier.md`; for geometry, use `task30_lotte_geometry_scale_validation.md`. |
| `task28_pre_token_cost_audit.md` | Historical/superseded guardrail | Use `task28_context_token_cost_summary.md` and `task28_1_context_token_backfill_summary.md` for completed corrections. |

## Internal Handoff Or Backlog

| File | Status | Note |
|---|---|---|
| `task33_5_llm_generation_smoke_handoff.md` | Internal handoff | Superseded by `task33_5_llm_generation_smoke_summary.md`. |
| `task33_pre_writing_validation_backlog.md` | Internal backlog | Use only for project management, not paper evidence. |

## Paper-Facing Rule

Do not cite internal `TaskXX` labels in the paper body. Convert them into
paper-facing names such as:

- conservative confidence-based context policy;
- token-quality frontier;
- multi-seed stability analysis;
- component ablation;
- geometry scale diagnostic;
- encoder robustness check;
- downstream generation smoke test;
- duplicate-evidence limitation analysis.
