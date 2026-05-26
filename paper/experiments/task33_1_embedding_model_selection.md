# Task33.1 Embedding Model Selection Matrix

Updated: 2026-05-26

Task33.1 addresses the "single embedding model" reviewer risk. The goal is not
to benchmark embedding models. The embedding encoder is treated as a replaceable
representation module, while the paper studies whether IntentWeight remains a
valid feedback-driven adaptive retrieval controller under another open-source
embedding family.

## Selection Criteria

The selection should balance:

- MTEB English v1 / public benchmark score;
- model parameter count;
- embedding dimensionality;
- CPU and memory requirements;
- whether the model is open-source and locally reproducible;
- fit with LoTTE English technology/search retrieval;
- implementation friction in the current scripts.

## Candidate Matrix

| Rank for Task33.1 | Model | MTEB English v1 / Public Score | Params | Dim | Hardware Cost | Fit for Task33.1 | Notes |
|---:|---|---:|---:|---:|---|---|---|
| 1 | `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` | Public full MTEB v1 average is less central than its QA/search training; commonly reported around low 50s depending on benchmark slice | 22.7M | 384 | Very low | Highest | Same resource class as current MiniLM, trained on 215M QA/search pairs, best CPU-friendly robustness choice |
| 2 | `sentence-transformers/all-MiniLM-L6-v2` | 56.26 / about 56.3 | 22.7M | 384 | Very low | Main baseline | Current complete evidence chain; lightweight, open-source, CPU-friendly, reproducible |
| 3 | `nomic-ai/nomic-embed-text-v1.5` | 62.28 at 768d; 61.96 at 512d; 61.04 at 256d | about 137M | 768, Matryoshka-truncatable | Medium to high | Strong open-source robustness | Stronger open model, but not MiniLM-class CPU cost; requires task prefixes and likely `trust_remote_code=True` |
| 4 | `nomic-ai/nomic-embed-text-v1` | 62.39 | about 100M+ | 768 | Medium to high | Secondary Nomic option | Slightly higher public score than v1.5, but v1.5 is more useful for cost experiments due to Matryoshka truncation |
| 5 | `BAAI/bge-base-en-v1.5` | Stronger modern dense family; exact paper use depends on benchmark slice | BERT-base class | 768 | High on CPU | GPU / overnight optional | Good reviewer-facing strong baseline, but CPU run was much slower than MiniLM in local tests |

## Local Runtime Evidence

On the current WSL CPU environment, a small 1024-document LoTTE benchmark showed:

| Model | Batch Size | Time | Docs/sec |
|---|---:|---:|---:|
| `sentence-transformers/all-MiniLM-L6-v2` | 64 | 13.34s | 76.76 |
| `BAAI/bge-base-en-v1.5` | 16 | 84.43s | 12.13 |
| `BAAI/bge-base-en-v1.5` | 32 | 88.78s | 11.53 |
| `BAAI/bge-base-en-v1.5` | 64 | 93.88s | 10.91 |

BGE base was about 6-7x slower than MiniLM on this CPU. It also used only about
7-8 CPU threads effectively, which appeared as roughly 40-50% host CPU
utilization on a 16-thread machine. This is expected for a larger BERT-base
style encoder and does not indicate an experiment-logic bug.

The interrupted BGE 100k attempt produced no result files and no BGE embedding
cache because the current cache implementation writes embeddings only after the
full corpus encode completes.

## Interpretation

`multi-qa-MiniLM-L6-cos-v1` should be the first Task33.1 run because it directly
tests whether the current evidence depends on the exact `all-MiniLM-L6-v2`
encoder while keeping hardware requirements comparable. It is also more aligned
with query-document retrieval than generic sentence similarity because it was
trained for semantic search over question-answer pairs.

`nomic-embed-text-v1.5` is a better open-source strong-model supplement than
BGE for this project boundary, but it is not a MiniLM-class CPU model. It should
be treated as a second-stage robustness check after scripts support:

- corpus/query task prefixes: `search_document: ...` and `search_query: ...`;
- `trust_remote_code=True` loading;
- optional Matryoshka truncation, especially 512d or 256d.

BGE should no longer be the default CPU robustness path. It remains useful on a
GPU machine or as an overnight optional run.

## Recommended Task33.1 Plan

1. **Task33.1a: CPU-friendly MiniLM-family robustness**
   - Model: `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`
   - Scale: LoTTE 100k first
   - Runs: dense-only, Task29-C, geometry diagnostics, final context-token comparison
   - Purpose: answer whether IntentWeight depends specifically on
     `all-MiniLM-L6-v2`.

2. **Task33.1b: Nomic open-source strong-model smoke**
   - Model: `nomic-ai/nomic-embed-text-v1.5`
   - Scale: LoTTE 20k or 50k first
   - Required code support: prefixes, trust remote code, optional Matryoshka dim
   - Purpose: test another open-source embedding family with stronger public
     benchmark performance.

3. **Task33.1c: Optional BGE GPU/overnight run**
   - Model: `BAAI/bge-base-en-v1.5`
   - Scale: 100k only if GPU or long CPU window is available
   - Purpose: strong dense-family sensitivity check, not required for the
     minimum pre-writing completion set.

## Paper Wording

Recommended wording:

> We do not aim to benchmark embedding models. The encoder is treated as a
> replaceable representation module. The main experiments use
> `all-MiniLM-L6-v2` for tractability and reproducibility; additional robustness
> checks use a QA-tuned MiniLM encoder and, where compute permits, an
> open-source Nomic encoder.

Avoid:

> IntentWeight outperforms state-of-the-art embedding models.

Also avoid:

> BGE/Nomic results replace the main MiniLM evidence chain.

## Source Notes

- MTEB paper Table 11 reports `MiniLM-L6` average `56.26` and `MiniLM-L12`
  average `56.53` on English results.
- Hugging Face model cards report both `all-MiniLM-L6-v2` and
  `multi-qa-MiniLM-L6-cos-v1` as 22.7M-parameter, 384-dimensional
  SentenceTransformer models.
- The `multi-qa-MiniLM-L6-cos-v1` model card states that it was trained on
  about 215M question-answer pairs and is intended for semantic search.
- Nomic model cards report `nomic-embed-text-v1` MTEB `62.39` and
  `nomic-embed-text-v1.5` MTEB `62.28`, with v1.5 supporting Matryoshka
  dimensionality reduction to 512d, 256d, 128d, and 64d.
