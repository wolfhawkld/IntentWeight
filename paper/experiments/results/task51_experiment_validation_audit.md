# Task51 Experiment Validation Audit

- Manifest: `paper/experiments/task51_experiment_manifest.json`
- Total checks: 209
- PASS: 209
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

## Category Status

| category | status | pass | warn | error |
| --- | --- | ---: | ---: | ---: |
| dimension | PASS | 108 | 0 | 0 |
| display | PASS | 30 | 0 | 0 |
| statistics | PASS | 71 | 0 | 0 |

## Warnings And Errors

No warnings or errors.

## Interpretation

- Dimension checks cover dataset/query shape, ranking variants, query coverage, and chunk-reference resolution where configured.
- Statistics checks cover paired-result arithmetic, confidence interval ordering, p-value ranges, and token-ratio consistency.
- Display checks cover paper-facing Markdown reports; they do not judge visual aesthetics.
- Large corpus checks can skip full corpus-reference scans by manifest to keep this audit lightweight.
