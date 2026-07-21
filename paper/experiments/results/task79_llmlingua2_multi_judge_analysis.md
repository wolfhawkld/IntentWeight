# Task79 LLMLingua-2 Multi-Judge Analysis

Status: **COMPLETE_THREE_JUDGE_ANALYSIS**

- Answers: `1200/1200`
- Valid judgments: `3600/3600`
- Missing judgments (not imputed): `0`
- Logged failure attempts: `456`; recovered keys: `440`
- Compressor peak allocated VRAM: `2.526 GiB`

## Context Endpoints

| method_label | queries | mean_context_tokens | mean_prompt_tokens | hit_at_10 | mean_target_error_tokens |
| --- | --- | --- | --- | --- | --- |
| dense_sent_mmr_r0.85_l0.70 | 300 | 1239.8000 | 2572.1133 | 0.8700 |  |
| intentweight_sent_mmr_r0.85_l0.70_seed19 | 300 | 1157.3800 | 2402.7467 | 0.8767 |  |
| dense_llmlingua2_matched_sent_mmr | 300 | 1259.2200 | 1640.3067 | 0.8700 | 19.4200 |
| intentroute_llmlingua2_matched_sent_mmr_seed19 | 300 | 1175.0200 | 1529.3233 | 0.8767 | 17.6400 |

## Primary Paired Comparison

| judge_scope | paired_queries | is_correct_delta_pp | is_correct_delta_ci_low_pp | is_correct_delta_ci_high_pp | is_correct_mcnemar_exact_p | is_faithful_delta_pp | citations_supported_delta_pp | context_token_saving_percent | prompt_token_saving_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash | 300 | 3.0000 | -1.0000 | 7.0000 | 0.1996 | 3.6667 | 0.3333 | 6.6867 | 6.7660 |
| glm-5.2 | 300 | 0.6667 | -3.3333 | 4.6667 | 0.8679 | 0.3333 | -1.0000 | 6.6867 | 6.7660 |
| minimax-m3 | 300 | 0.0000 | -3.6667 | 4.0000 | 1.0000 | -1.3333 | 0.0000 | 6.6867 | 6.7660 |
| three_judge_majority | 300 | 0.6667 | -3.0000 | 4.3333 | 0.8642 | 0.0000 | 0.3333 | 6.6867 | 6.7660 |

## Boundaries

- Judge scores are reported separately; raw score scales are not pooled.
- Majority results use only complete three-judge pairs; missing outputs are not imputed.
- Qualitative categories are candidates for manual review, not automatic causal findings.
- This tests route/compressor complementarity, not a geometry-to-compression causal path.
- Cross-compressor prompt-token deltas include sentence-versus-chunk header overhead; the matched context-token measure remains primary.
