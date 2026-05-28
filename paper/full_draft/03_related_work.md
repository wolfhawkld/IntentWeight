# 2. Related Work

This section is a first draft and still needs formal citations. Citation TODOs
should be filled once the target venue and bibliography format are chosen.

## 2.1 Retrieval-Augmented Generation

Retrieval-augmented generation connects a parametric language model to an
external evidence source. Instead of relying only on model parameters, a RAG
system retrieves passages, documents, graph nodes, or other evidence units and
conditions the generator on that retrieved context. This improves factual
grounding and domain adaptation, but it shifts a large part of system quality to
the retrieval layer. If the retrieval layer misses the relevant evidence, the
generator cannot reliably recover. If the retrieval layer returns excessive or
noisy evidence, downstream generation becomes more expensive and may become less
faithful.

Prior RAG work has studied retriever-generator integration, retrieval
granularity, evidence grounding, query rewriting, and multi-stage retrieval
pipelines. IntentWeight is complementary to this line of work. It does not
propose a new generator or a new evidence format. Instead, it focuses on the
retrieval controller: given several retrieval routes, route confidence, and
feedback, how should the system decide which retrieval surface to trust and how
many retrieved chunks to send to the generator?

TODO citations: original RAG, open-domain QA RAG, retrieval-grounded generation,
query rewriting, evidence citation and grounding.

## 2.2 Sparse, Dense, and Hybrid Retrieval

Sparse lexical retrieval such as BM25 remains valuable in domain settings where
exact terms, entity names, identifiers, abbreviations, and technical phrases
matter. Dense retrieval improves semantic matching by embedding queries and
documents into a shared representation space, allowing the system to recover
evidence even when words do not match exactly. Hybrid retrieval combines these
signals, often through score interpolation, reciprocal-rank fusion, or a
reranking stage.

The current paper treats dense retrieval as a strong baseline, not as a weak
component to be replaced. Dense-only retrieval remains the main quality anchor
in our experiments, and dense fallback is retained in IntentWeight when route
confidence is low. BM25 contributes lexical coverage, and cluster-local dense
retrieval contributes a structured local search path. The contribution is not a
claim that any single route is best, but that a controller can learn when and
how to use different routes.

TODO citations: BM25, DPR/dense retrieval, BEIR or heterogeneous retrieval
benchmarks, hybrid retrieval and reciprocal-rank fusion.

## 2.3 Adaptive Retrieval and Contextual Bandits

RAG systems are often configured with fixed hyperparameters: a fixed top-k, a
fixed retriever mixture, a fixed reranker, or a fixed fallback policy. Such
static configurations are easy to deploy but poorly matched to heterogeneous
query streams. Some queries require exact lexical anchors, others require
semantic expansion, and others can be answered from a smaller local evidence
region.

Contextual bandits provide a natural framework for this setting. A bandit policy
observes a context, selects an action, receives feedback, and updates its policy
for future decisions. LinUCB is a simple and interpretable contextual bandit
algorithm that models each arm's expected reward as a linear function of the
context and adds an uncertainty bonus for exploration. IntentWeight uses LinUCB
not as a replacement retriever, but as an adaptive routing policy over
cluster-local retrieval arms and confidence-controlled route choices.

TODO citations: LinUCB, contextual bandits for recommendation, online learning
with feedback, retrieval routing and adaptive retrieval.

## 2.4 Geometry and Manifold-Inspired Retrieval

Embedding spaces used for retrieval often contain local structure: documents
from the same topic, entity neighborhood, task workflow, or domain subfield tend
to occupy nearby regions. This motivates clustering, tree indexes, graph-based
retrieval, and other structured retrieval methods. However, local geometry is
not sufficient by itself. If a cluster or tree branch is selected incorrectly,
early pruning can remove the correct evidence before dense retrieval or rerankers
can recover it.

IntentWeight uses a bounded piecewise relevance-manifold assumption. The paper
does not claim to prove a mathematical manifold theorem. Instead, it tests
whether local cluster geometry is useful as a routing signal. Dense retrieval
and BM25 remain available as rescue paths, and geometry is evaluated
diagnostically through nearest-cluster hit, PCA variance, and context retention.

TODO citations: clustering for retrieval, hierarchical retrieval, RAPTOR or
tree-based retrieval, GraphRAG or graph-based retrieval, manifold learning or
intrinsic-dimension diagnostics where appropriate.

## 2.5 User Feedback and Trust Weighting

User feedback can improve retrieval systems, but real feedback is delayed,
biased, sparse, and user-dependent. Explicit ratings may be rare, and implicit
signals such as dwell time, copied text, or follow-up queries can be noisy.
This motivates feedback denoising and trust weighting. Feedback should be
interpreted as a signal with varying reliability rather than as a perfect
oracle.

The current paper uses controlled simulated feedback rather than real human
feedback. This choice makes it possible to isolate the route-learning mechanism,
evaluate trust-weighted updates, and avoid uncontrolled user-behavior variance.
The result validates the policy-learning mechanism under controlled conditions,
but it does not claim that real deployment feedback has already been solved.

TODO citations: feedback learning, implicit feedback bias, trust-weighted user
signals, online evaluation in retrieval.
