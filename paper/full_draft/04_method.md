# 3. Method

## 3.1 Problem Formulation

In the retrieval-backed implementation evaluated here, let an evidence corpus
be a set of chunks $D = \{d_i\}_{i=1}^{N}$ and a query stream
$Q = \{q_t\}_{t=1}^{T}$. For each query $q_t$, a retrieval system returns an
ordered context $C_t = [d_{t,1}, \ldots, d_{t,k}]$ that will be passed to a
downstream generator. The objective is to preserve retrieval quality while
controlling both retrieval cost and final context cost.

IntentRoute separates confidence-gated routing from final-context budgeting.
For each query, the system estimates how much to rely on global dense retrieval,
lexical BM25 recall, and cluster-local retrieval. A separately calibrated policy
then budgets the resulting ranked evidence. Retrieval quality and final context tokens remain the
primary mechanism-level outcomes; a frozen 300-query generation-and-judge
experiment evaluates whether the same trade-off reaches answer-level behavior.

## 3.2 Piecewise Relevance-Manifold Assumption

The method is motivated by a bounded assumption:

> In vertical-domain evidence retrieval, query-document relevance often
> follows a piecewise local structure induced by domain terminology, semantic
> neighborhoods, document organization, and user intent.

This does not mean that corpus geometry is sufficient by itself. Instead,
IntentRoute uses geometry as one routing signal among several. Dense retrieval
remains a global recall floor, BM25 provides lexical anchors, and cluster-local
retrieval provides local evidence patches.

## 3.3 Multi-Route Retrieval Surface

IntentRoute uses three retrieval routes.

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
final context tokens. The stronger token-saving policy described below is
calibrated independently after route construction; it does not convert route
confidence into a per-query token ratio.

Figure 1 summarizes this route-control architecture after the route surface is
defined. It should be read as a controller diagram rather than a claim that
LinUCB replaces dense or BM25 retrieval: dense and BM25 are global recall
routes, LinUCB selects cluster-local arms, and the resulting ranking is passed
to a separately calibrated final context-budget controller.

## 3.4 Routing Arm Construction

Corpus chunk embeddings are clustered with KMeans or MiniBatchKMeans. This is a
deliberate experimental choice. LinUCB requires a fixed number of arms, fixed
arms improve reproducibility across seeds and scales, and KMeans is fast enough
for large-scale LoTTE experiments. The same arm count is used across LoTTE
technology/search scales to keep the LinUCB state space comparable, even though larger corpora
therefore contain more chunks per arm.
We use 32 routing arms as the main reproducible operating point. A sensitivity
study over $K \in \{8,16,32,64,128\}$ shows that full multi-route fused quality
is stable across this range, while retrieval-stage gated routing is more
sensitive because smaller $K$ changes route granularity and larger $K$ spreads
feedback across more arms. We therefore treat 32 as an engineering choice, not
a manifold-derived optimum.

The paper does not claim that KMeans is the best clustering algorithm for
retrieval. HDBSCAN, graph clusters, or learned routing structures may be better
in some deployments, but dynamic arm counts complicate the current LinUCB setup.
Here, each cluster arm represents a local region of the retrieval surface. The
cluster route searches inside selected arms, while dense and BM25 routes can
rescue cases where the cluster route misses relevant evidence.

## 3.5 LinUCB Route Policy

For each query $q_t$, IntentRoute computes a controller context vector
$x_t \in \mathbb{R}^{p}$ by applying a corpus-fitted PCA projection to the
query embedding and then L2-normalizing the projected vector. For each arm
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
the cluster-local retrieval path and provide confidence signals for route
gating and fallback.

### Controller Context and Route-Gating Signals

The tested LinUCB context is deliberately narrow: it is the normalized
PCA-projected query embedding, not a concatenation of dense scores, BM25
scores, route agreement, feedback summaries, or budget variables. The PCA fit
uses corpus embeddings only, so query vectors and fixed KMeans arm centroids
share one controller space.

After LinUCB selects arms from this context, the implementation computes
policy-derived confidence and centroid-based semantic drift as separate
route-gating signals. These signals determine whether the system retains the
full dense/BM25/cluster fusion surface or permits a lighter route with a Dense
floor. Dense and BM25 rankings are then constructed and fused after the route
decision; their score concentration, lexical strength, and route overlap are
not inputs to the tested LinUCB vector. The main calibrated budget remains
separate from these signals and does not map confidence to a per-query token
ratio.

## 3.6 Trust-Weighted Feedback

IntentRoute models feedback as a noisy signal rather than a perfect oracle. In
the trust-weighted mode, each simulated user feedback event is assigned a trust
weight. Higher-trust feedback contributes more to the arm update and local
feedback memory. Lower-trust feedback has a weaker effect.

For a selected source arm, let $o_{t,a}$ be the observed simulated-feedback
reward and let $w_{t,a}$ be its trust- and propagation-weighted update weight.
The tested update is:

$$
\begin{aligned}
A_a &\leftarrow A_a + w_{t,a} x_t x_t^\top, \\
b_a &\leftarrow b_a + w_{t,a} o_{t,a} x_t.
\end{aligned}
$$

The reward is an evidence-quality signal derived from the selected route or
the final fused ranking, according to the declared attribution mode. Trust
weighting changes the update strength, and neighboring arms can receive a
decayed propagated update. Candidate cost and final-context tokens are measured
separately; the tested LinUCB reward does not include a $-\lambda c_t$
cost-penalty term.

The current experiments do not claim that real human feedback was collected.
They evaluate controlled repeated-interaction adaptation and hard-case recovery.
The strongest feedback evidence is visible in policy metrics such as last true
reward and selected-cluster hit rate, especially when final retrieval quality is
already protected by dense and BM25 fallback.

## 3.7 Route-Level Credit Assignment

The implementation supports two attribution modes. `final_fused` assigns reward
from the final fused ranking, whereas `cluster_only` assigns reward from the
selected cluster-local route and avoids crediting Dense/BM25 rescue to that arm.
The common cross-dataset evidence rows and formal frozen-policy audit use
`final_fused` attribution; `cluster_only` is retained for dedicated
credit-assignment and mechanism diagnostics. Every result family reports its
attribution mode in Supplementary Table S29.

This distinction matters because final fused reward measures the system outcome,
while cluster-only reward isolates the cluster-route component. Neither mode
allows Dense/BM25 rescue to be omitted from the interpretation of final quality.

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

The separate frozen-policy audit tests this boundary directly: it trains
policy state on disjoint history folds and ranks held-out queries once with all
updates frozen. It evaluates transferable route-policy behavior, not
final-context budgeting. The audit does not establish a learned-feedback
advantage over matched static-nearest or cold no-feedback full routing, and it
finds that learned cost-aware gating is unsafe as a frozen first-pass policy in
the tested domains.

## 3.9 Final Context Budgeting and Conservative Confidence Baseline

Preliminary token-cost analysis showed that reducing source candidates does not
automatically reduce final context tokens. IntentRoute therefore combines
confidence-gated routing with an explicit calibrated budget policy, the central
quality-cost control interface.

Let $R_t$ be the ranking produced by the confidence-gated route surface. A
calibration policy $\pi_\phi$ selects a token ratio $r \in (0,1]$ and a
mandatory ranked prefix size $m$. The final context begins with that prefix,
then scans the remaining top-10 candidates in rank order and retains a candidate
only when it fits the residual budget:

$$
\mathrm{Tokens}(C_t) \le r\,\mathrm{Tokens}(R_t[:10]).
$$

This is an order-preserving budgeted subset with a mandatory prefix. It may skip
an oversized later chunk and admit a smaller lower-ranked chunk, so it is not
necessarily a contiguous longest ranked prefix. The policy parameters $\phi$
are selected on calibration queries subject to a retrieval-quality eligibility
gate and then frozen before held-out test evaluation. Geometry and feedback
affect route construction, while the stronger token saving arises when the
separately calibrated length budget acts on the routed ranking. The
implementation does not learn a direct per-query mapping from confidence to
token ratio.

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

The main token-quality result uses frozen calibration/test budget policies.
They select a global ratio and minimum-prefix size on calibration queries, then
apply both unchanged to held-out test queries. The conservative
confidence-based policy remains a
stable baseline: it reduces final context tokens by about 4.7-5.3% across LoTTE
technology/search at 100k, 200k, 400k, and 638k while preserving dense-level
query hit.

For the conservative `confidence_topk` baseline only, semantic drift rarely
exceeds the configured fallback threshold, so context-size decisions are
primarily confidence-conditioned. The fixed-pool factorial audit does not show
that this confidence predicts compression safety better than matched controls;
the baseline is an empirical operating point rather than a validated causal
mechanism.

## 3.10 Feedback-Triggered Recovery

IntentRoute can also use feedback as a recovery signal after a compressed
context fails. In this mode, feedback does not insert the missing ground-truth
chunk into the current answer. Instead, it updates arm-level route value and
marks the associated local region as risky for future routing or optional
post-feedback retry.

The safe recovery behavior is conservative:

1. If feedback indicates that a compressed context missed evidence, identify
   the evidence-bearing arm or risky query-arm relation.
2. Prefer a less aggressive final-context budget or full-context fallback for
   that local region.
3. Avoid unconditional global arm boosting, because a feedback-positive arm for
   one query can transfer poorly to unrelated queries.

This recovery mechanism is deployment-facing. It represents how a system can
repair tail failures after user or evaluator feedback, not how the first-pass
ranking is produced before feedback is observed.

## 3.11 Algorithm Sketch

Input: query $q_t$, corpus $D$, route artifacts, and the current LinUCB state.

1. Embed $q_t$ and form the normalized PCA controller context $x_t$.
2. Score cluster arms with LinUCB using $s_t(a)$.
3. Retrieve candidates from the global dense route, the global BM25 route, and
   dense search within selected cluster arms.
4. Fuse route rankings.
5. Apply the independently calibrated final-context budget, or the explicitly
   labeled conservative `confidence_topk` baseline.
6. Evaluate retrieval quality for $q_t$.
7. Only after evaluation, convert the ground-truth label into simulated
   feedback and update LinUCB for later queries.
8. If the interaction is a post-feedback retry or a later query in a risky
   local region, use the updated arm state to choose a safer route or fallback
   path; final-context budgeting remains independently calibrated.

Output: final retrieved context $C_t$ and updated policy state.

## 3.12 Reproducibility Parameters

The common cross-dataset evidence protocol uses 32 fixed KMeans/MiniBatchKMeans arms,
three candidate arms per query, a 64-dimensional context projection,
$\alpha=1.0$, and eight prequential epochs. Earlier mechanism diagnostics may
use other epoch counts and attribution modes; Supplementary Table S29 records
those result-family differences. The calibration grid covers
$r \in \{0.85,0.88,0.90,0.92,0.95,0.98\}$ and
$m \in \{4,\ldots,8\}$. Supplementary Section S12 reports the complete route
depths, safety floors, fusion weights, confidence thresholds, decay, and trust
parameters; scale-specific cache paths and dataset sizes remain in the tracked
experiment artifacts.

The notation `token_budget_r0.85_m4` means that each query keeps a safe prefix
of at least four chunks and then admits additional chunks only while the final
context remains within 85% of the original dense top-10 token budget. The
policy is chosen on calibration queries and then frozen before held-out test
evaluation.
