# Task63 Expanded Downstream LLM Evaluation

Task63 is complete as a formal answer-level RAG evaluation.

Task65.7 subsequently extends the fixed 2,100-answer artifact with GLM-5.2 and
MiniMax-M3 judges. Use
`task65_7_multi_judge_analysis_summary.md` for current paper-facing
cross-judge claims; retain this file as the original DeepSeek-judge result.

## Scope

- Dataset: LoTTE technology search 100k.
- Split: 300 deterministic queries from the 417-query Task38 frozen test split.
- Generator and judge: DeepSeek `deepseek-v4-flash`.
- Coverage: 7 retrieval/context methods, 2,100 generated answers, and 2,100
  complete judge records.
- Validation: every answer and judgment has a unique query-method key; all
  judgment records contain the required schema. Failed parse attempts are kept
  separately in `judgment_failures.jsonl` for auditability.

Result directory:

- `paper/experiments/results/task63_downstream_llm_evaluation/`

## Formal Results

| Method | Correct | Faithful | Strict citation support | Insufficient context | Avg. context tokens | Tokens / correct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM dense top-10 | 0.9200 | 0.9533 | 0.3533 | 0.0967 | 1461 | 1588 |
| BGE dense top-10 | 0.9167 | 0.9433 | 0.3567 | 0.0767 | 1698 | 1852 |
| BGE positive IntentWeight | 0.9167 | 0.9200 | 0.3700 | 0.0767 | 1596 | 1741 |
| E5 dense top-10 | 0.9167 | 0.9300 | 0.4100 | 0.0700 | 1525 | 1663 |
| E5 full IntentWeight | 0.9200 | 0.9333 | 0.3633 | 0.0567 | 1341 | 1458 |
| Dense + SentMMR | 0.8900 | 0.9100 | 0.0733 | 0.0800 | 1240 | 1393 |
| IntentWeight + SentMMR | 0.9133 | 0.9267 | 0.0833 | 0.0900 | 1157 | 1267 |

## Paired Comparisons

All confidence intervals use 10,000 deterministic paired bootstrap samples over
the same 300 queries. Correctness p-values use the exact McNemar test.

| Matched comparison | Correctness delta | 95% CI | McNemar p | Context-token saving | 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: |
| BGE IntentWeight vs BGE dense | +0.00 pp | [-2.67, +2.67] pp | 1.000 | 6.00% | [4.01%, 7.97%] |
| E5 IntentWeight vs E5 dense | +0.33 pp | [-3.00, +3.67] pp | 1.000 | 12.04% | [9.93%, 14.16%] |
| IntentWeight+SentMMR vs Dense+SentMMR | +2.33 pp | [-1.67, +6.33] pp | 0.324 | 6.65% | [4.28%, 8.97%] |

Faithfulness deltas are respectively -2.33, +0.33, and +1.67 percentage
points; all three paired 95% intervals include zero. The BGE faithfulness point
estimate should therefore be reported as uncertainty, not hidden or described
as an improvement.

## Conclusion And Claim Boundary

Across all three matched comparisons, IntentWeight reduces final context tokens
with a positive paired 95% saving interval while no statistically detectable
correctness loss is observed. This supports the paper's cost-quality trade-off
claim at the downstream answer level and extends it across BGE, E5, and the
SentMMR composition.

The experiment does not establish a statistically significant answer-quality
gain: every correctness-delta interval includes zero. The defensible wording is
"preserves judged answer correctness while reducing context," not "improves
answer correctness." Strict citation support is an exact chunk-id diagnostic
and should remain secondary to judge faithfulness because sentence compression
changes citation granularity.

`estimated_context_cost_per_correct` remains zero in the machine summary because
no provider-specific input-token price was frozen. The provider-independent
`context_tokens_per_correct` metric is the formal cost proxy.
