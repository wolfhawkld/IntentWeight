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
| P1.5 | TechQA / technical-support evidence retrieval | Candidate RAGBench/TechQA corpus construction still needs validation; embeddings are new, and the original TechQA corpus may be much larger than the RAGBench row count | optional technical-support vertical row |
| P1.5 | LegalBench-RAG | New legal corpus and span-to-chunk preprocessing; license/download and chunking must be checked before use | optional legal evidence-retrieval row or CUAD replacement |
| P1.5 | FinQA full protocol | Feasibility download/preprocessing is complete, but the native processed corpus has 196,659 chunks and 16,562 queries; full Dense/IntentRoute should run on GPU or overnight infrastructure | optional finance-domain breadth row |
| P2 | Additional embedding-backbone robustness | BGE or other GPU-friendly encoder requires full reranking under a second backbone | robustness appendix or reviewer-response evidence |

## Current CPU / Non-Large-Embedding Queue

These tasks are suitable for the current CPU environment because their corpora
are small or their missing endpoints can be computed from existing rankings and
metrics.

| Priority | Task | Missing endpoint | Dataset role |
|---|---|---|---|
| P2 | FiQA metadata/preprocessing check | Optional BEIR finance alternative only if FinQA proves too expensive or unsuitable | finance-domain fallback |
| P2 | CUAD GT-anchored sample | optional token-budget and paired statistics only if kept as a boundary appendix row | sparse-GT boundary only |
| P2 | Banking77 native full | optional route-learning summary table cleanup; not pooled with evidence retrieval | mechanism-only row |
| P2 | Task69 audit integration | update protocol coverage after each CPU/GPU batch | reproducibility and reviewer readability |

## Merged Dataset-Expansion Decision

The Nemesis expansion review and the current Task69 plan agree on the main
direction:

- **Strong accept:** add more LoTTE search domains. LoTTE is the cleanest
  cross-domain extension because the corpus/query/qrels schema is identical to
  the current technology/search and science/search runs. This strengthens
  domain generalization without changing the protocol.
- **Accept with validation:** add TechQA and LegalBench-RAG only after checking
  corpus construction, license, and chunk-to-evidence mapping. They are useful
  because they add technical-support and legal retrieval evidence, but they
  should not be silently pooled with LoTTE until they pass the same endpoint
  coverage audit.
- **Accept as a biomedical discriminative supplement:** add CovidQA-RAG if we
  need a non-ceiling biomedical row. PubMedQA is now useful as a safety fallback
  row, but Dense is nearly saturated there, so it is weak evidence for feedback
  improvement.
- **Optional:** add exactly one finance dataset, preferably FinQA if we want
  RAGBench-format convenience or FiQA if we want a more conventional BEIR
  retrieval benchmark.
- **Do not remove existing boundary evidence prematurely:** CUAD should remain
  a sparse-GT boundary appendix row unless LegalBench-RAG is successfully
  preprocessed and evaluated. Banking77 remains a mechanism-only route-learning
  proxy.

The resulting paper-facing structure should be:

1. **LoTTE scale/domain matrix:** technology/search full scale, science/search
   partial scale, and lifestyle/recreation/writing 100k.
2. **External vertical evidence rows:** eManual deduplicated, PubMedQA, and
   optionally CovidQA-RAG, TechQA, LegalBench-RAG, or one finance dataset.
3. **Mechanism/boundary rows:** Banking77 and CUAD, reported separately and not
   pooled with evidence retrieval.

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
4. If cross-domain LoTTE is stable, choose at most two external vertical
   candidates for the next expansion batch. CovidQA-RAG is already complete;
   the remaining preferred order is TechQA, LegalBench-RAG, then one finance
   dataset.
5. Decide whether science/search full and second-encoder robustness are worth
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
- CovidQA-RAG native full: completed RAGBench parquet download, preprocessing,
  Dense/BM25/hybrid, 8-epoch trust-weighted and no-feedback IntentRoute,
  five-fold cross-fitted budget selection, paired statistics, and feedback
  recovery diagnostics. This row is the biomedical discriminative supplement to
  PubMedQA: Dense is not saturated, and the selector finds a modest context
  saving under small mean Hit@10 change.
- FinQA feasibility probe: completed RAGBench parquet download, preprocessing,
  and processed-dataset validation. The native processed corpus has 196,659
  chunks and 16,562 queries, with 9,051 queries carrying usable GT. Full
  common-protocol evaluation is moved to the GPU/overnight queue rather than
  this CPU session.
