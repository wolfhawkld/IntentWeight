# 1. Introduction

Knowledge-augmented agents improve language-model responses by conditioning
generation on external evidence. In many systems this evidence is supplied by a
retrieval-augmented generation (RAG) layer, but the underlying control problem
is broader: an agent must decide which pieces of structured domain knowledge
should enter its limited context. If relevant evidence is not selected, the
generator has little chance to recover; if too much evidence is selected,
latency, context cost, and distracting noise increase. Practical systems must
repeatedly decide how much evidence to retrieve, which route to trust, and when
a smaller context is safe.

Dense retrieval is a strong baseline for this problem because it can recover
semantically related passages even when the query and evidence do not share the
same surface form. However, dense-only retrieval remains a fixed route. It does
not explicitly decide when lexical matching is safer, when local cluster
structure is informative, when global dense retrieval should remain as a
fallback, or when the final retrieved context can be compacted. These questions
become more important in vertical-domain knowledge settings, where corpora are
often large, terminology-heavy, and shaped by repeated workflows, entities, and
user intents.

This paper studies the following hypothesis: vertical-domain knowledge data
often exhibits a piecewise relevance structure. Relevant evidence is not
uniformly distributed across the embedding space. Instead, it tends to form
local regions induced by domain concepts, lexical anchors, task workflows, and
user behavior. Pure dense retrieval performs local semantic neighborhood search
in one representation space, but it may not fully capture lexical constraints,
cluster-level routing, or user-specific relevance. At the same time, geometry
alone is not enough: a cluster route that prunes too early can miss the correct
evidence, and dense retrieval must remain available as a recall floor.

We propose IntentWeight, a feedback-guided adaptive evidence selection
controller for manifold-structured vertical-domain data. IntentWeight does not
replace dense retrieval with a single alternative retriever. Instead, in our
retrieval-augmented QA implementation, it builds a multi-route retrieval surface
including dense retrieval, BM25 lexical recall, and cluster-local retrieval.
Fixed KMeans/MiniBatchKMeans clusters provide stable arms for a LinUCB policy.
The policy observes query and route features, selects cluster-local routes, and
is updated by trust-weighted simulated feedback. A confidence-based final
context policy then decides whether to compact the retrieved context or keep a
denser fallback.

The framework is motivated by general evidence selection in knowledge-augmented
agents, including possible memory, graph, tree, or retrieval-backed carriers.
However, the empirical validation in this paper is limited to
retrieval-augmented question answering over LoTTE technology/search. Claims
about other knowledge-carrier formats should therefore be treated as motivation
and future work rather than demonstrated results.

This design separates three cost layers that are often conflated in RAG
experiments: the number of source candidates considered during retrieval, the
rate at which global dense retrieval is invoked, and the final number of
retrieved context tokens sent to the generator. Our main efficiency claim uses
the third layer. Earlier candidate-count reductions are useful retrieval-stage
diagnostics, but they are not evidence of lower LLM context cost unless the
final context itself is reduced.

We evaluate IntentWeight on multiple datasets and use LoTTE technology/search
as the main large-scale vertical-domain evidence benchmark. On LoTTE, we scale
from 100k to 638k corpus chunks and compare against dense-only retrieval using
`sentence-transformers/all-MiniLM-L6-v2` with exact cosine search. Under the
conservative Task29-C final context policy, IntentWeight reduces final retrieved
context tokens by approximately 4.7-5.3% across all scales. It preserves
near-dense Hit@10 at 100k and has mean Hit@10 above dense-only retrieval at
200k, 400k, and 638k. We treat these as bounded mean improvements rather than
universal or statistically significant dominance claims.

The contributions of this paper are:

1. We formulate evidence selection over structured vertical-domain data as an
   adaptive route-control problem rather than a fixed retriever selection
   problem.
2. We introduce IntentWeight, a feedback-guided multi-route controller combining
   dense retrieval, BM25 lexical recall, cluster-local retrieval,
   trust-weighted LinUCB route learning, and confidence-based final context
   compaction in a retrieval-augmented QA implementation.
3. We provide large-scale LoTTE evidence that conservative context compaction
   can reduce final retrieved context tokens while preserving dense-level
   Hit@10.
4. We add geometry diagnostics and ablations showing that local cluster
   structure is useful for routing, but not sufficient to replace dense
   retrieval.
5. We document limitation cases where dataset structure, weak labels, duplicate
   evidence, sparse ground truth, or complete-evidence requirements reduce the
   benefit of adaptive routing.

The resulting claim is intentionally bounded. IntentWeight is not presented as
a universal replacement for dense retrieval. It is a feedback-driven controller
that uses dense retrieval as a recall floor and learns when route confidence is
strong enough to reduce the final context budget.
