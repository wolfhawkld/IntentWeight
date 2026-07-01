# IntentWeight Paper Draft

> **Superseded draft / 已归档草稿**: 本目录是 Task31-40 阶段的早期
> IntentWeight 草稿。当前论文主源已经迁移到 `paper/full_draft/`，LaTeX 源在
> `paper/latex/`。当前人类可读名称为 **IntentRoute**；历史 `IntentWeight`
> 仅保留为 legacy package、artifact label 和旧任务记录。后续写作与投稿不应从
> 本目录复制标题、方法名或结论，除非先按
> `docs/intentweight-paper-core-narrative.md` 重新校准。

Updated: 2026-06-11

This directory starts the paper-writing phase after Task31 consolidated the
experimental evidence. The draft uses
`paper/experiments/task31_paper_evidence_package.md`, the Task33.7 pre-writing
audit, the Task34 review-defense revision plan, and the Task38-40 validation
updates as the source of truth for claims, tables, limitations, and
reviewer-risk boundaries.

## Draft Files

- `outline.md`: paper structure, core thesis, contribution plan, figure/table plan.
- `abstract.md`: first paper abstract draft and claim-safe variants.
- `introduction.md`: motivation, research gap, hypothesis, and contributions.
- `method.md`: IntentWeight method description, including routes, LinUCB, trust
  feedback, geometry, and context compaction.
- `experiments.md`: dataset roles, protocol, main result tables, ablations, and
  interpretation.
- `limitations.md`: current boundaries that must remain visible in the paper.

## Current Writing Position

The paper should not claim that IntentWeight universally replaces dense
retrieval. The supported claim is narrower and stronger:

> IntentWeight is a feedback-driven adaptive retrieval controller for
> vertical-domain RAG. It uses dense, BM25, and cluster-local retrieval routes
> with trust-weighted LinUCB route learning and confidence-based final context
> compaction. On LoTTE technology/search up to 638k corpus chunks, the
> conservative policy reduces final retrieved context tokens by about 4.7-5.3%
> while preserving dense-level Hit@10.

The strengthened post-review position adds three bounded claims:

- Calibration/test validation shows that frozen context-budget policies can
  save 6-18% final evidence-context tokens while avoiding the Hit@10 losses
  seen in dense-only adaptive truncation.
- LoTTE science/search provides cross-domain ranking support, but also shows
  that final-context compression strength must be domain calibrated.
- Feedback-driven hard-case recovery can repair a meaningful fraction of
  budget-induced tail failures in post-feedback retry; this is recovery
  evidence, not first-pass IID dominance.

## Evidence Sources

- Evidence package: `paper/experiments/task31_paper_evidence_package.md`
- Token-quality frontier: `paper/experiments/task29_2_token_quality_frontier.md`
- Seed stability: `paper/experiments/results/task29_3_seed_variance_ci.md`
- Geometry validation: `paper/experiments/task30_lotte_geometry_scale_validation.md`
- Historical cost correction: `paper/experiments/task28_1_context_token_backfill_summary.md`
- Credit assignment: `paper/experiments/task25_credit_assignment_summary.md`
- Scale-up summary: `paper/experiments/task23_lotte_scaleup_summary.md`
- Pre-writing consistency audit:
  `paper/experiments/task33_7_pre_writing_consistency_audit.md`
- Multi-embedding robustness:
  `paper/experiments/task33_1a_multiqa_minilm_robustness_summary.md`
- LLM generation smoke:
  `paper/experiments/task33_5_llm_generation_smoke_summary.md`
- Five-seed 100k stability:
  `paper/experiments/task33_6_additional_seeds_summary.md`
- Review defense revision:
  `paper/experiments/task34_review_defense_revision_plan.md`
- Calibration/test context-budget validation:
  `paper/experiments/task38_calibrated_context_budget_validation.md`
- Cross-domain validation:
  `paper/experiments/task39_lotte_cross_domain_validation.md`
- Feedback-driven hard-case recovery:
  `paper/experiments/task40_feedback_recovery_summary.md`
