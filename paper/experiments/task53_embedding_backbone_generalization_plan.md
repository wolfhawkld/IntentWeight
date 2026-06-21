# Task53 Embedding Backbone Generalization Plan

Updated: 2026-06-22

## Purpose

Record the next experiment direction before rerunning GPU-heavy embedding
jobs. Task52 showed that `BAAI/bge-base-en-v1.5` raises the dense retrieval
quality floor relative to MiniLM, but also increases final top-10 context
tokens on the Task38 held-out split. The next step is to test IntentWeight as a
model-agnostic route-and-budget controller under matched embedding backbones.

## Planned Comparisons

Use the same LoTTE technology/search 100k corpus, Task38 frozen held-out split,
context-token accounting, and Task51 validation gate.

| Embedding backbone | Dense baseline | IntentWeight variant | Purpose |
| --- | --- | --- | --- |
| `sentence-transformers/all-MiniLM-L6-v2` | available | available | Existing lightweight baseline. |
| `BAAI/bge-base-en-v1.5` | available from Task52 | pending | Strong dense floor replacement. |
| `intfloat/e5-base-v2` | pending | pending | Third open-source backbone for generalization. |

## Model-Specific Encoding Notes

- BGE query prefix:
  `Represent this sentence for searching relevant passages: `
- E5 query prefix: `query: `
- E5 corpus prefix: `passage: `
- Keep embedding caches under `paper/experiments/data/embeddings/`; they are
  local artifacts and should not be committed.

## Claim Target

Do not frame the paper around one MiniLM-specific dominance claim. The stronger
and more defensible target is:

IntentWeight provides a matched-backbone quality-cost trade off against the
corresponding dense baseline. If MiniLM, BGE, and E5 show the same pattern, the
paper can discuss backbone-level robustness: IntentWeight acts as a
model-agnostic route-and-budget layer that can reduce final context tokens
under controlled retrieval-quality change.

## Deferred Work

1. Replace IntentWeight's dense branch with BGE and rerun the Task38-style
   route-and-budget comparison.
2. Add E5-base-v2 dense and IntentWeight runs with the correct query/corpus
   prefixes.
3. Produce a matched-backbone summary table with Hit@10,
   EvidenceRecall@10, average context tokens, token saving, and paired
   confidence intervals.
4. Promote the result into the manuscript only after Task51 reports no
   warnings or errors.
