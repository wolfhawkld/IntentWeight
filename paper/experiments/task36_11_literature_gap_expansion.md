# Task36.11 Literature Gap Expansion

Updated: 2026-05-31

## Purpose

Audit the full draft for missing direct prior art before venue-specific
formatting. This is a writing revision only. It does not add or change
experimental results.

## Main Finding

The previous related-work draft covered RAG, sparse/dense retrieval, LinUCB,
manifold learning, structured retrieval, and feedback learning, but it
under-covered adaptive retrieval and context compression. The most important
omission was MBA-RAG, which already applies a multi-armed bandit to dynamic RAG
strategy selection with an accuracy-efficiency reward.

The paper must therefore avoid any claim that IntentWeight is the first use of
bandits in retrieval-augmented generation.

## Added Literature Groups

### Adaptive retrieval and correction

- FLARE: active retrieval during generation under token-level uncertainty.
- Adaptive-RAG: query-complexity classification over retrieval strategies.
- Self-RAG: on-demand retrieval and critique through reflection tokens.
- CRAG: evidence-quality evaluation and corrective retrieval actions.

### Direct bandit comparison

- MBA-RAG: bandit-based selection among retrieval strategies with a
  cost-sensitive reward.

### Context compression and evidence refinement

- Selective Context: redundancy pruning for compact LLM inputs.
- LLMLingua and LLMLingua-2: prompt compression methods.
- DSLR: sentence-level reranking and reconstruction of retrieved passages.
- REPLUG: tuneable retrieval for frozen black-box language models.

## Paper-Facing Distinction

IntentWeight is positioned as a feedback-guided evidence-selection controller,
not as the first adaptive RAG router. Relative to MBA-RAG and other adaptive
retrieval systems, the current study focuses on:

- fixed cluster-local routes over a domain corpus;
- route-level credit assignment;
- trust-weighted simulated feedback;
- dense rescue paths that bound hard-pruning risk;
- geometry diagnostics under a piecewise relevance-manifold assumption;
- final context-token measurement rather than source-candidate proxy cost.

## Files Updated

- `paper/full_draft/03_related_work.md`
- `paper/full_draft/10_reference_seed.md`
- `paper/full_draft/references.bib`
- `paper/experiments/task_paper_use_status.md`

## Validation

Regenerate the independent-review packet and run:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
```
