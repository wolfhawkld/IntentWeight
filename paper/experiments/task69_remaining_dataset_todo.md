# Task69 Remaining Dataset TODO

Updated: 2026-07-07

## Purpose

This TODO tracks the remaining dataset-level work after the Task69
cross-dataset consistency audit. It follows the Nemesis-aligned protocol
decision: use one common endpoint set where tasks are comparable, but do not
force all datasets into the same corpus-size grid.

The evidence chain remains:

`local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`

## Current Completed Common-Protocol Rows

| Dataset | Scale | Role | Status |
|---|---:|---|---|
| LoTTE technology/search | 100k, 200k, 400k, 638k full | scale/full-stack anchor | complete |
| LoTTE science/search | 100k, 200k | cross-domain scale | complete |
| PubMedQA | native full | non-LoTTE evidence transfer | complete |
| eManual deduplicated | native full | corrected boundary | complete |

These rows include Dense, BM25, hybrid RRF, IntentRoute, feedback controls,
final-context tokens, five-fold cross-fitted budget selection, and paired
statistics.

## GPU / Embedding-Heavy Queue

These tasks require new large corpus embeddings or new LoTTE domain stores.
They should be run on the GPU machine unless intentionally deferred.

| Priority | Task | Why it is embedding-heavy | Target output |
|---|---|---|---|
| P1 | LoTTE science/search 400k | Extends the science scale-store from 200k to 400k; about 200k new corpus rows | common-protocol 400k row |
| P2 | LoTTE science/search native full | Native science/search is much larger than technology full; only run if resources justify it | optional full-scale cross-domain row |
| P1 | LoTTE lifestyle/search 100k | New domain, new processed corpus and embeddings | 100k domain-generalization row |
| P1 | LoTTE recreation/search 100k | New domain, new processed corpus and embeddings | 100k domain-generalization row |
| P1 | LoTTE writing/search 100k | New domain, new processed corpus and embeddings | 100k domain-generalization row |
| P2 | Additional embedding-backbone robustness | BGE or other GPU-friendly encoder requires full reranking under a second backbone | robustness appendix or reviewer-response evidence |

## Current CPU / Non-Large-Embedding Queue

These tasks are suitable for the current CPU environment because their corpora
are small or their missing endpoints can be computed from existing rankings and
metrics.

| Priority | Task | Missing endpoint | Dataset role |
|---|---|---|---|
| P2 | CUAD GT-anchored sample | optional token-budget and paired statistics only if kept as a boundary appendix row | sparse-GT boundary only |
| P2 | Banking77 native full | optional route-learning summary table cleanup; not pooled with evidence retrieval | mechanism-only row |
| P2 | Task69 audit integration | update protocol coverage after each CPU/GPU batch | reproducibility and reviewer readability |

## Table-Design Guardrails

- Do not pool Banking77 with evidence-retrieval datasets.
- Do not pool CUAD sparse-GT smoke results with LoTTE/PubMedQA/eManual common
  evidence rows.
- Do not require PubMedQA or eManual to have 100k/200k/400k scales; use native
  full instead.
- Treat `Hit@10` as sufficient-evidence retrieval, not complete evidence
  collection.
- Keep final-context token saving separate from source-corpus embedding cost.
- Keep simulated feedback labeled as controlled feedback validation, not
  production RLHF.

## Suggested Execution Order

1. Update the Task69 audit and paper-facing dataset/protocol table after each
   new GPU batch.
2. On the GPU machine, run LoTTE science/search 400k.
3. On the GPU machine, run LoTTE lifestyle/recreation/writing 100k rows.
4. Decide whether science/search full and second-encoder robustness are worth
   the additional cost.

## Completed CPU Updates

- PubMedQA native full: completed Dense/BM25/hybrid, 8-epoch trust-weighted and
  no-feedback IntentRoute, five-fold cross-fitted budget selection, paired
  statistics, and a no-op feedback-recovery endpoint. The selector falls back to
  Dense in all folds, yielding 0.00% context saving but preserving Hit@10.
- eManual deduplicated native full: completed the deduplicated processed
  dataset, Dense/BM25/hybrid, 8-epoch trust-weighted and no-feedback
  IntentRoute, five-fold cross-fitted budget selection, paired statistics, and
  feedback-recovery diagnostics.
