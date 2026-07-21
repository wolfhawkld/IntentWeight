# Task65.7 Multi-Judge Answer Evaluation Summary

Task65.7 is complete as an offline robustness analysis of the fixed Task63
answer set.

## Protocol

The analysis reuses the 2,100 answers generated for 300 frozen LoTTE
technology/search queries and seven retrieval/context methods. Answers are not
regenerated. Three independent LLM judges evaluate the same answer artifacts:

- DeepSeek `deepseek-v4-flash`;
- `glm-5.2` through Volcengine Agent Plan;
- `minimax-m3` through Volcengine Agent Plan.

Model-specific distributions use every valid judgment from that model.
Cross-judge agreement and three-judge majority analyses use only the 2,072
query-method keys valid for all judges. Raw ordinal scores are not pooled across
judges. Within-judge method comparisons use query-paired bootstrap intervals
with 10,000 deterministic resamples and exact McNemar tests for binary
correctness.

## Coverage

| Judge | Valid judgments | Coverage | Missing |
| --- | ---: | ---: | ---: |
| DeepSeek | 2,100 | 100.00% | 0 |
| GLM-5.2 | 2,100 | 100.00% | 0 |
| MiniMax-M3 | 2,072 | 98.67% | 28 |

The 28 remaining MiniMax-M3 omissions span 17 queries and remain unavailable
after provider-side content filtering. No values are imputed. Repeated failed attempts remain in
the failure log, while the paper-facing missingness count uses unique
query-method-judge keys.

## Judge Calibration And Agreement

| Judge | Correctness mean | Correct | Faithfulness mean | Faithful | Citations supported |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek | 4.672 | 91.33% | 4.782 | 93.10% | 89.57% |
| GLM-5.2 | 4.551 | 88.24% | 4.734 | 92.81% | 92.14% |
| MiniMax-M3 | 4.292 | 85.67% | 4.632 | 95.42% | 94.45% |

The models differ in absolute calibration: DeepSeek assigns more top-end
correctness scores, while MiniMax-M3 uses score 4 more often. On the common
2,072 keys, pairwise raw agreement is 89.86--92.18% for `is_correct` and
91.70--93.39% for `is_faithful`. Pairwise Cohen's kappa is 0.504--0.656 for
correctness and 0.362--0.403 for faithfulness. The lower faithfulness kappa
coexists with high raw agreement because positive faithfulness judgments are
very prevalent.

Three-judge unanimity is 86.53% for correctness and 89.19% for faithfulness.
Majority-positive rates are 88.90% and 95.32%, respectively. These results
support answer-level robustness across judge choices, but they do not turn
LLM-as-judge evaluation into human evaluation.

## Matched Method Comparisons

All individual-judge and majority-vote correctness intervals include zero, and
all correctness McNemar p-values exceed 0.05.

| Evaluator | BGE delta | E5 delta | SentMMR delta |
| --- | ---: | ---: | ---: |
| DeepSeek | +0.00 pp | +0.33 pp | +2.33 pp |
| GLM-5.2 | -3.00 pp | -1.33 pp | +0.33 pp |
| MiniMax-M3 | -2.42 pp | -2.77 pp | +1.33 pp |
| Three-judge majority | -3.46 pp | -2.08 pp | +0.33 pp |

The corresponding context-token savings remain approximately 6.0% for BGE,
12.0% for E5, and 6.6--6.7% for the SentMMR composition. The three-judge
majority BGE interval is `[-6.92, 0.00] pp` with McNemar `p=0.0755`; this is not
a statistically significant difference, but it is close enough to require an
explicit non-inferiority caveat. The E5 majority interval is
`[-5.88, +1.73] pp`, and the SentMMR majority interval is
`[-3.33, +4.00] pp`.

Faithfulness is mixed rather than uniformly preserved. The three-judge
majority estimates a `-4.15pp` BGE faithfulness delta
(`95% CI [-6.92, -1.73]pp`, exact McNemar `p=0.0018`) and a `+3.67pp`
SentMMR-composition delta (`95% CI [+0.33, +7.00]pp`, `p=0.0522`).
MiniMax-M3 reports a positive SentMMR faithfulness point estimate
(`+3.33pp`, `p=0.0639`), while no individual-judge SentMMR faithfulness
comparison reaches `p<0.05`. The paper must therefore separate correctness
from faithfulness and retain the BGE boundary result.

## Claim Boundary

Task65.7 supports the bounded statement that no matched comparison shows a
statistically detectable correctness difference under any individual judge or
the three-judge majority, while every matched method uses fewer final-context
tokens. It does not establish strict answer-level non-inferiority, uniform
faithfulness preservation, significant answer-quality improvement, or
judge-independent absolute scores. Negative BGE/E5 correctness point estimates
from the stricter judges and the BGE majority-vote faithfulness decrease must
remain visible.

The field `insufficient_context_appropriate` is excluded from headline and
agreement evidence. Its true rate varies from 16.51% to 78.24% because the
judge prompt did not operationally define how to score sufficient-context
answers. The field is retained in raw artifacts for auditability.

## Artifacts

- `paper/experiments/scripts/task65_7_multi_judge_analysis.py`
- `paper/experiments/results/task65_7_multi_judge_analysis.json`
- `paper/experiments/results/task65_7_multi_judge_analysis.md`
- `paper/experiments/results/task65_7_multi_judge_analysis.judges.csv`
- `paper/experiments/results/task65_7_multi_judge_analysis.agreement.csv`
- `paper/experiments/results/task65_7_multi_judge_analysis.consensus.csv`
- `paper/experiments/results/task65_7_multi_judge_analysis.majority.csv`
- `paper/experiments/results/task65_7_multi_judge_analysis.paired.csv`
- `paper/experiments/results/task65_7_multi_judge_analysis.missingness.csv`
