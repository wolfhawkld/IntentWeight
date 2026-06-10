# Task38 Calibrated Context-Budget Validation

## Goal

Task38 addresses a reviewer-facing risk in Task37: the strong
`token_budget_r0.95_m5` operating point was selected after inspecting the main
LoTTE test results. Even without per-query leakage, this can introduce
test-set model-selection bias.

Task38 therefore uses a deterministic calibration/test protocol:

1. split the 596 LoTTE held-out queries into 179 calibration queries and 417
   frozen test queries;
2. choose the token-budget policy only on calibration queries;
3. freeze the selected policy;
4. report dense-vs-method paired statistics only on frozen test queries.

The split is deterministic by query id and scale-specific salt. The retrieval
rankings are the same saved dense and gated fixed top-10 rankings from Task37;
Task38 does not rerun embedding, dense retrieval, or LinUCB.

## Selection Rule

Candidate policies are:

```text
budget ratios: 0.98, 0.95, 0.92, 0.90, 0.88, 0.85
min_keep:      4, 5, 6, 7, 8
```

The default Task38 selection rule is intentionally stricter than the reporting
non-inferiority margin:

- selection requires calibration mean Hit@10 delta vs dense `>= 0`;
- among eligible policies, select the largest final context-token saving;
- if no policy is eligible, select the policy with the highest calibration
  Hit@10 delta, then highest token saving.

The frozen test still reports the standard `1pp` non-inferiority CI check for
comparison with Task37-C.

## Frozen Test Results

All values below are averaged over three LinUCB seeds on the frozen test split.
Token saving is final LLM evidence-context input token saving relative to dense
top-10.

| Scale | Selected policy | Calibration eligible | Task38 Hit delta | Task38 token saving | Task38 NI seeds | Dense adaptive Hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 6.18% | 0/3 | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 16.00% | 1/3 | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False | +2.32 pp | 6.57% | 3/3 | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 17.53% | 0/3 | -3.84 pp | 21.90% |

## Interpretation

Task38 strengthens the paper in two ways.

First, it confirms that the main context-cost finding is not merely a dense
top-k truncation effect. Dense adaptive truncation usually saves more tokens,
but it loses Hit@10 on every scale. Task38 keeps substantially better Hit@10 at
a still meaningful context-token saving level.

Second, it gives a cleaner answer to test-set selection bias. Once the policy is
selected on calibration queries and frozen before test evaluation, Task38 still
preserves dense-level average Hit@10 on 100k, 200k, and 638k, and exceeds dense
on 400k. The best frozen test trade-off is scale-dependent:

- 100k: conservative frozen policy, modest saving, dense-level mean Hit@10;
- 200k: aggressive frozen policy, strong saving and above-dense mean Hit@10;
- 400k: no no-drop calibration policy exists, so the fallback chooses the
  highest-calibration-Hit policy; frozen test is nevertheless strongly positive;
- 638k: aggressive frozen policy saves about 17.5% context tokens with nearly
  dense-level average Hit@10, but strict CI non-inferiority is not proven.

The result should therefore be written as:

> Under a calibration/test protocol, IntentWeight's budgeted final-context
> policy consistently outperforms dense-only adaptive truncation and can reduce
> final LLM evidence-context input tokens while maintaining dense-level average
> sufficient-evidence Hit@10. Strict seed-level non-inferiority remains
> scale-dependent and should be reported transparently.

This is a stronger and more defensible claim than the earlier Task37-only
statement, but it also narrows the wording: the paper should not claim universal
statistical non-inferiority for every seed and scale.

## Artifacts

- `paper/experiments/scripts/task38_calibrated_context_budget.py`
- `paper/experiments/results/task38_100k_calibrated_context_budget.md`
- `paper/experiments/results/task38_200k_calibrated_context_budget.md`
- `paper/experiments/results/task38_400k_calibrated_context_budget.md`
- `paper/experiments/results/task38_638k_calibrated_context_budget.md`

Each scale also has `.json`, `.calibration.csv`, `.test_paired.csv`, and
`.rankings.json` artifacts under `paper/experiments/results/`.

## Paper Use

Task38 should be used as a reviewer-defense experiment in the main paper or
appendix:

- cite Task37 as the full held-out query result and stronger initial frontier;
- cite Task38 to show that the conclusion survives a cleaner
  calibration/test split;
- show dense adaptive truncation as a necessary same-budget/truncation baseline;
- keep the headline centered on final LLM context input cost and query-level
  sufficient-evidence Hit@10, not complete evidence collection.
