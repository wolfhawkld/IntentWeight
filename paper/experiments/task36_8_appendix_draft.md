# Task36.8 Appendix Draft

Updated: 2026-05-31

## Purpose

This task creates a paper-facing appendix draft from existing supporting
evidence. It does not add new experiments or new claims. The appendix preserves
important reviewer-facing diagnostics without overloading the main paper.

## Files Added

- `paper/full_draft/12_appendix.md`

## Files Updated

- `paper/full_draft/06_results.md`
- `paper/full_draft/README.md`
- `paper/full_draft/11_table_figure_plan.md`
- `paper/experiments/task_paper_use_status.md`

## Appendix Structure

- Appendix A: multi-seed LoTTE stability diagnostics and five-seed 100k
  extension.
- Appendix B: static LoTTE BM25, dense, and hybrid baselines.
- Appendix C: source-candidate versus final context-token correction audit.
- Appendix D: PubMedQA, Banking77, eManual, and CUAD supporting/boundary
  evidence, including the eManual duplicate-text diagnostic.
- Appendix E: QA-tuned MiniLM-family encoder robustness check.
- Appendix F: downstream generation smoke test.
- Appendix G: reproducibility and reporting guardrails.

The main Results section now summarizes appendix-facing evidence and points to
the appendix instead of duplicating the detailed seed, secondary-dataset, and
generation-smoke tables.

## Internal Source Mapping

- Appendix A:
  - `results/task29_3_seed_variance_ci.md`
  - `task33_6_additional_seeds_summary.md`
- Appendix B:
  - `task23_lotte_scaleup_summary.md`
- Appendix C:
  - `task28_context_token_cost_summary.md`
  - `task28_1_context_token_backfill_summary.md`
- Appendix D:
  - `task36_2_secondary_dataset_evidence.md`
  - `results/retrieval_baseline_tables.md`
  - `results/emanual_failure_analysis_tables.md`
- Appendix E:
  - `task33_1a_multiqa_minilm_robustness_summary.md`
- Appendix F:
  - `task33_5_llm_generation_smoke_summary.md`
- Appendix G:
  - `task33_4_protocol_defense.md`
  - `task33_7_pre_writing_consistency_audit.md`

## Claim Guardrail

The appendix uses canonical paper-facing metric names. It does not reintroduce
historical source-candidate counts as token-cost evidence, mix Banking77 with
evidence-retrieval headline results, promote CUAD sampled smoke into a
full-corpus claim, or present simulated feedback as production validation.
