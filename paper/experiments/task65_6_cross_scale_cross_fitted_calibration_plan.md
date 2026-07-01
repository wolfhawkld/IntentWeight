# Task65.6 Cross-Scale Cross-Fitted Calibration Plan

## Status

Protocol locked before the formal run.

## Motivation

The original 400k calibration split did not contain an IntentRoute budget
policy with non-negative mean calibration Hit@10 delta, although the frozen
test result was positive. Task65.5 subsequently found that 16 of 20 overlapping
30/70 splits were calibration-eligible, but policy selection remained mixed.
This follow-up evaluates the 400k operating point with disjoint out-of-fold
testing instead of searching for a favorable replacement split. To keep the
scale comparison normalized, the identical protocol is run at 100k, 200k,
400k, and 638k rather than only on the problematic 400k row.

## Locked Protocol

- Dataset: LoTTE technology/search at 100k, 200k, 400k, and 638k corpus
  chunks, using the same labeled-query set available at each scale.
- Inputs: frozen Task37 IntentRoute rankings for seeds 13, 17, and 19, plus the
  shared frozen Dense ranking.
- Query partition: five deterministic, balanced, disjoint folds. Assignment is
  obtained by sorting SHA-256 hashes of canonical LoTTE source query IDs
  (`metadata.original_query_id`) under the fixed salt
  `task65_6_cross_scale_crossfit_v1` and assigning sorted positions round-robin.
  The same source query is therefore held out in the same fold at every corpus
  scale even though processed query IDs contain scale-specific prefixes.
- For each outer fold, the other four folds are calibration data and the held
  fold is test data.
- Candidate final-context policies use the original Task38 grid at every scale:
  ratios `{0.98, 0.95, 0.92, 0.90, 0.88, 0.85}` and minimum prefixes
  `{4, 5, 6, 7, 8}`. No 400k-only candidate is added.
- Dense and IntentRoute select policies independently on each calibration
  partition.
- Eligibility rule: mean calibration Hit@10 delta relative to Dense top-10 must
  be non-negative, up to the existing numerical tolerance of `1e-12`.
- Selection objective among eligible policies: maximize final-context token
  saving, with calibration Hit delta as the tie-breaker.
- If no IntentRoute policy is eligible in a fold, that fold uses Dense top-10 as
  the declared safety fallback. Independently calibrated Dense uses the same
  fallback rule. The eligibility margin will not be relaxed after observing
  results.
- Each query contributes to held-out evaluation exactly once. Out-of-fold
  rankings are compared with Dense top-10 using query-level paired bootstrap,
  exact McNemar testing, and final-context token statistics.
- Strict non-inferiority uses the existing one-percentage-point Hit@10 margin
  and is reported per IntentRoute seed; it is not inferred from the seed mean.

## Interpretation Guardrails

- Reusing frozen rankings reuses shared intermediate model outputs, not prior
  calibration or test statistics.
- This is a post-hoc follow-up protocol and does not erase the original 400k
  calibration failure.
- Cross-scale rows are directly comparable within this follow-up because they
  share the same folds, grid, seeds, selection rule, cost metric, and tests.
- A positive result may upgrade 400k from a single-split diagnostic to
  cross-fitted robustness evidence, but it does not establish universal or
  split-invariant non-inferiority.
- A negative or mixed result remains a valid boundary result and will be
  retained without tuning the protocol.

## Expected Artifacts

- `results/task65_6_cross_scale_cross_fitted_calibration.folds.csv`
- `results/task65_6_cross_scale_cross_fitted_calibration.paired.csv`
- `results/task65_6_cross_scale_cross_fitted_calibration.rankings.json`
- `results/task65_6_cross_scale_cross_fitted_calibration.json`
- `results/task65_6_cross_scale_cross_fitted_calibration.md`
