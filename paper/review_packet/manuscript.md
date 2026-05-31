# IntentWeight: Feedback-Guided Evidence Selection under a Piecewise Relevance-Manifold Assumption

<!-- Generated review packet. Edit source chapters under paper/full_draft/. -->

# Abstract

Knowledge-augmented agents must select enough evidence to support answer
quality while limiting latency, noise, and final context cost. This trade-off is
especially difficult for vertical-domain data, where relevance is shaped by
domain terminology, local semantic neighborhoods, workflow structure, and
evolving user intent. We propose IntentWeight, a feedback-guided evidence
selection controller motivated by a piecewise relevance-manifold assumption.
IntentWeight combines dense semantic retrieval, BM25 lexical recall, and
cluster-local routing, and uses trust-weighted LinUCB to learn route preferences
from simulated feedback. A confidence-based final context policy then compacts
the selected evidence sent to the generator while preserving dense fallback
under low confidence. We instantiate this framework in a retrieval-augmented
question-answering setting on LoTTE technology/search,
evaluated from 100k to 638k corpus chunks; our empirical claims are limited to
this retrieval-augmented QA setting rather than all possible knowledge-carrier
formats. The conservative policy reduces final retrieved context tokens by
approximately 4.7-5.3% while preserving near-dense $\mathrm{Hit@10}$ at 100k
and achieving mean above-dense $\mathrm{Hit@10}$ at 200k, 400k, and 638k.
Geometry diagnostics and ablations show that local cluster structure provides
useful routing signal, while dense retrieval remains an important recall floor.
A 60-query downstream generation smoke test shows no obvious answer-quality
degradation from the compressed context. These results position IntentWeight
not as a universal replacement for dense retrieval, but as an adaptive
quality-cost controller for evidence selection over structured domain data.

---

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
controller motivated by a piecewise relevance-manifold assumption for
vertical-domain data. IntentWeight does not replace dense retrieval with a
single alternative retriever. Instead, in our retrieval-augmented QA
implementation, it builds a multi-route retrieval surface
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
conservative confidence-based final context policy, IntentWeight reduces final
retrieved context tokens by approximately 4.7-5.3% across all scales. It
preserves near-dense $\mathrm{Hit@10}$ at 100k and has mean
$\mathrm{Hit@10}$ above dense-only retrieval at 200k, 400k, and 638k. We treat
these as bounded mean improvements rather than universal or statistically
significant dominance claims.

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
   $\mathrm{Hit@10}$.
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

---

# 2. Related Work

This section uses provisional citation keys. The exact BibTeX style should be
normalized once the target venue template is selected.

## 2.1 Retrieval-Augmented and Knowledge-Augmented Generation

Retrieval-augmented generation connects a parametric language model to an
external evidence source. Instead of relying only on model parameters, the
system retrieves passages, documents, graph nodes, tree summaries, memory
entries, or other evidence units and conditions generation on that selected
context. Early RAG work formalized this parametric/non-parametric memory
combination for knowledge-intensive NLP tasks [@lewis2020rag]. Dense passage
retrieval further established neural retrieval as a strong component for
open-domain question answering [@karpukhin2020dpr].

This line of work improves factual grounding and domain adaptation, but it also
makes evidence selection a central point of failure. If the retrieval layer
misses relevant evidence, the generator has limited ability to recover. If it
returns excessive or noisy evidence, downstream generation becomes more
expensive and may become less faithful. IntentWeight is complementary to
retriever-generator architectures: it does not propose a new generator or a new
knowledge carrier. It studies a feedback-guided controller for deciding which
evidence route to trust and how much selected evidence should enter the final
context.

## 2.2 Sparse, Dense, and Hybrid Retrieval

Sparse lexical retrieval remains valuable in domain settings where exact terms,
entity names, identifiers, abbreviations, and technical phrases matter. BM25 is
a standard probabilistic lexical retrieval function and is still widely used as
a strong sparse baseline [@robertson2009bm25]. Dense retrieval embeds queries
and documents into a shared representation space, enabling semantic matching
when surface terms differ [@karpukhin2020dpr]. Broad heterogeneous retrieval
benchmarks show that retrieval performance varies substantially across tasks and
domains, so a single retrieval family should not be assumed to dominate all
settings [@thakur2021beir].

Hybrid retrieval combines sparse and dense signals through score interpolation,
rank fusion, or reranking. Reciprocal rank fusion is a simple and widely used
rank-level fusion method [@cormack2009rrf]. In this paper, dense retrieval is a
strong baseline and an explicit recall floor, not a weak component to be
replaced. BM25 contributes lexical coverage, and cluster-local dense retrieval
contributes a structured local search path. The contribution is not that any
single route is best, but that a controller can learn when and how to combine
routes under a final context budget.

## 2.3 Adaptive Retrieval and Contextual Bandits

Many retrieval-augmented systems are configured with fixed hyperparameters: a
fixed top-$k$, a fixed retriever mixture, a fixed reranker, or a fixed fallback
policy. Static configurations are easy to deploy but poorly matched to
heterogeneous query streams. Some queries require exact lexical anchors, others
require semantic expansion, and others can be answered from a smaller local
evidence region.

Contextual bandits provide a natural abstraction for adaptive route control. A
policy observes a context, selects an action, receives feedback, and updates its
future decisions. LinUCB is a simple and interpretable contextual bandit
algorithm that models each arm's expected reward as a linear function of the
context and adds an upper-confidence exploration bonus. It was originally
studied for personalized news recommendation [@li2010linucb], and contextual
bandits more broadly are a standard framework for sequential decision making
under partial feedback [@lattimore2020bandits].

IntentWeight uses LinUCB not as a replacement retriever, but as an adaptive
routing policy over cluster-local evidence routes and confidence-controlled
context choices. This distinguishes the method from static hybrid retrieval:
the controller is updated by feedback and can change route preference over
time.

## 2.4 Geometry and Manifold-Inspired Retrieval

Embedding spaces used for retrieval often contain local structure: documents
from the same topic, entity neighborhood, task workflow, or domain subfield tend
to occupy nearby regions. Classical manifold learning studies how high
dimensional observations may concentrate on lower-dimensional nonlinear
structures, as in Isomap [@tenenbaum2000isomap], locally linear embedding
[@roweis2000lle], and Laplacian Eigenmaps [@belkin2003laplacian]. This paper
does not use these algorithms directly, but it adopts a bounded diagnostic
view: vertical-domain evidence may exhibit local relevance structure that can
be probed through PCA spectrum, cluster routing, and context-space retention.

Structured retrieval systems also exploit local or hierarchical organization.
Tree-organized retrieval methods such as RAPTOR build recursive summaries over
clusters [@sarthi2024raptor], while graph-based RAG methods organize entities
and communities to answer broader corpus-level questions [@edge2024graphrag].
These methods show that retrieval structure can matter, but structure also
introduces routing risk: a wrong branch, cluster, or graph neighborhood can
discard relevant evidence early.

IntentWeight therefore treats geometry as one signal in a controller rather
than as a complete retrieval model. Dense retrieval and BM25 remain available as
rescue paths, and the geometry assumption is evaluated diagnostically through
$\mathrm{NearestClusterHit@K}$, $\mathrm{PCAvar@m}$, $\mathrm{PCAdim90}$, and
$\mathrm{ContextRetention@K}$.

## 2.5 User Feedback, RLHF-Inspired Optimization, and Trust Weighting

User feedback can improve retrieval systems, but real feedback is delayed,
biased, sparse, and user-dependent. Earlier work on clickthrough and implicit
feedback shows that user behavior can train ranking systems, while also
requiring care because clicks and query reformulations are biased signals
[@joachims2002clickthrough; @radlinski2005querychains]. In language-model
systems, human-preference learning and RLHF-style optimization show how feedback
can shape model behavior [@christiano2017preferences; @ouyang2022instructgpt].

IntentWeight is inspired by this feedback-optimization paradigm, but it is not a
full RLHF pipeline. The current experiments use controlled simulated feedback
to isolate whether a contextual-bandit retrieval controller can improve route
selection under noisy and trust-weighted feedback. Trust weighting is used to
scale feedback updates by simulated reliability, reflecting the deployment
assumption that not all users or implicit signals should be trusted equally.
The paper therefore claims mechanism validation under controlled feedback, not
that real human-feedback deployment has already been solved.

---

# 3. Method

## 3.1 Problem Formulation

In the retrieval-backed implementation evaluated here, let an evidence corpus
be a set of chunks $D = \{d_i\}_{i=1}^{N}$ and a query stream
$Q = \{q_t\}_{t=1}^{T}$. For each query $q_t$, a retrieval system returns an
ordered context $C_t = [d_{t,1}, \ldots, d_{t,k}]$ that will be passed to a
downstream generator. The objective is to preserve retrieval quality while
controlling both retrieval cost and final context cost.

IntentWeight treats retrieval as a route-control problem. For each query, the
system chooses how much to rely on global dense retrieval, lexical BM25 recall,
and cluster-local retrieval. The final response generator is outside the main
experiment scope. The paper evaluates retrieval quality and the token count of
the retrieved context that would be sent to the generator, with one small
downstream generation smoke test.

## 3.2 Piecewise Relevance-Manifold Assumption

The method is motivated by a bounded assumption:

> In vertical-domain evidence retrieval, query-document relevance often
> follows a piecewise local structure induced by domain terminology, semantic
> neighborhoods, document organization, and user intent.

This does not mean that corpus geometry is sufficient by itself. Instead,
IntentWeight uses geometry as one routing signal among several. Dense retrieval
remains a global recall floor, BM25 provides lexical anchors, and cluster-local
retrieval provides local evidence patches.

## 3.3 Multi-Route Retrieval Surface

IntentWeight uses three retrieval routes.

**Dense route.** The dense route performs global dense retrieval over the
selected corpus using cosine similarity in embedding space. It is the primary
quality baseline and the main recall floor.

**BM25 route.** The BM25 route performs global lexical retrieval. It supports
exact-match and terminology-sensitive queries and provides a lexical alternative
when dense similarity is insufficient.

**Cluster-local route.** The cluster-local route performs dense retrieval within
LinUCB-selected cluster arms. It allows the system to exploit local structure
without searching the entire corpus as aggressively.

The routes are fused in the retrieval layer. The system can run in a full
multi-route mode, a gated cost-aware mode, or a final context compaction mode.
Full multi-route retrieval improves coverage but does not automatically reduce
final context tokens. The final context policy described below is the mechanism
that converts route confidence into retrieved-context token savings.

Figure 1 summarizes this route-control architecture. It should be read as a
controller diagram rather than a claim that any single retrieval route is
removed: dense retrieval remains a fallback, while LinUCB and confidence
signals decide when cluster-local evidence is reliable enough for context
compaction.

## 3.4 Cluster Arms

Corpus chunk embeddings are clustered with KMeans or MiniBatchKMeans. This is a
deliberate experimental choice. LinUCB requires a fixed number of arms, fixed
arms improve reproducibility across seeds and scales, and KMeans is fast enough
for large-scale LoTTE experiments. The same arm count is used across LoTTE
scales to keep the LinUCB state space comparable, even though larger corpora
therefore contain more chunks per arm.

The paper does not claim that KMeans is the best clustering algorithm for
retrieval. HDBSCAN, graph clusters, or learned routing structures may be better
in some deployments, but dynamic arm counts complicate the current LinUCB setup.
Here, each cluster arm represents a local region of the retrieval surface. The
cluster route searches inside selected arms, while dense and BM25 routes can
rescue cases where the cluster route misses relevant evidence.

## 3.5 LinUCB Route Policy

For each query $q_t$, IntentWeight computes a context feature vector
$x_t \in \mathbb{R}^{p}$. Features include query embedding projections, route
confidence signals, and local geometry signals. For each arm
$a \in \mathcal{A}$, LinUCB maintains a linear value model:

$$
\begin{aligned}
\hat{\theta}_a &= A_a^{-1} b_a, \\
s_t(a) &= \hat{\theta}_a^\top x_t
        + \alpha \sqrt{x_t^\top A_a^{-1} x_t}.
\end{aligned}
$$

The first term estimates the arm value under the current query context. The
second term is an exploration bonus. The parameter $\alpha$ controls the
exploration-exploitation balance: larger values encourage the policy to explore
arms whose value estimate is uncertain.

The policy selects the top candidate arms by score. The selected arms define
the cluster-local retrieval path and provide confidence signals for later
context compaction.

## 3.6 Trust-Weighted Feedback

IntentWeight models feedback as a noisy signal rather than a perfect oracle. In
the trust-weighted mode, each simulated user feedback event is assigned a trust
weight. Higher-trust feedback contributes more to the arm update and local
feedback memory. Lower-trust feedback has a weaker effect.

Conceptually:

$$
\begin{aligned}
r_t &= g_t - \lambda c_t, \\
\tilde{r}_t &= \tau_t r_t, \\
A_a &\leftarrow A_a + \tau_t x_t x_t^\top, \\
b_a &\leftarrow b_a + \tilde{r}_t x_t.
\end{aligned}
$$

Here, $g_t$ is the retrieval-quality signal, $c_t$ is the cost penalty,
$\lambda$ controls the quality-cost trade-off, $\tau_t$ is the feedback trust
weight, and $\tilde{r}_t$ is the weighted reward applied to the selected arm.

The current experiments do not claim that real human feedback was collected.
They show that under controlled simulated feedback, the route policy can
self-improve. The strongest feedback evidence is visible in policy metrics such
as last true reward and selected-cluster hit rate, especially when final
retrieval quality is already protected by dense and BM25 fallback.

## 3.7 Route-Level Credit Assignment

Early experiments used final fused retrieval success as the reward signal. This
can over-credit the selected cluster arm when dense or BM25 rescue the final
ranking. IntentWeight therefore uses a stricter `cluster_only` reward
attribution mode in the main policy-learning experiments. The LinUCB arm is
updated using the quality of its own cluster-local route.

This distinction is important. The final fused ranking measures the system
outcome, while cluster-only reward measures whether LinUCB is learning a better
route. Dense and BM25 rescue paths protect final quality; cluster-only credit
assignment tests whether the adaptive component itself is improving.

## 3.8 Prequential Adaptation Protocol

The evaluation uses a no-leakage prequential protocol. For each query $q_t$,
the current policy state is frozen before retrieval. The system ranks
candidates, constructs the final context, and is evaluated against ground-truth
evidence. Only after this evaluation is the ground-truth label converted into
simulated feedback and used to update the LinUCB state for later queries.

This means feedback for $q_t$ cannot improve the ranking of $q_t$ itself.
Earlier feedback can influence later queries, but future query feedback is not
available to the current policy. The protocol should therefore be described as
simulated test-time adaptation, not as offline IID held-out generalization.

Several repeated-feedback experiments use multiple prequential epochs over the
same query stream to simulate repeated interactions. Each epoch preserves the
same discipline: rank and evaluate the current query before applying feedback
from that query. Multi-epoch results are therefore controlled repeated
interaction studies. They should not be over-interpreted as single-pass
generalization results.

## 3.9 Confidence-Based Final Context Compaction

Preliminary token-cost analysis showed that reducing source candidates does not
automatically reduce final context tokens. IntentWeight therefore adds an
explicit final context policy.

The conservative `confidence_topk` policy works as follows:

1. If route confidence is low or semantic drift is high, keep dense fallback and
   the normal top-10 context.
2. If LinUCB confidence is high, reduce final context size from the default
   top-10 to $k=8$.
3. If confidence is mid-level, keep $k=10$ as a safety tier rather than calling
   it true compression.
4. Report the actual retrieved context token count, not only candidate counts.

For the conservative policy, the effective compaction rate is therefore the
high-confidence compression rate, not the broader rate of queries that enter a
non-fallback route. Hybrid-lite can reduce dense influence in fusion while
retaining dense candidates as a safety net; it should not be described as
reducing dense computation unless the global dense route is actually skipped.

The main result uses this conservative confidence-based policy. It reduces
final context tokens by about 4.7-5.3% across LoTTE 100k, 200k, 400k, and 638k
while preserving dense-level $\mathrm{Hit@10}$, with mean above-dense
$\mathrm{Hit@10}$ on 200k, 400k, and 638k.

## 3.10 Algorithm Sketch

Input: query $q_t$, corpus $D$, route artifacts, and the current LinUCB state.

1. Embed $q_t$ and compute context features $x_t$.
2. Score cluster arms with LinUCB using $s_t(a)$.
3. Retrieve candidates from the global dense route, the global BM25 route, and
   dense search within selected cluster arms.
4. Fuse route rankings.
5. Apply confidence-based final context policy.
6. Evaluate retrieval quality for $q_t$.
7. Only after evaluation, convert the ground-truth label into simulated
   feedback and update LinUCB for later queries.

Output: final retrieved context $C_t$ and updated policy state.

---

# 4. Experimental Setup

## 4.1 Datasets

The experiments use several datasets, but they have different roles. The paper
does not treat all datasets as equal evidence for the main claim.

**Table 1. Dataset roles and evaluation guardrails.**

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

- $\mathrm{Hit@K}$: whether any ground-truth chunk appears in the top $K$.
- $\mathrm{EvidenceRecall@K}$: fraction of all ground-truth chunks retrieved.
- $\mathrm{MRR@K}$: reciprocal rank of the first relevant chunk.
- $\mathrm{nDCG@K}$: binary relevance ranking quality.

For query $q_t$, let $G_t$ be the set of ground-truth chunks and let $R_t^K$
be the top-$K$ retrieved chunks. The query-level hit metric is:

$$
\mathrm{Hit@K}(q_t) =
\mathbb{1}\left[ R_t^K \cap G_t \neq \varnothing \right].
$$

The evidence-recall metric is:

$$
\mathrm{EvidenceRecall@K}(q_t) =
\frac{\left| R_t^K \cap G_t \right|}{\left|G_t\right|}.
$$

For mean reciprocal rank, let $\rho_t$ be the rank of the first relevant chunk
within the top-$K$ list, or $\infty$ if no relevant chunk is retrieved:

$$
\mathrm{MRR@K}(q_t) =
\begin{cases}
\frac{1}{\rho_t}, & \rho_t \le K, \\
0, & \rho_t = \infty.
\end{cases}
$$

For binary relevance, let $\mathrm{rel}_{t,j} \in \{0,1\}$ denote whether the
chunk at rank $j$ for query $q_t$ is relevant. We compute:

$$
\mathrm{DCG@K}(q_t) =
\sum_{j=1}^{K} \frac{\mathrm{rel}_{t,j}}{\log_2(j+1)},
$$

$$
\mathrm{nDCG@K}(q_t) =
\frac{\mathrm{DCG@K}(q_t)}{\mathrm{IDCG@K}(q_t)}.
$$

If $\mathrm{IDCG@K}(q_t)=0$, we set $\mathrm{nDCG@K}(q_t)=0$.

The main headline uses query-level $\mathrm{Hit@10}$. This choice reflects the
target use case: retrieving at least one usable evidence chunk for RAG
generation under a smaller context budget. It does not imply complete evidence
collection. $\mathrm{EvidenceRecall@10}$ is reported separately where
multi-evidence coverage is important.

Cost and efficiency are separated into three layers:

- Source candidate cost: number of candidates considered before final fusion.
- Dense invocation rate: fraction of queries using the global dense path.
- Final context tokens: token count of retrieved chunks sent to the generator.

The main cost result uses final context tokens. Source candidate cost and dense
invocation rate are retrieval-stage diagnostics.

Let $C_t$ be the final retrieved context selected for query $q_t$ and let
$\mathrm{tok}(d)$ be the token count of chunk $d$. The final context token cost
is:

$$
\mathrm{Tokens}(C_t) =
\sum_{d \in C_t} \mathrm{tok}(d).
$$

## 4.4 Geometry Diagnostics

The geometry diagnostics are used to test whether the corpus has usable local
structure for route control. They are diagnostic support for the
piecewise relevance-manifold assumption, not mathematical proof of a manifold.

Let $E \in \mathbb{R}^{n \times p}$ be a sampled matrix of corpus chunk
embeddings after mean-centering. Let
$\lambda_1 \ge \lambda_2 \ge \cdots \ge \lambda_p \ge 0$ be the eigenvalues of
the empirical covariance matrix. The explained variance retained by the first
$m$ principal components is:

$$
\mathrm{PCAvar@m} =
\frac{\sum_{i=1}^{m} \lambda_i}
     {\sum_{i=1}^{p} \lambda_i}.
$$

The dimension needed to explain 90% of the variance is:

$$
\mathrm{PCAdim90} =
\min \left\{m:
\frac{\sum_{i=1}^{m} \lambda_i}
     {\sum_{i=1}^{p} \lambda_i}
\ge 0.9
\right\}.
$$

For cluster diagnostics, let $y_t$ be the PCA/context representation of query
$q_t$, let $\mu_c$ be the centroid of cluster $c$, and let $\ell_i$ be the
cluster label of chunk $d_i$. The top-$K$ nearest clusters for query $q_t$ are:

$$
\mathcal{N}_K(q_t) =
\operatorname{TopK}_{c}
\left(\mu_c^\top y_t\right).
$$

Let $\mathcal{C}_t = \{\ell_i : d_i \in G_t\}$ be the set of clusters that
contain ground-truth evidence for query $q_t$. The nearest-cluster hit metric
is:

$$
\mathrm{NearestClusterHit@K} =
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}}
\mathbb{1}
\left[
\mathcal{N}_K(q_t) \cap \mathcal{C}_t \neq \varnothing
\right],
$$

where $\mathcal{Q}_{GT}$ is the set of queries with at least one ground-truth
chunk in the evaluated corpus.

Finally, let $R_{t,\mathrm{ctx}}^K$ be the top-$K$ chunks retrieved by inner
product in the PCA/context space, and let $R_{t,\mathrm{dense}}^K$ be the
top-$K$ chunks retrieved by dense embedding similarity. We define:

$$
\mathrm{ContextHit@K} =
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}}
\mathbb{1}
\left[
R_{t,\mathrm{ctx}}^K \cap G_t \neq \varnothing
\right],
$$

and report context retention relative to dense retrieval:

$$
\mathrm{ContextRetention@K} =
\frac{\mathrm{ContextHit@K}}
     {\mathrm{DenseHit@K}}.
$$

If $\mathrm{DenseHit@K}=0$, we set $\mathrm{ContextRetention@K}=0$.

## 4.5 Prequential Simulated Feedback

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

## 4.6 Implementation Notes

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2` with exact
cosine search on CPU. Embeddings and retrieval artifacts are cached to avoid
repeating deterministic computation. Metrics are recomputed from saved
rankings, not copied from prior summaries.

KMeans/MiniBatchKMeans uses a fixed number of arms across scales. This supports
LinUCB comparability and reproducibility, but it is not claimed to be the best
possible clustering design.

---

# 5. Results

## 5.1 Main Token-Quality Frontier

The conservative confidence-based context policy is the main token-efficiency
result because it directly measures final retrieved context tokens. It is
selected as the conservative end of the context-compaction policy frontier.
More aggressive policies show that stronger context reduction is possible at a
visible $\mathrm{Hit@10}$ cost, while the conservative policy prioritizes
quality preservation over maximum token saving.

**Table 2. LoTTE token-quality frontier for the conservative context policy.**

| Scale | Corpus | Dense $\mathrm{Hit@10}$ | Conservative policy $\mathrm{Hit@10}$ | Hit delta | Dense $\mathrm{Tokens@10}$ | Conservative policy $\mathrm{Tokens@10}$ | Token saving |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE 100k | 101311 | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| LoTTE 200k | 201010 | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| LoTTE 400k | 400674 | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| LoTTE 638k | 638509 | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

The 100k result is near dense, with a small $\mathrm{Hit@10}$ drop. At 200k,
400k, and 638k, the conservative policy has mean $\mathrm{Hit@10}$ above dense
while using fewer final context tokens. The result should be framed as
conservative final context compaction, not as aggressive dense replacement.
Figure 2 visualizes the same result as a token-quality frontier across corpus
scale.

## 5.2 Seed Stability

The multi-seed stability analysis reports three-seed diagnostics for the
conservative policy. With only three seeds, these intervals should be presented
as engineering stability diagnostics, not as strong statistical significance
proof.

The 400k token-saving interval is wider than the other scales. We interpret
this as seed-level variance in route confidence and context-budget control, not
as a contradiction of the overall direction. CI-level confirmation of
$\mathrm{Hit@10}$ improvement is strongest at 200k. The 400k and 638k rows
should be reported as mean above-dense results with limited seed counts.

An additional five-seed robustness check extends the LoTTE 100k conservative
policy setting. The five-seed mean is $\mathrm{Hit@10}=0.8708$ versus dense
$0.8674$, with final context token ratio $0.9507\times$. The Hit delta
confidence interval overlaps zero, so this strengthens stability but does not
justify a statistical-superiority claim at 100k.

Appendix A reports the complete three-seed confidence-interval tables and the
five-seed LoTTE 100k extension.

## 5.3 Component Ablation

The component ablation table summarizes which parts of the system provide the
quality floor, routing signal, feedback adaptation, and final token saving on
LoTTE 100k.

**Table 3. LoTTE 100k component ablation.**

| Component | Role | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | $\mathrm{Tokens@10}$ | Token ratio | Dense rate | LinUCB rate | Cluster hit | Last reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | Quality floor | 0.8674 | 0.7026 | 1472.39 | 1.0000 | - | - | - | - |
| BM25-only | Lexical baseline | 0.7232 | 0.5240 | 1745.12 | 1.1852 | - | - | - | - |
| Dense+BM25 hybrid | Static fusion | 0.8624 | 0.6848 | 1705.46 | 1.1583 | - | - | - | - |
| No feedback gated | Dense/full fallback control | 0.8826 | 0.7246 | 1561.15 | 1.0603 | 1.0000 | 0.0000 | 0.1553 | 0.1516 |
| Equal noisy feedback | No trust weighting | 0.8641 | 0.6604 | 1423.84 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | Default trust scoring | 0.8641 | 0.6661 | 1399.51 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | Best controlled-noise point | 0.8775 | 0.6795 | 1362.68 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Conservative final policy | Main conservative policy | 0.8652 | 0.6737 | 1401.24 | 0.9517 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Oracle feedback | Upper bound | 0.8758 | 0.6768 | 1327.03 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Dense-only remains the quality floor. BM25-only is weaker as a standalone
retriever, and static dense+BM25 hybrid is near dense but uses more final
context tokens. No-feedback gated routing has high $\mathrm{Hit@10}$ because it
falls back to full dense/multi-route retrieval; it does not learn efficient
route control.
Trust-weighted feedback improves policy internals relative to equal noisy
feedback, especially selected-cluster hit and last true reward. The oracle row
shows the upper bound under clean feedback.

## 5.4 Feedback Self-Evolution

The feedback experiments show that final $\mathrm{Hit@10}$ can be saturated by
dense and BM25 rescue routes, making feedback gains less visible in the fused
final ranking. The strongest evidence for LinUCB self-evolution is therefore in
route-policy metrics rather than only final $\mathrm{Hit@10}$.

**Table 4. Feedback self-evolution summary on LoTTE 100k.**

| Feedback mode | $\mathrm{Hit@10}$ | Token ratio | Dense rate | LinUCB rate | Selected-cluster hit | Last true reward |
|---|---:|---:|---:|---:|---:|---:|
| Equal noisy feedback | 0.8641 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | 0.8641 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | 0.8775 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Oracle feedback | 0.8758 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

Under default noisy feedback, trust weighting improves selected-cluster hit from
$0.5979$ to $0.7223$ and last true reward from $0.7517$ to $0.8328$ relative to
equal noisy feedback. Under mild trust-weighted noise, selected-cluster hit
reaches $0.7908$, last true reward reaches $0.8820$, dense rate falls to
$0.5826$, and final context token ratio falls to $0.9255\times$.

This supports the feedback self-evolution claim in a bounded form: controlled
trust-weighted simulated feedback improves the route-policy value field. It
does not prove that real human feedback has already been solved.

## 5.5 Secondary Dataset Evidence

The main paper claim is evaluated on LoTTE because it provides the cleanest
large-scale vertical retrieval setting for token-quality analysis. Other
datasets are used as supporting evidence and boundary cases rather than as
equal main benchmarks.

PubMedQA and Banking77 support the feedback self-evolution mechanism. In both
cases, final retrieval quality is already close to ceiling, so the important
signal is not only final $\mathrm{Hit@10}$ but also last true reward and
selected-cluster hit. PubMedQA is an evidence-retrieval proof-of-concept with
section-level ground truth, while Banking77 is better understood as an
intent-routing proxy.

eManual and CUAD are useful because they prevent overclaiming. eManual has
18,812 corpus chunks but only 1,729 unique text strings; many ground-truth
references share duplicate text. Under strict chunk-id evaluation, dense
retrieval reaches only $\mathrm{Hit@10}=0.3231$, but text-equivalent dense
evaluation reaches $0.5615$, and the deduplicated corpus baseline reaches
$0.8615$. This indicates that strict IDs can mark semantically equivalent
retrievals as wrong. CUAD remains a sparse smoke case using a GT-anchored
sample, so it should be reported only as a stress/limitation result.

Appendix D reports the full secondary-dataset table and the eManual
duplicate-text diagnostic.

## 5.6 Geometry Diagnostics

The geometry scale diagnostic validates whether LoTTE retains usable local
geometry as scale grows.

**Table 5. LoTTE geometry diagnostics across corpus scale.**

| Scale | $\mathrm{PCAdim90}$ sample | $\mathrm{PCAvar@64}$ sample | $\mathrm{NearestClusterHit@3}$ | $\mathrm{ContextRetention@10}$ | Conservative policy hit delta |
|---|---:|---:|---:|---:|---:|
| 100k | 182 | 0.6437 | 0.8870 | 0.9033 | -0.22 pp |
| 200k | 186 | 0.6292 | 0.8697 | 0.8947 | +2.80 pp |
| 400k | 190 | 0.6110 | 0.9016 | 0.8826 | +1.01 pp |
| 638k | 196 | 0.5867 | 0.9016 | 0.8571 | +1.85 pp |

$\mathrm{NearestClusterHit@3}$ remains high, around 0.87-0.90, suggesting
local geometry is useful for routing. $\mathrm{PCAdim90}$ increases and
$\mathrm{PCAvar@64}$ decreases with scale, suggesting the representation
geometry becomes more complex. Context retention declines with scale, showing
that geometry alone should not replace dense retrieval.

These diagnostics support the piecewise relevance-manifold framing as a useful
motivation and diagnostic, not as a theorem.
Figure 3 visualizes the geometry trend: nearest-cluster hit remains high, while
context retention and PCA concentration decline as the corpus grows.

## 5.7 Encoder Robustness

The encoder robustness check tests whether the result depends on the exact
`all-MiniLM-L6-v2` encoder. With
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned MiniLM-family
encoder, the dense baseline becomes stronger on LoTTE 100k: $\mathrm{Hit@10}$
increases to $0.8809$. IntentWeight still reaches mean
$\mathrm{Hit@10}=0.8853$ under the conservative policy and reduces final
context tokens by $3.35\%$.

This reduces the single-encoder risk but does not eliminate it. The result
shows same-resource-class robustness within a MiniLM family; it does not prove
the claim for all stronger encoders, rerankers, or late-interaction models.
Appendix E reports the complete robustness table.

## 5.8 Downstream Generation Smoke

The downstream generation smoke test compares dense top-10 context with the
compressed conservative-policy context on 60 sampled LoTTE 100k queries using
`deepseek-v4-flash` with thinking enabled.

The smoke does not show obvious answer-quality degradation from conservative
context compaction. Dense has a small average-score and relevance edge, so this
should not be overclaimed as the conservative policy beating dense in generated
answer quality. It is a sanity check, not a replacement for the retrieval and
final-context-token experiments. Appendix F reports the full smoke table.

---

# 6. Discussion

## 6.1 Supported Claim

IntentWeight supports a bounded but useful claim. It is a feedback-driven
adaptive evidence-selection controller instantiated as a retrieval controller
in the evaluated QA setting. It can control final context budget while
preserving dense-level retrieval quality. On LoTTE technology/search, the
conservative confidence-based context policy reduces final retrieved context
tokens by about 4.7-5.3% from 100k to 638k corpus chunks. Mean
$\mathrm{Hit@10}$ is above dense-only retrieval on 200k, 400k, and 638k.

This result is not a claim that dense retrieval is weak. Dense retrieval remains
the primary quality baseline and an important recall floor. The value of
IntentWeight is that it learns when dense fallback is needed, when local
geometry is reliable, and when the final context can be safely compacted.

## 6.2 Why Multi-Route Retrieval Alone Is Not Enough

A static combination of dense, BM25, and cluster-local retrieval can improve
coverage, but it does not automatically reduce final context tokens. In fact,
static dense+BM25 hybrid retrieval can use more context tokens than dense-only
retrieval because it surfaces longer or noisier chunks. The token-saving
mechanism is therefore not "more routes." It is confidence-based final context
control.

The main confidence-based policy is intentionally conservative. It compresses
only high-confidence cases to $k=8$ and keeps mid-confidence cases at $k=10$.
This is why the saving is modest but stable. More aggressive configurations
save more tokens, but they produce visible $\mathrm{Hit@10}$ loss. The
conservative policy should therefore be interpreted as a safe operating point
on a token-quality frontier.

## 6.3 Feedback Improves the Policy Field

Dense and BM25 fallback can saturate final $\mathrm{Hit@10}$. This can hide the
effect of feedback in final fused retrieval metrics. The clearer feedback
signal appears in route-policy metrics such as selected-cluster hit and last
true reward.

Trust weighting improves these policy metrics under controlled simulated
feedback. This supports the idea that the system can self-improve under a
usable feedback signal. However, the current feedback is simulated and
ground-truth-derived. Production systems still need real feedback collection,
trust scoring, delayed-feedback handling, and safeguards against unreliable or
adversarial signals.

## 6.4 Geometry Is Useful but Not Sufficient

The geometry diagnostics support a piecewise relevance-manifold framing.
$\mathrm{NearestClusterHit@3}$ remains high across LoTTE scales, and local
geometry provides useful routing information. However, context retention
declines with scale, and geometry alone is not a complete retrieval model. If a
cluster route prunes too early, correct evidence can be lost.

IntentWeight therefore uses geometry as one signal in a controller. Dense
retrieval remains a fallback, BM25 provides lexical anchors, and LinUCB learns
route confidence over repeated interactions.

## 6.5 Evidence Completeness Versus Usable Evidence

The main retrieval headline is query-level $\mathrm{Hit@10}$. This metric asks
whether at least one relevant chunk appears in the final context. It is
appropriate for many RAG settings where one good supporting chunk is enough to
ground an answer. However, context compaction can reduce
$\mathrm{EvidenceRecall@10}$, the fraction of all GT chunks retrieved.

This is an expected trade-off. IntentWeight optimizes usable evidence under a
smaller context budget, not exhaustive evidence collection. For legal review,
medical synthesis, or compliance workflows where complete evidence coverage is
required, the system should use a more conservative context policy or disable
compaction.

## 6.6 Production Interpretation

The measured 4.7-5.3% token reduction is conservative. It is measured with
limited simulated interaction history and a cautious $k=8$ high-confidence
compression policy. In production, repeated query patterns, user-specific
feedback, and richer confidence tiers may increase the fraction of queries that
can be safely compacted. This is a hypothesis for production evaluation rather
than a claim proven by the current experiments.

The correct deployment interpretation is therefore:

- keep dense retrieval as a recall floor;
- use feedback and confidence to reduce final context when the policy is stable;
- monitor evidence quality and fallback rates;
- avoid aggressive compaction for complete-evidence tasks;
- treat token saving as a controllable frontier rather than a fixed guarantee.

---

# 7. Limitations and Future Work

## 7.1 Simulated Feedback

The current experiments use simulated feedback derived from ground truth and
controlled noise/trust settings. This validates whether the policy can improve
under a feedback signal, but it does not prove the same behavior under real
human feedback. Real deployments must handle delayed feedback, biased implicit
signals, adversarial or low-quality users, and non-stationary intent.

## 7.2 Limited Generation Evaluation

The main experiments evaluate retrieval and final retrieved context tokens.
A 60-query LLM generation smoke test shows no obvious answer-quality
degradation from conservative context compaction, but this is not a full
end-to-end human evaluation. The supported main claim remains evidence
retrieval and retrieved context budget, not generated answer superiority or
user satisfaction.

## 7.3 Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentWeight should not be
claimed as a universal replacement for dense retrieval. The evidence supports a
controller that can reduce final context tokens while preserving dense-level
$\mathrm{Hit@10}$ in the main LoTTE setting, and that can expose a quality-cost
frontier across routes.

## 7.4 Evidence Completeness Trade-Off

The main retrieval headline is query-level $\mathrm{Hit@10}$. Final context
compaction can preserve whether at least one relevant chunk is retrieved while
reducing the fraction of all ground-truth chunks retrieved. For tasks that
require complete evidence collection, such as legal review, medical evidence
synthesis, or exhaustive compliance analysis, a more conservative context
policy or no compaction may be preferable.

## 7.5 Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
$\mathrm{NearestClusterHit@3}$, PCA spectrum, and context retention. These
diagnostics do not prove a mathematical manifold theorem. They show that local
geometry is informative for routing on LoTTE, while dense retrieval remains
necessary.

## 7.6 KMeans Is an Experimental Arm Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and
the experiments need reproducible, scalable arms. This is not a claim that
KMeans is the best clustering method for all RAG systems. HDBSCAN or
graph-based clusters may perform better in some deployments, but dynamic arm
counts complicate the current LinUCB setup.

## 7.7 Limited Encoder and Domain Coverage

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2`. The
paper adds a CPU-friendly encoder robustness check with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, but the paper should not
generalize the result to stronger domain-specific encoders, rerankers, or
late-interaction models without additional experiments.

LoTTE technology/search is the main positive large-scale domain. Additional
LoTTE domains or other vertical corpora would strengthen external validity.

## 7.8 Seed Count and 400k Variance

The stability analysis reports three-seed confidence intervals across LoTTE
100k-638k, and an additional robustness check extends LoTTE 100k to five seeds.
These are useful engineering stability diagnostics, but they should not be
over-framed as strong statistical significance proof. The LoTTE 400k
token-saving interval is notably wider than the other scales and should be
interpreted as seed-level variance in route confidence and context-budget
control.

## 7.9 Future Work

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- larger end-to-end LLM answer-quality and citation-faithfulness studies;
- stronger dense encoders, rerankers, and late-interaction retrieval models;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- larger seed counts and additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.

---

# 8. Conclusion

This paper presents IntentWeight, a feedback-driven adaptive evidence-selection
controller motivated by a piecewise relevance-manifold assumption. In the
evaluated retrieval-backed QA implementation, IntentWeight builds a multi-route
retrieval surface over dense, BM25, and cluster-local retrieval, uses
trust-weighted LinUCB to learn route preferences from controlled feedback, and
applies confidence-based final context compaction to reduce retrieved context
tokens.

The main evidence comes from LoTTE technology/search at 100k to 638k corpus
chunks. Under the conservative confidence-based context policy, IntentWeight
reduces final retrieved context tokens by approximately 4.7-5.3% while
preserving dense-level $\mathrm{Hit@10}$. Mean $\mathrm{Hit@10}$ is above
dense-only retrieval at 200k, 400k, and 638k. Additional diagnostics show that
local geometry provides useful routing signal, trust-weighted feedback improves
route-policy metrics, and a small downstream generation smoke test does not
show obvious answer-quality degradation from context compaction.

The result is intentionally bounded. IntentWeight is not a universal dense
replacement, and it does not prove that geometry alone solves retrieval. Dense
retrieval remains an important recall floor. The contribution is a controller
that learns when multiple retrieval routes and route confidence can be used to
preserve retrieval quality while reducing the final context budget.

---

# Appendix

## A. Seed Stability Diagnostics

The conservative confidence-based context policy is evaluated with three seeds
at every LoTTE scale. These intervals are engineering stability diagnostics,
not strong inferential proof: each scale has only three observations.

**Appendix Table A1. Multi-seed retrieval-quality stability.**

| Scale | Dense $\mathrm{Hit@10}$ | Policy $\mathrm{Hit@10}$ mean | Std | 95% CI | Mean hit delta |
|---|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | 0.0035 | [0.8565, 0.8739] | -0.0022 |
| 200k | 0.7970 | 0.8249 | 0.0079 | [0.8052, 0.8446] | +0.0280 |
| 400k | 0.7718 | 0.7819 | 0.0044 | [0.7709, 0.7929] | +0.0101 |
| 638k | 0.7282 | 0.7466 | 0.0089 | [0.7246, 0.7687] | +0.0185 |

**Appendix Table A2. Multi-seed final context-token stability.**

| Scale | Dense $\mathrm{Tokens@10}$ | Policy $\mathrm{Tokens@10}$ mean | Std | 95% CI | Mean token saving | Saving 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 1472.39 | 1401.24 | 11.49 | [1372.70, 1429.79] | 4.83% | [2.89%, 6.77%] |
| 200k | 1444.12 | 1376.46 | 4.61 | [1365.01, 1387.91] | 4.69% | [3.89%, 5.48%] |
| 400k | 1482.30 | 1403.43 | 31.10 | [1326.16, 1480.69] | 5.32% | [0.11%, 10.53%] |
| 638k | 1525.62 | 1451.49 | 3.83 | [1441.97, 1461.00] | 4.86% | [4.24%, 5.48%] |

The token-saving direction is consistent across scales. The wider 400k token
interval should be interpreted as route-confidence and context-budget variance,
not hidden as a uniform result.

A five-seed extension is also available for LoTTE 100k. The additional seeds
test sensitivity to KMeans initialization and route-policy stochasticity.

**Appendix Table A3. Five-seed LoTTE 100k extension.**

| Setting | Seeds | $\mathrm{Hit@10}$ | Avg $\mathrm{Tokens@10}$ | Token ratio vs dense | Token saving |
|---|---:|---:|---:|---:|---:|
| Dense-only | 1 | 0.8674 | 1472.39 | 1.0000x | 0.00% |
| Conservative policy | 5 | 0.8708 | 1399.83 | 0.9507x | 4.93% |

The five-seed hit-delta interval is $[-0.0082, +0.0150]$. This supports
dense-level retrieval quality with stable context-token reduction, not a
statistical-superiority claim.

## B. Static Retrieval Baselines

Dense retrieval is the primary quality baseline. BM25 supplies lexical
coverage, but it is weaker as a standalone retriever on LoTTE. Static
dense-plus-BM25 reciprocal-rank fusion is competitive at some scales but does
not consistently dominate dense.

**Appendix Table B1. Static LoTTE retrieval baselines across corpus scale.**

| Scale | Corpus chunks | BM25 $\mathrm{Hit@10}$ | Dense $\mathrm{Hit@10}$ | Static hybrid $\mathrm{Hit@10}$ |
|---|---:|---:|---:|---:|
| 100k | 101311 | 0.7232 | 0.8674 | 0.8624 |
| 200k | 201010 | 0.6292 | 0.7970 | 0.8003 |
| 400k | 400674 | 0.5721 | 0.7718 | 0.7617 |
| 638k | 638509 | 0.5084 | 0.7282 | 0.7181 |

The declining dense score as corpus scale grows motivates adaptive context
control, but it does not make dense retrieval obsolete. Dense remains an
important recall floor and fallback route in IntentWeight.

## C. Cost-Metric Guardrail

The experiments separate three efficiency layers:

1. source candidate cost: candidates considered before final fusion;
2. dense invocation rate: fraction of queries using global dense retrieval;
3. final context tokens: retrieved chunk tokens sent to the generator.

The main paper claim uses the third layer. Historical routing experiments
showed that reducing candidate counts does not automatically reduce final
context tokens when the final context remains fixed at top-10.

**Appendix Table C1. Representative fixed-top-10 correction audit.**

| Dataset / scale | Routing setting | $\mathrm{Hit@10}$ | Avg $\mathrm{Tokens@10}$ | Ratio vs dense | Source candidate cost |
|---|---|---:|---:|---:|---:|
| Banking77 | Gated cost-aware routing | 0.9813 | 120.82 | 0.9978x | 142.51 |
| eManual | Gated cost-aware routing | 0.0116 | 17.92 | 0.9829x | 214.07 |
| LoTTE 100k | Quality-first routing | 0.8770 | 1518.44 | 1.0313x | 229.97 |
| LoTTE 100k | Conditional fallback routing | 0.8747 | 1516.24 | 1.0298x | 227.29 |
| LoTTE 100k | Cluster-credit routing | 0.8764 | 1550.65 | 1.0532x | 181.47 |
| LoTTE 200k | Initial gated routing | 0.8154 | 1549.39 | 1.0729x | 232.01 |
| LoTTE 400k | Initial gated routing | 0.7836 | 1547.66 | 1.0441x | 233.22 |
| LoTTE 638k | Initial gated routing | 0.7343 | 1599.95 | 1.0487x | 236.22 |

This audit motivated the explicit confidence-based final context policy. Its
token savings come from reducing selected final context size in
high-confidence cases, not from treating candidate-count savings as prompt
token savings.

## D. Secondary Datasets and Boundary Cases

The secondary datasets have different roles. PubMedQA supports the
evidence-retrieval mechanism near a dense ceiling. Banking77 is an
intent-routing proxy rather than an evidence-retrieval benchmark. eManual and
CUAD are boundary cases that prevent universal claims.

**Appendix Table D1. Secondary dataset evidence and boundary cases.**

| Dataset | Role | Dense/reference $\mathrm{Hit@10}$ | Supporting or diagnostic result | Interpretation |
|---|---|---|---|---|
| PubMedQA | Evidence retrieval proof-of-concept | 0.9930 | Trust-weighted $\mathrm{Hit@10}=0.9940$, last reward $0.8727$, selected-cluster hit $0.8860$ | Feedback improves policy internals near a dense ceiling; GT is abstract-level context. |
| Banking77 | Intent routing proxy | 0.9805 | Trust-weighted $\mathrm{Hit@10}=0.9844$, last reward $0.9805$, selected-cluster hit $0.9983$ | Strong intent structure; do not mix with evidence-retrieval headline results. |
| eManual | Duplicate-text limitation | 0.3231 strict; 0.5615 text-equivalent | Deduplicated dense $\mathrm{Hit@10}=0.8615$ | Strict chunk IDs understate success because many evidence texts are duplicated. |
| CUAD | Sparse legal smoke/stress case | 0.0759 | Trust-weighted smoke $\mathrm{Hit@10}=0.0886$ | GT-anchored sample only; do not treat as positive full-corpus evidence. |

### D.1 eManual Duplicate-Text Diagnostic

eManual contains 18,812 corpus chunks but only 1,729 unique text strings.
Strict chunk-id evaluation can therefore mark semantically equivalent
retrievals as incorrect.

**Appendix Table D2. eManual strict, text-equivalent, and deduplicated
evaluation.**

| Method | Evaluation mode | $\mathrm{Hit@10}$ | $\mathrm{MRR@10}$ | $\mathrm{nDCG@10}$ |
|---|---|---:|---:|---:|
| BM25 | Strict chunk ID | 0.1154 | 0.0244 | 0.0256 |
| BM25 | Text-equivalent | 0.3846 | 0.3059 | 0.1620 |
| Dense | Strict chunk ID | 0.3231 | 0.0551 | 0.0526 |
| Dense | Text-equivalent | 0.5615 | 0.4716 | 0.2030 |
| Static hybrid | Strict chunk ID | 0.1692 | 0.0366 | 0.0287 |
| Static hybrid | Text-equivalent | 0.5846 | 0.4895 | 0.2263 |
| Dense | Deduplicated corpus | 0.8615 | 0.5736 | 0.3807 |

The text-equivalent and deduplicated metrics are diagnostics, not replacements
for the strict evaluation. They show that eManual's low strict score cannot be
interpreted as proof that useful local structure is absent.

## E. Encoder Robustness

The main scale-up uses `sentence-transformers/all-MiniLM-L6-v2`. A LoTTE 100k
robustness check replaces it with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, a QA-tuned MiniLM-family
encoder with the same 384-dimensional embedding size and a similar
CPU-friendly resource class.

**Appendix Table E1. QA-tuned MiniLM-family encoder robustness.**

| Method | $\mathrm{Hit@10}$ | $\mathrm{MRR@10}$ | $\mathrm{nDCG@10}$ | $\mathrm{EvidenceRecall@10}$ | Avg $\mathrm{Tokens@10}$ | Token ratio vs dense |
|---|---:|---:|---:|---:|---:|---:|
| Dense-only | 0.8809 | 0.7220 | 0.6616 | 0.7163 | 1514.51 | 1.0000x |
| Conservative policy | 0.8853 | 0.7118 | 0.6291 | 0.6789 | 1463.71 | 0.9665x |

Under the QA-tuned encoder, the dense baseline becomes stronger and the
conservative policy still preserves dense-level query hit while reducing final
context tokens by 3.35%. Ranking metrics and evidence recall are lower than
dense, so this is a bounded robustness result rather than a universal
retrieval-metric improvement.

## F. Downstream Generation Smoke

A small downstream generation smoke compares dense top-10 context with the
compressed conservative-policy context on 60 sampled LoTTE 100k queries. The
same LLM configuration generates and judges answers in this smoke.

**Appendix Table F1. Downstream generation smoke test.**

| Method | Answer score | Faithfulness | Answer relevance | Win count | Prompt context-token proxy ratio |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 4.4000 | 4.6500 | 4.6500 | 14 | 1.0000x |
| Conservative policy | 4.2833 | 4.6333 | 4.4500 | 14 | 0.9321x |
| Tie | - | - | - | 32 | - |

The smoke does not show obvious answer-quality degradation from conservative
context compaction. It is not a full human evaluation: the sample is small,
one generator/judge model is used, and LLM-as-judge can be biased.

## G. Reproducibility and Reporting Guardrails

The following rules apply when migrating the draft into a submission template:

- report query-level $\mathrm{Hit@10}$ as the primary retrieval headline;
- report $\mathrm{EvidenceRecall@10}$ separately for complete-evidence tasks;
- use final retrieved context tokens for prompt-context efficiency claims;
- label source candidate cost and dense invocation rate as retrieval-stage
  diagnostics;
- describe multi-epoch prequential adaptation as simulated repeated
  interaction, not IID held-out generalization;
- describe feedback as controlled simulation, not collected production
  feedback;
- describe geometry diagnostics as support for a piecewise local-structure
  interpretation, not theorem-level manifold proof;
- keep dense retrieval visible as a recall floor and fallback route.
