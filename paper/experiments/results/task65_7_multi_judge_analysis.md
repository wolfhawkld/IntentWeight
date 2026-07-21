# Task65.7 Multi-Judge Analysis

This is an offline analysis of the fixed 2,100 Task63 answers; no answers were regenerated.

## Coverage

| judge | valid | coverage_percent | missing |
| --- | --- | --- | --- |
| deepseek-v4-flash | 2100 | 100.0000 | 0 |
| glm-5.2 | 2100 | 100.0000 | 0 |
| minimax-m3 | 2072 | 98.6667 | 28 |

Cross-judge analyses use the `2072` query-method keys valid for all three judges.
MiniMax missing judgments are not imputed.

## Judge-Level Distribution

| judge | correctness_mean | is_correct | faithfulness_mean | is_faithful | citations_supported |
| --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash | 4.6719 | 0.9133 | 4.7824 | 0.9310 | 0.8957 |
| glm-5.2 | 4.5505 | 0.8824 | 4.7343 | 0.9281 | 0.9214 |
| minimax-m3 | 4.2920 | 0.8567 | 4.6318 | 0.9542 | 0.9445 |

Absolute score calibration differs by judge, so raw scores are not pooled across models.

## Pairwise Agreement On Shared Keys

| field | judge_left | judge_right | n | raw_agreement | cohen_kappa |
| --- | --- | --- | --- | --- | --- |
| is_correct | deepseek-v4-flash | glm-5.2 | 2072 | 0.9102 | 0.5086 |
| is_correct | deepseek-v4-flash | minimax-m3 | 2072 | 0.8986 | 0.5038 |
| is_correct | glm-5.2 | minimax-m3 | 2072 | 0.9218 | 0.6556 |
| is_faithful | deepseek-v4-flash | glm-5.2 | 2072 | 0.9170 | 0.3623 |
| is_faithful | deepseek-v4-flash | minimax-m3 | 2072 | 0.9329 | 0.3794 |
| is_faithful | glm-5.2 | minimax-m3 | 2072 | 0.9339 | 0.4029 |

## Three-Judge Consensus

| field | n | unanimous_rate | majority_positive_rate | all_positive_rate | all_negative_rate |
| --- | --- | --- | --- | --- | --- |
| is_correct | 2072 | 0.8653 | 0.8890 | 0.8152 | 0.0502 |
| is_faithful | 2072 | 0.8919 | 0.9532 | 0.8764 | 0.0154 |

## Within-Judge Paired Comparisons

| judge_model | comparison | paired_queries | correct_delta_pp | correct_delta_ci_low_pp | correct_delta_ci_high_pp | mcnemar_exact_p | faithful_delta_pp | faithful_mcnemar_exact_p | context_token_saving_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash | BGE IntentRoute vs BGE dense | 300 | 0.0000 | -2.6667 | 2.6667 | 1.0000 | -2.3333 | 0.2295 | 6.0005 |
| deepseek-v4-flash | E5 IntentRoute vs E5 dense | 300 | 0.3333 | -3.0000 | 3.6667 | 1.0000 | 0.3333 | 1.0000 | 12.0358 |
| deepseek-v4-flash | IntentRoute+SentMMR vs Dense+SentMMR | 300 | 2.3333 | -1.6667 | 6.3333 | 0.3240 | 1.6667 | 0.4996 | 6.6478 |
| glm-5.2 | BGE IntentRoute vs BGE dense | 300 | -3.0000 | -6.3333 | 0.3333 | 0.1078 | -3.6667 | 0.0614 | 6.0005 |
| glm-5.2 | E5 IntentRoute vs E5 dense | 300 | -1.3333 | -5.0000 | 2.3333 | 0.5966 | -2.6667 | 0.2295 | 12.0358 |
| glm-5.2 | IntentRoute+SentMMR vs Dense+SentMMR | 300 | 0.3333 | -3.6667 | 4.3333 | 1.0000 | 1.0000 | 0.7283 | 6.6478 |
| minimax-m3 | BGE IntentRoute vs BGE dense | 289 | -2.4221 | -5.8824 | 1.0381 | 0.2478 | -2.4221 | 0.1185 | 6.2710 |
| minimax-m3 | E5 IntentRoute vs E5 dense | 289 | -2.7682 | -6.9204 | 1.0381 | 0.2295 | -1.0381 | 0.6776 | 11.9676 |
| minimax-m3 | IntentRoute+SentMMR vs Dense+SentMMR | 300 | 1.3333 | -2.6667 | 5.3333 | 0.6358 | 3.3333 | 0.0639 | 6.6478 |
| three_judge_majority | BGE IntentRoute vs BGE dense | 289 | -3.4602 | -6.9204 | 0.0000 | 0.0755 | -4.1522 | 0.0018 | 6.2710 |
| three_judge_majority | E5 IntentRoute vs E5 dense | 289 | -2.0761 | -5.8824 | 1.7301 | 0.3616 | -0.6920 | 0.8238 | 11.9676 |
| three_judge_majority | IntentRoute+SentMMR vs Dense+SentMMR | 300 | 0.3333 | -3.3333 | 4.0000 | 1.0000 | 3.6667 | 0.0522 | 6.6478 |

## Interpretation Boundary

- Report each judge separately and use within-judge paired comparisons; do not pool raw scores.
- Use `is_correct` and `is_faithful` for primary agreement analysis.
- Correctness differences are non-significant, but majority-vote faithfulness decreases for BGE and increases for the SentMMR composition.
- Exclude `insufficient_context_appropriate` from headline evidence because its rubric was under-specified.
- Multi-judge agreement is robustness evidence for answer-level evaluation, not human evaluation.
