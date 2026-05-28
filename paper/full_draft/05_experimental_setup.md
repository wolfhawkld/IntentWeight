# 4. Experimental Setup

## 4.1 Datasets

The experiments use several datasets, but they have different roles. The paper
does not treat all datasets as equal evidence for the main claim.

| Dataset | Role | Paper use | Caveat |
|---|---|---|---|
| LoTTE technology/search | Main vertical-domain retrieval benchmark | Main scale-up, token-quality frontier, geometry validation | No true corpus topic labels in processed qrels |
| PubMedQA | Feedback/manifold proof-of-concept | Shows trust feedback and local propagation can improve policy | GT is abstract-level context, not strict answer sentence |
| Banking77 | Intent/domain routing proxy | Shows strong feedback self-evolution and intent structure | Should not be mixed with evidence retrieval main table |
| eManual | Failure/limitation case | Shows duplicate text and strict chunk-id issues | Low strict recall does not prove geometry is absent |
| CUAD | Sparse smoke/stress case | Shows sparse legal-domain limitation | GT-anchored sample only, not full-corpus main evidence |

LoTTE technology/search is the main large-scale evidence benchmark. We evaluate
nested corpus scales from 100k to 638k chunks with 596 test queries. CUAD and
eManual are reported as limitation cases rather than main positive evidence.

## 4.2 Baselines and Variants

The baseline family includes:

- BM25-only lexical retrieval.
- Dense-only retrieval with `sentence-transformers/all-MiniLM-L6-v2`.
- BM25 + dense hybrid retrieval using reciprocal-rank fusion.
- Full multi-route IntentWeight.
- Gated cost-aware IntentWeight.
- Confidence-based final context IntentWeight.
- Static geometry controls such as nearest-cluster routing.
- Naive controls such as random or epsilon-greedy arm selection.

Dense-only retrieval is the primary quality baseline. The paper should avoid
weak baseline framing: dense is strong and remains a required recall floor in
the proposed method.

## 4.3 Metrics

Retrieval quality is measured with:

- `Hit@K`: whether any ground-truth chunk appears in the top K.
- `evidence_recall@K`: fraction of all ground-truth chunks retrieved.
- `MRR@K`: reciprocal rank of the first relevant chunk.
- `nDCG@K`: binary relevance ranking quality.

The main headline uses query-level `Hit@10`. This choice reflects the target
use case: retrieving at least one usable evidence chunk for RAG generation under
a smaller context budget. It does not imply complete evidence collection.
`evidence_recall@10` is reported separately where multi-evidence coverage is
important.

Cost and efficiency are separated into three layers:

- Source candidate cost: number of candidates considered before final fusion.
- Dense invocation rate: fraction of queries using the global dense path.
- Final context tokens: token count of retrieved chunks sent to the generator.

The main cost result uses final context tokens. Source candidate cost and dense
invocation rate are retrieval-stage diagnostics.

## 4.4 Prequential Simulated Feedback

LinUCB experiments use a no-leakage prequential simulated-feedback protocol.
For each query, the current policy state is frozen before retrieval. The system
ranks candidates, constructs the final context, and is evaluated against the
ground-truth evidence. Only after this evaluation is the ground-truth label
converted into simulated feedback and used to update the LinUCB state for later
queries.

The feedback signal is controlled and ground-truth-derived. Oracle feedback is
used only as an upper bound. Equal noisy and trust-weighted modes simulate
imperfect user feedback with different reliability assumptions. Trust weighting
changes how strongly a feedback event updates the route policy, but it does not
give the current query access to its answer label before ranking.

This setup validates the route-learning mechanism under controlled feedback
quality. It does not claim that real user feedback has already been collected,
nor that delayed, biased, or adversarial human feedback would have the same
effect without additional deployment safeguards.

Some experiments use multiple prequential epochs over the same query stream to
simulate repeated interaction. These runs are useful for route-policy
self-evolution analysis. They are not IID held-out generalization results.

## 4.5 Implementation Notes

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2` with exact
cosine search on CPU. Embeddings and retrieval artifacts are cached to avoid
repeating deterministic computation. Metrics are recomputed from saved
rankings, not copied from prior summaries.

KMeans/MiniBatchKMeans uses a fixed number of arms across scales. This supports
LinUCB comparability and reproducibility, but it is not claimed to be the best
possible clustering design.
