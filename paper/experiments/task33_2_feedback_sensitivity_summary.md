# Task33.2 Feedback Simulation Sensitivity Summary

Updated: 2026-05-26

Task33.2 tests whether the feedback-driven LinUCB component depends on one
hand-tuned feedback setting. The experiment uses the main paper evidence model,
`sentence-transformers/all-MiniLM-L6-v2`, on LoTTE technology/search 100k under
the same prequential cost-aware routing protocol used by the main evidence
chain.

The goal is not to claim that simulated feedback is equivalent to real human
feedback. The goal is narrower: verify whether the policy-learning mechanism is
sensitive to feedback quality in the expected direction, and whether
trust-weighted feedback is more stable than equal noisy feedback under
controlled noise.

## Protocol

All variants use:

- dataset: `lotte_technology_search_100k`;
- query split: `test`;
- model: `sentence-transformers/all-MiniLM-L6-v2`;
- seeds: `13,17,19`;
- epochs: `8`;
- routing mode: `gated_cost_aware`;
- reward attribution: `cluster_only`;
- confidence mode: `value`;
- final context policy: `confidence_topk`;
- no leakage prequential evaluation: each query is ranked before its feedback
  is used for later updates.

The sensitivity matrix includes:

- `none`: no feedback; effectively relies on dense/full fallback;
- `oracle`: clean upper-bound feedback;
- `equal_default`: noisy feedback without trust weighting;
- `trust_default`: same default noisy setting with trust weighting;
- `trust_mild`: trust-weighted feedback with milder noise;
- `trust_strong`: trust-weighted feedback under severe noise.

## Route-Learning Results

| Feedback setting | Hit@10 | Last true reward | Selected cluster hit | Source candidate cost | Final k | Dense rate | LinUCB primary |
|---|---:|---:|---:|---:|---:|---:|---:|
| none | 0.8826 | 0.1516 | 0.1553 | 300.00 | 10.00 | 1.0000 | 0.0000 |
| oracle | 0.8758 | 0.8932 | 0.8386 | 160.27 | 8.87 | 0.4345 | 0.5655 |
| equal_default | 0.8641 | 0.7517 | 0.5979 | 185.53 | 9.50 | 0.7480 | 0.2520 |
| trust_default | 0.8641 | 0.8328 | 0.7223 | 181.47 | 9.34 | 0.6708 | 0.3292 |
| trust_mild | 0.8775 | 0.8820 | 0.7908 | 173.30 | 9.17 | 0.5826 | 0.4174 |
| trust_strong | 0.8479 | 0.5912 | 0.4813 | 187.48 | 9.73 | 0.8670 | 0.1330 |

Interpretation:

- `none` has high Hit@10 because the policy never learns a useful route and
  falls back to dense/full context. It is a quality floor, not evidence of
  self-evolution.
- `oracle` gives the clean upper bound: with reliable feedback, LinUCB learns a
  much better route policy, selected-cluster hit rises to `0.8386`, dense usage
  falls to `0.4345`, and source candidate cost falls from `300.00` to `160.27`.
- `trust_default` and `equal_default` have the same final Hit@10, but
  trust-weighting substantially improves the policy internals: last true reward
  rises from `0.7517` to `0.8328`, selected-cluster hit rises from `0.5979` to
  `0.7223`, dense usage falls from `0.7480` to `0.6708`, and source candidate
  cost falls from `185.53` to `181.47`.
- `trust_mild` is the strongest realistic controlled-noise setting. It reaches
  Hit@10 `0.8775`, last true reward `0.8820`, selected-cluster hit `0.7908`,
  dense rate `0.5826`, and source candidate cost `173.30`.
- `trust_strong` degrades the policy. This is an expected limitation: if
  feedback is severely unreliable, trust weighting and fallback reduce but do
  not eliminate the damage.

## Final Context Token Results

The token table measures final retrieved chunk text at top-10. It does not count
system prompts, generation output, reranker internals, or retrieval-stage
candidate counts.

| Feedback setting | Hit@10 | Avg context tokens@10 | Token ratio vs dense | Hit delta vs dense |
|---|---:|---:|---:|---:|
| dense | 0.8674 | 1472.39 | 1.0000 | 0.0000 |
| none | 0.8826 | 1561.15 | 1.0603 | +0.0151 |
| oracle | 0.8758 | 1327.03 | 0.9013 | +0.0084 |
| equal_default | 0.8641 | 1423.84 | 0.9670 | -0.0034 |
| trust_default | 0.8641 | 1399.51 | 0.9505 | -0.0034 |
| trust_mild | 0.8775 | 1362.68 | 0.9255 | +0.0101 |
| trust_strong | 0.8479 | 1448.43 | 0.9837 | -0.0196 |

Interpretation:

- Clean and mild trust-weighted feedback can preserve or improve Hit@10 while
  reducing final context tokens.
- `trust_mild` is the most useful paper-facing sensitivity point: compared with
  dense, it improves Hit@10 by `+1.01` percentage points while reducing final
  context tokens by about `7.45%`.
- `equal_default` and `trust_default` both remain near dense in Hit@10, but
  trust-weighting has better token and policy efficiency.
- Severe feedback noise weakens both route learning and final retrieval quality,
  so the paper should explicitly motivate user trust scoring, conservative
  fallback, and feedback denoising as required deployment components.

## Paper-Facing Conclusion

Task33.2 supports the feedback self-evolution claim, but only in the bounded
form that the paper has been converging toward:

> Under controlled simulated feedback, LinUCB route learning improves in the
> expected direction as feedback quality improves. Trust-weighted feedback makes
> the adaptive policy more stable than equal noisy feedback, improving route
> reward, selected-cluster hit rate, dense fallback reduction, and final context
> token efficiency. The result does not prove real human-feedback deployment;
> it validates the mechanism under a no-leakage controlled simulation.

The result should be used as sensitivity analysis, not as a claim that feedback
always improves final Hit@10. The strongest evidence is the monotonic policy
behavior across `none`, noisy, trust-weighted, mild, oracle, and strong-noise
conditions.

## Artifacts

- Route summaries:
  - `paper/experiments/results/task33_2_feedback_none/`
  - `paper/experiments/results/task33_2_feedback_oracle/`
  - `paper/experiments/results/task33_2_feedback_equal_default/`
  - `paper/experiments/results/task33_2_feedback_trust_default/`
  - `paper/experiments/results/task33_2_feedback_trust_mild/`
  - `paper/experiments/results/task33_2_feedback_trust_strong/`
- Final context token comparison:
  - `paper/experiments/results/task33_2_feedback_sensitivity_context_tokens.csv`
  - `paper/experiments/results/task33_2_feedback_sensitivity_context_tokens.json`
  - `paper/experiments/results/task33_2_feedback_sensitivity_context_tokens.md`
