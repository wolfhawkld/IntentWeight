# Task51 Experiment Validation Audit

- Manifest: `paper/experiments/task51_experiment_manifest.json`
- Total checks: 921
- PASS: 921
- WARN: 0
- ERROR: 0

## Experiment Status

| experiment | status | pass | warn | error |
| --- | --- | ---: | ---: | ---: |
| task38_lotte_technology_100k_context_budget | PASS | 18 | 0 | 0 |
| task38_lotte_technology_200k_context_budget | PASS | 16 | 0 | 0 |
| task38_lotte_technology_400k_context_budget | PASS | 16 | 0 | 0 |
| task38_lotte_technology_638k_context_budget | PASS | 16 | 0 | 0 |
| task39_lotte_science_100k_context_budget | PASS | 18 | 0 | 0 |
| task39_lotte_science_20k_q200_context_budget | PASS | 18 | 0 | 0 |
| task46_sentence_mmr_same_budget | PASS | 25 | 0 | 0 |
| task47_cross_encoder_reranker | PASS | 25 | 0 | 0 |
| task48_compressor_normalized_comparison | PASS | 25 | 0 | 0 |
| task52_bge_base_100k_dense_all_queries | PASS | 13 | 0 | 0 |
| task52_bge_base_100k_task38_test_comparison | PASS | 19 | 0 | 0 |
| task53_bge_base_100k_full_context_budget | PASS | 18 | 0 | 0 |
| task53_bge_base_100k_gated_context_budget | PASS | 18 | 0 | 0 |
| task53_e5_base_100k_dense_all_queries | PASS | 13 | 0 | 0 |
| task53_e5_base_100k_full_context_budget | PASS | 18 | 0 | 0 |
| task53_e5_base_100k_gated_context_budget | PASS | 18 | 0 | 0 |
| task53_embedding_backbone_generalization_summary | PASS | 7 | 0 | 0 |
| task54_bge_base_100k_positive_hit_context_budget | PASS | 18 | 0 | 0 |
| task55_backbone_stability_summary | PASS | 13 | 0 | 0 |
| task58_geometry_random_ablation | PASS | 44 | 0 | 0 |
| task59_feedback_control_ablation | PASS | 106 | 0 | 0 |
| task60_arm_count_sensitivity | PASS | 250 | 0 | 0 |
| task61_geometry_to_control_analysis | PASS | 6 | 0 | 0 |
| task62_prompt_compression_baseline | PASS | 25 | 0 | 0 |
| task63_downstream_llm_evaluation | PASS | 25 | 0 | 0 |
| task65_1_safe_compression_attribution | PASS | 24 | 0 | 0 |
| task65_2_factorial_safe_compression | PASS | 26 | 0 | 0 |
| task65_3_dynamic_route_mediation | PASS | 20 | 0 | 0 |
| task65_4_matched_frontier | PASS | 20 | 0 | 0 |
| task65_5_calibration_split_sensitivity | PASS | 13 | 0 | 0 |
| task65_6_cross_scale_cross_fitted_calibration | PASS | 13 | 0 | 0 |
| task65_7_multi_judge_analysis | PASS | 17 | 0 | 0 |

## Category Status

| category | status | pass | warn | error |
| --- | --- | ---: | ---: | ---: |
| dimension | PASS | 469 | 0 | 0 |
| display | PASS | 159 | 0 | 0 |
| statistics | PASS | 293 | 0 | 0 |

## Warnings And Errors

No warnings or errors.

## Interpretation

- Dimension checks cover dataset/query shape, ranking variants, query coverage, and chunk-reference resolution where configured.
- JSONL checks stream answer and judgment records while enforcing counts, schemas, and configured key cardinalities.
- Statistics checks cover paired-result arithmetic, confidence interval ordering, p-value ranges, token-ratio consistency, and configured heterogeneous analysis tables.
- Display checks cover paper-facing Markdown reports; they do not judge visual aesthetics.
- Large corpus checks can skip full corpus-reference scans by manifest to keep this audit lightweight.
