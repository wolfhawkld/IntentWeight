# Task69 Cross-Dataset Experimental Consistency

Updated: 2026-07-06

## Objective

Task69 converts the tiered six-setting narrative into a reviewer-readable
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

Status: in progress; science/search 100k and 200k checkpoints complete.

1. Complete science/search 100k with standalone BM25 and hybrid baselines,
   five-fold cross-fitted budgeting, and matched feedback controls.
2. Extend science/search incrementally to 200k, 400k, and native full scale.
3. Run lifestyle/search, recreation/search, and writing/search at 100k before
   deciding whether additional scale curves are informative.

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

The technology/search experiment does not need to be rerun. Its existing
Task38/65 rankings, five-fold selections, paired statistics, and token artifacts
already satisfy the reference protocol. The shared Task69 table generator will
verify and assemble those artifacts into the reference row; it will not reuse a
previously reported aggregate as if it were raw evidence.

The remaining Task69.3 work is science/search 400k/full and the additional 100k
LoTTE domains. No larger science/search run beyond 200k has been started at
this checkpoint.

### Task69.4: Non-LoTTE Common-Protocol Completion

Status: pending.

- PubMedQA: add five-fold context-budget, final-token, paired, and recovery
  endpoints on the existing native corpus.
- eManual: run IntentRoute on the deduplicated/text-equivalent corpus before
  adding it to the common performance table.

### Task69.5: Mechanism And Boundary Tables

Status: pending.

- Banking77 remains a separate feedback route-learning table.
- CUAD remains a separate sparse-GT boundary table unless a defensible full
  evidence benchmark is constructed.

### Task69.6: Paper Integration

Status: pending until the missing experiments are complete.

- generate the cross-dataset common-protocol result table;
- retain a separate LoTTE scale table;
- add a compact dataset/protocol table;
- update figures and manuscript claims only from generated artifacts.

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
