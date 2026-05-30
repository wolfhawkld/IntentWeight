# Task36.4 Table and Figure Placement Plan

Updated: 2026-05-31

## Purpose

This task defines which results should appear in the main paper and which
should move to the appendix. It does not add new experiments. The goal is to
make the draft easier to convert into a formal paper without overloading the
main text with historical or diagnostic tables.

## Files Updated

- `paper/full_draft/11_table_figure_plan.md`
- `paper/full_draft/README.md`
- `paper/experiments/task_paper_use_status.md`

## Main-Paper Recommendation

Use the following core evidence package in the main paper:

1. dataset role and guardrail table;
2. LoTTE token-quality frontier table;
3. LoTTE 100k component ablation table;
4. compact feedback self-evolution table;
5. geometry diagnostics table only if space permits.

Use the following main figures:

1. IntentWeight system diagram;
2. token-quality frontier across corpus scale;
3. geometry diagnostic trend.

## Appendix Recommendation

Move these details to appendix or supplement:

- full seed intervals and five-seed extension;
- full static baseline metrics;
- source-candidate and dense-invocation diagnostics;
- secondary dataset details and boundary cases;
- encoder robustness details;
- downstream LLM generation smoke details;
- historical or superseded task artifacts.

## Internal Source Mapping

The draft-level placement plan avoids internal task labels in its paper-facing
descriptions. The internal source mapping is:

- token-quality frontier: `task29_2_token_quality_frontier.md` and
  `task29_confidence_context_policy_summary.md`;
- clean component ablation: `task33_3_clean_ablation_table.md`;
- feedback sensitivity: `task33_2_feedback_sensitivity_summary.md`;
- geometry scale diagnostics: `task30_lotte_geometry_scale_validation.md`;
- seed stability: `task29_3_seed_variance_ci.md` result table and
  `task33_6_additional_seeds_summary.md`;
- context-token correction audit: `task28_context_token_cost_summary.md` and
  `task28_1_context_token_backfill_summary.md`;
- secondary datasets and boundary cases:
  `task36_2_secondary_dataset_evidence.md`;
- encoder robustness: `task33_1_embedding_model_selection.md` and
  `task33_1a_multiqa_minilm_robustness_summary.md`;
- downstream generation smoke: `task33_5_llm_generation_smoke_summary.md`;
- historical/superseded guardrail: `task_paper_use_status.md`.

## Paper-Facing Decision

The main paper should prioritize the final context-token claim, component
attribution, feedback self-evolution, and bounded geometry diagnostics. Source
candidate cost, dense invocation rate, eManual/CUAD failure details, and
historical ablations remain useful but should not compete with the main
quality-token story in the body.
