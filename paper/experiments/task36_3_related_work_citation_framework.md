# Task36.3 Related-Work Citation Framework

Updated: 2026-05-31

## Purpose

This task converts the related-work section from an internal placeholder into a
paper-facing citation framework. It does not add new experiments. Its purpose
is to make the current draft easier to migrate into a venue template and to
reduce the risk that internal task labels or uncited claims leak into the final
paper.

## Files Updated

- `paper/full_draft/03_related_work.md`
- `paper/full_draft/10_reference_seed.md`
- `paper/full_draft/README.md`
- `paper/experiments/task_paper_use_status.md`

## Citation Groups Added

- Retrieval-augmented and knowledge-augmented generation:
  RAG and dense passage retrieval.
- Sparse, dense, and hybrid retrieval:
  BM25, dense retrieval, BEIR, and reciprocal rank fusion.
- Adaptive retrieval and contextual bandits:
  LinUCB and the broader contextual-bandit framing.
- Geometry and manifold-inspired retrieval:
  Isomap, locally linear embedding, Laplacian Eigenmaps, RAPTOR, and GraphRAG.
- User feedback, RLHF-inspired optimization, and trust weighting:
  implicit feedback, preference learning, and controlled feedback simulation.

## Paper-Facing Guardrail

The draft now uses provisional citation keys such as `[@lewis2020rag]` and
`[@li2010linucb]`. These are not final BibTeX entries. Before camera-ready
submission, convert the seed list into the target venue's bibliography format
and verify all metadata against primary sources or canonical DOI/arXiv pages.

## Claim Boundary

This task supports writing clarity only. It does not change the experimental
claim boundary: IntentWeight is still presented as a feedback-guided evidence
selection and context-budget controller evaluated in retrieval-augmented
question answering, not as a universal proof that every knowledge carrier or
every data manifold can be optimized by the same policy.
