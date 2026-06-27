# Task51 Experiment Validation Framework

Updated: 2026-06-22

## Objective

Create a reusable validation layer for future experiment expansion. The goal is
not to rerun retrieval or generation, but to verify that generated artifacts are
dimensionally consistent, statistically sane, and usable for paper-facing
tables or summaries before they influence manuscript claims.

## Added Files

- `paper/experiments/task51_experiment_manifest.json`
- `paper/experiments/scripts/task51_experiment_validation.py`
- `paper/experiments/results/task51_experiment_validation_audit.csv`
- `paper/experiments/results/task51_experiment_validation_audit.json`
- `paper/experiments/results/task51_experiment_validation_audit.md`

## Default Coverage

The default manifest audits:

- Task38 LoTTE technology/search calibrated context-budget frontier at 100k,
  200k, 400k, and 638k.
- Task39 LoTTE science/search cross-domain context-budget validation at
  20k/q200 and 100k.
- Task46 Dense+Sentence-MMR same-budget baseline.
- Task47 cross-encoder reranker same-budget baseline.
- Task48 compressor-normalized Dense/IntentRoute comparison.
- Task52 BGE-base strong embedding dense baseline and Task38 held-out
  comparison.
- Task53 matched-backbone embedding generalization.
- Task54 BGE positive-hit operating point.
- Task55 backbone stability summary.
- Task58 geometry-random ablation.
- Task59 feedback-control ablation.
- Task60 arm-count sensitivity.
- Task61 geometry-to-control diagnostic synthesis.
- Task62 prompt-compression baseline.

## Checks

Dimension checks:

- processed query and corpus JSON shape where configured;
- expected query counts;
- duplicate query or chunk IDs;
- ground-truth chunk reference resolution where corpus scans are enabled;
- ranking artifact variant counts, ranked-query counts, query IDs, ranking
  lengths, duplicate ranking refs, and top-k chunk refs where configured.

Statistics checks:

- required paired CSV columns;
- finite numeric values;
- `method_hit@10 - baseline_hit@10 == hit_delta_mean`;
- confidence interval ordering around hit deltas and token savings;
- `token_saving_percent == (1 - token_ratio) * 100`;
- McNemar p-values and hit rates within `[0, 1]`;
- `num_queries` consistency against each experiment's expected held-out count.

Display checks:

- Markdown summary exists;
- top-level heading exists;
- at least one Markdown table is present;
- token-cost language is present.

## Current Audit Result

Command:

```bash
.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py
```

Result:

- PASS: 763
- WARN: 0
- ERROR: 0

The Task39 science/search processed datasets and Task53 matched-backbone
artifacts, plus the Task54 positive-hit operating point, Task55 backbone
stability summary, Task58 geometry-random ablation, and Task59
feedback-control ablation, Task60 arm-count sensitivity, and Task61
geometry-to-control diagnostic synthesis, and Task62 prompt-compression
baseline are now available locally and configured in the manifest. Task51
audits those runs with query count, ground-truth reference, top-k ranking
chunk-reference, paired-statistics, and display-readiness checks where
applicable.

## Usage For Future Experiments

For each new experiment, add a manifest entry with:

- a stable `id`;
- the experiment `role`;
- `expected_num_queries` for the evaluated split;
- dataset query/corpus paths when available;
- result JSON, summary CSV, paired CSV, ranking artifact, and Markdown summary
  paths as applicable.

Then run:

```bash
.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py \
  --experiments <experiment_id>
```

New experiment outputs should not be promoted into the manuscript until this
audit has no errors. Warnings are acceptable only when they are intentional and
documented, such as skipping large-corpus chunk-reference scans or auditing a
metrics-only artifact whose processed dataset is not local.

## Writing Policy

Task51 does not require immediate manuscript edits for every new experiment.
It creates a validation gate. Manuscript changes should be batched after a
group of experiments stabilizes or when new results change the paper's central
claim, baseline positioning, or limitation boundary.
