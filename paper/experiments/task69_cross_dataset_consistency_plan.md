# Task69 Cross-Dataset Experimental Consistency

Updated: 2026-07-12

## Objective

Task69 converts the tiered seven-setting narrative into a reviewer-readable
experimental matrix without pooling incompatible tasks. It addresses the valid
part of the Nemesis consistency review: the current artifacts are quantitative,
but their dimensions are too uneven for a reader to judge cross-dataset
generalization from one common table.

## Review Decision

The review's claim that PubMedQA, Banking77, eManual, and CUAD have no
quantitative results is obsolete. Their Dense, BM25, hybrid, route-policy,
geometry, or corrected-boundary artifacts exist and are already cited in the
current Results section. The remaining issue is protocol completeness, not
total absence of evidence.

The following review requests are adopted:

- add a centralized dataset/query/sampling inventory;
- define a minimum common protocol for comparable evidence-retrieval datasets;
- expose missing endpoints rather than treating historical results as
  equivalent;
- mark the 60-query generation smoke and early experiment draft as superseded;
- keep a machine-readable content-consistency audit.

The following requests are rejected or bounded:

- exploratory `pre_validation/` HDBSCAN and rule-based speech-act results are
  not promoted into the main paper because they use a different task and
  protocol and would weaken attribution;
- Banking77 is not pooled with evidence retrieval because it is an intent
  retrieval proxy;
- CUAD is not pooled because its current evidence is a sparse GT-anchored smoke
  sample;
- historical artifact identifiers remain `IntentWeight` for provenance, while
  paper-facing text remains `IntentRoute`.

## Task Breakdown

### Task69.1: Fact And Scope Audit

Status: complete.

- audited dataset scale, query count, GT semantics, sampling, and paper role;
- moved the superseded warning to the top of `paper/draft/experiments.md`;
- confirmed that current non-LoTTE quantitative artifacts exist;
- separated evidence retrieval, intent routing, and sparse-boundary groups.

### Task69.2: Freeze The Minimum Common Protocol

Status: complete.

The machine-readable protocol is
`paper/experiments/task69_common_protocol.json`. The common evidence track uses:

- matched MiniLM Dense, BM25, hybrid RRF, and IntentRoute;
- `top_k=10`, KMeans `K=32`, and route seeds 13/17/19;
- an eight-epoch no-leakage prequential adaptation trajectory, with labels from
  each interaction available only to later interactions;
- explicit disclosure that repeated-query adaptation is not IID held-out
  generalization;
- five-fold cross-fitted context-budget selection under the locked Task38 grid;
- Hit@10, EvidenceRecall@10, MRR@10, nDCG@10, final-context tokens, and feedback
  recovery;
- paired bootstrap intervals, exact McNemar tests, and win/loss/tie counts.

### Task69.3: LoTTE Cross-Domain Completion

Status: complete for the required Task69 science/search scope: 100k, 200k, and
the 400k scale-boundary row. Native full and new LoTTE domains are explicitly
deferred post-Task69 expansion candidates.

1. Complete science/search 100k with standalone BM25 and hybrid baselines,
   five-fold cross-fitted budgeting, and matched feedback controls.
2. Extend science/search incrementally to 200k, 400k, and native full scale.
3. Decide whether at most one or two additional LoTTE domains answer a specific
   remaining coverage question after Task69 paper integration.

Completed science/search 100k checkpoint:

- standalone BM25 and hybrid RRF baselines;
- matched no-feedback control against the existing trust-weighted trajectory;
- five-fold cross-fitted budget selection over all 596 queries;
- OOF mean Hit@10 delta `-0.11pp` with `16.88%` final-context token saving;
- strict 1pp non-inferiority remains `0/3` seeds;
- mean EvidenceRecall@10 delta is approximately `-2.86pp`, so this supports
  sufficient-evidence retrieval rather than complete evidence collection.

Completed science/search 200k checkpoint:

- incrementally extended the canonical science/search scale-store from
  101,187 to 201,098 corpus rows;
- standalone BM25, Dense, hybrid RRF, trust-weighted IntentRoute, and
  no-feedback control baselines;
- five-fold cross-fitted budget selection over all 596 queries;
- OOF mean Hit@10 delta `-0.67pp` with `10.75%` final-context token saving;
- strict 1pp non-inferiority remains `0/3` seeds;
- mean EvidenceRecall@10 delta is approximately `-2.97pp`, so this remains a
  sufficient-evidence trade-off row rather than complete-evidence preservation.

Completed science/search 400k core endpoint:

- extends the canonical science/search scale-store to 400,902 chunks;
- standalone BM25, Dense, hybrid RRF, trust-weighted IntentRoute, and matched
  no-feedback control all use the same 596 test queries and cached-exact
  retrieval engine;
- five-fold frozen-ranking budget selection yields only `1/5` eligible folds,
  `-0.67pp` mean Hit@10 delta, `3.15%` final-context token saving, and `0/3`
  strict 1pp non-inferiority seeds;
- mean EvidenceRecall@10 delta is approximately `-1.12pp`;
- this is a scale-boundary result, not evidence for robust lossless
  compression. The matched no-feedback control is complete. A Task40-style
  recovery replay finds only 3-6 affected queries per seed and recovers 2-5
  with same-query arm boosts; it is small-sample recovery evidence, not a new
  first-pass quality claim.

The technology/search experiment does not need to be rerun. Its existing
Task38/65 rankings, five-fold selections, paired statistics, and token artifacts
already satisfy the reference protocol. The shared Task69 table generator will
verify and assemble those artifacts into the reference row; it will not reuse a
previously reported aggregate as if it were raw evidence.

The optional science/search native-full scale and lifestyle/recreation/writing
100k rows move to the post-Task69 expansion queue. Sol review explicitly
recommends selecting at most one or two hypothesis-driven domains rather than
adding all remaining LoTTE domains merely to increase dataset count.

### Task69.4: Non-LoTTE Common-Protocol Completion

Status: complete for PubMedQA native full, CovidQA-RAG native full, and eManual
deduplicated native full.

- PubMedQA: added Dense/BM25/hybrid, 8-epoch trust-weighted and no-feedback
  IntentRoute, five-fold context-budget, final-token, paired, and no-op
  recovery endpoints on the native corpus. The frozen selector falls back to
  Dense in all folds, yielding 0.00% context saving while preserving Hit@10.
- CovidQA-RAG: added RAGBench native-full Dense/BM25/hybrid, 8-epoch
  trust-weighted and no-feedback IntentRoute, five-fold context-budget, paired
  statistics, and feedback-recovery diagnostics. The discriminative biomedical
  row has non-ceiling dense performance, small mean Hit@10 loss under
  cross-fitted budget selection, and measurable final-context token saving.
- eManual: generated the deduplicated/text-equivalent processed corpus, ran
  Dense/BM25/hybrid, 8-epoch trust-weighted and no-feedback IntentRoute, added
  five-fold context-budget, paired, final-token, and feedback-recovery
  diagnostics. The cross-fitted row shows -0.26pp Hit@10 with 16.20% final-
  context token saving.

### Task69.5: Mechanism And Boundary Tables

Status: complete as Task69.8 CPU cleanup.

- Banking77 remains a separate feedback route-learning table and is not pooled
  with evidence retrieval. Task69.8 records that trust-weighted feedback
  strongly improves route-level cluster hit and true reward over no-feedback,
  while fused Hit@10 remains near ceiling and does not dominate all static
  baselines.
- CUAD remains a separate sparse-GT boundary table unless a defensible full
  evidence benchmark is constructed. Task69.8 records it as a GT-anchored
  10k-sample boundary row with 79 evaluated queries, not as common positive
  evidence.

Task69.8 generated:

- `paper/experiments/scripts/task69_8_mechanism_boundary_summary.py`
- `paper/experiments/results/task69_8_mechanism_boundary_summary.md`
- `paper/experiments/results/task69_8_mechanism_boundary_summary.summary.csv`
- `paper/experiments/results/task69_8_mechanism_boundary_summary.baselines.csv`
- `paper/experiments/results/task69_8_mechanism_boundary_summary.json`

### Task69.6: Paper Integration

Status: complete.

- generated the cross-dataset common-protocol result table and machine-readable
  audit;
- retained separate LoTTE scale evidence rather than pooling unmatched rows;
- added the compact dataset/protocol registry as Supplementary Table S29;
- added the cross-domain OOF boundary paragraph to the manuscript;
- regenerated and validated the review packet and journal submission package.

Task69.7 integrated the CovidQA-RAG native-full transfer row into the current
paper-facing hierarchy. All mandatory Task69 paper integration is complete.
Additional GPU-side LoTTE domains remain post-Task69, hypothesis-driven
expansion candidates rather than completion requirements.

## Current Audit Outputs

Run:

```bash
.venv/bin/python paper/experiments/scripts/task69_audit_cross_dataset_consistency.py
```

Generated outputs use the prefix:

`paper/experiments/results/task69_cross_dataset_consistency`

The result snapshot deliberately contains missing values where historical
artifacts do not implement the frozen common protocol. This prevents a visually
complete table from falsely implying experimental equivalence.

## Claim Boundary

Task69 is intended to strengthen the chain

`local geometry -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`

across more than one dataset. It does not convert Banking77 into evidence
retrieval, CUAD smoke results into full-corpus evidence, simulated feedback into
real-user validation, or Hit@10 into complete evidence collection.
