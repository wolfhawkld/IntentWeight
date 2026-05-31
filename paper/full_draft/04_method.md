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
