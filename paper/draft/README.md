# IntentWeight Paper Draft

Updated: 2026-05-25

This directory starts the paper-writing phase after Task31 consolidated the
experimental evidence. The draft uses
`paper/experiments/task31_paper_evidence_package.md` and the Task33.7
pre-writing audit as the source of truth for claims, tables, limitations, and
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
> while preserving near- or above-dense Hit@10.

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
