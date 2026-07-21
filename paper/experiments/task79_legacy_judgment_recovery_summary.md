# Task79 Legacy MiniMax Judgment Recovery Summary

Status: complete

Date: 2026-07-21

## Scope

Seven MiniMax-M3 judgments were missing for the two reused Sentence-MMR
endpoints in the Task79 300-query subset. The retry reused the exact stored
answers, reference evidence, judge instructions, user prompt construction,
model identifier, temperature, and JSON schema. Existing valid judgments were
skipped and never overwritten.

The first retry retained the original 900-token completion cap and recovered
five judgments. The two remaining requests returned incomplete/empty content
rather than a new content-filter rejection. A second technical retry changed
only the completion cap to 2,048 tokens and recovered both. Prior provider
failures remain in the failure log; no rejected output is interpreted as a
negative judgment and no value is imputed.

## Result

- Task79 valid judgments: `3,600/3,600`.
- Each of DeepSeek, GLM-5.2, and MiniMax-M3: `1,200/1,200`.
- Task79 local gate: `14/14`, status `PASS_COMPLETE`.
- The seven recovered rows were synchronized to the canonical Task63 artifact
  only after exact answer-payload equality was verified.
- Task63 valid judgments increase from `6,265` to `6,272`; its remaining
  MiniMax missingness decreases from `35` to `28` keys across 17 queries.

## Statistical Effect

The primary Task79 IntentRoute+LLMLingua-2 versus Dense+LLMLingua-2 comparison
is unchanged because it already had complete three-judge coverage.

The historical Sentence-MMR comparison now uses 300 rather than 295 complete
MiniMax/majority query pairs. Its three-judge-majority correctness delta is
`+0.33pp` (95% CI `[-3.33,+4.00]pp`, exact McNemar `p=1.0000`) with `6.65%`
context-token saving (95% CI `[4.19%,8.97%]`). The majority faithfulness point
estimate is `+3.67pp` (95% CI `[+0.33,+7.00]pp`), but exact McNemar
`p=0.0522`; it is therefore no longer reported as significant at the 0.05
level. The significant negative BGE faithfulness boundary remains unchanged.

## Claim Boundary

Recovery removes legacy missingness from the four-endpoint Task79 analysis but
does not strengthen its causal or non-inferiority claim. The result still
supports lower context without a statistically detected correctness change in
one frozen, automated-judge setting. The remaining 28 Task63 MiniMax failures
outside the Task79 Sentence-MMR subset stay explicit and are not imputed.

## Artifacts

- `paper/experiments/scripts/task79_sync_legacy_judgments.py`
- `paper/experiments/results/task79_legacy_judgment_recovery.json`
- `paper/experiments/results/task63_downstream_llm_evaluation/judgments.jsonl`
- `paper/experiments/results/task79_llmlingua2_downstream_evaluation/judgments.jsonl`
- `paper/experiments/results/task65_7_multi_judge_analysis.*`
- `paper/experiments/results/task79_llmlingua2_multi_judge_analysis.*`
- `paper/experiments/results/task79_local_validation.{json,md}`
