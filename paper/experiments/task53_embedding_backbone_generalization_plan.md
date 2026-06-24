# Task53 Embedding Backbone Generalization Plan

Updated: 2026-06-24

## Purpose

Record the experiment direction before rerunning GPU-heavy embedding jobs.
Task52 showed that `BAAI/bge-base-en-v1.5` raises the dense retrieval quality
floor relative to MiniLM, but also increases final top-10 context tokens on the
Task38 held-out split. Task53 has now executed this plan; the completed result
summary is `paper/experiments/task53_embedding_backbone_generalization_summary.md`.

## Planned Comparisons

Use the same LoTTE technology/search 100k corpus, Task38 frozen held-out split,
context-token accounting, and Task51 validation gate.

| Embedding backbone | Dense baseline | IntentWeight variant | Purpose |
| --- | --- | --- | --- |
| `sentence-transformers/all-MiniLM-L6-v2` | available | available | Existing lightweight baseline. |
| `BAAI/bge-base-en-v1.5` | completed | completed | Strong dense floor replacement. |
| `intfloat/e5-base-v2` | completed | completed | Third open-source backbone for generalization. |

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

## Completed Work

1. Replaced IntentWeight's dense branch with BGE and reran the Task38-style
   route-and-budget comparison.
2. Added E5-base-v2 dense and IntentWeight runs with the correct query/corpus
   prefixes.
3. Produced a matched-backbone summary table with Hit@10, token saving, and
   paired confidence intervals.
4. Added the Task53 artifacts to Task51; the current audit reports no warnings
   or errors.
