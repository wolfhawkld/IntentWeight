# IntentRoute: Geometry-Guided and Feedback-Adaptive Route Confidence for Efficient Evidence Selection

<!-- Generated review packet. Edit source chapters under paper/full_draft/. -->

# Abstract

Retrieval-augmented systems must select enough evidence to support an answer
while limiting noise and language-model context cost. We formulate this as a
two-stage route-control and budget-calibration problem. IntentRoute combines
dense retrieval, BM25, geometry-defined cluster-local routes, and
trust-weighted LinUCB feedback. Route confidence controls routing and fallback,
while an independently calibrated policy sets the final context budget. Dense
retrieval remains a recall floor. A bounded piecewise relevance-manifold
hypothesis motivates local route construction; geometry is evaluated as a
diagnostic signal rather than a standalone retrieval theory.

On LoTTE technology/search from 100k to 638k chunks, eligible frozen policies
reduce evidence-context tokens by 6-18% while avoiding the larger
$\mathrm{Hit@10}$ losses of dense-only adaptive truncation; the original 400k
split remains calibration-ineligible. A normalized five-fold 400k follow-up
yields 14.50% mean saving with no mean Hit change, although strict seed-level
non-inferiority remains unestablished. Matched BGE-base and E5-base tests retain
near-dense $\mathrm{Hit@10}$ with about 12% token reduction. Route controls show
that geometry and feedback improve route-level quality, but do not establish
safe per-query compression without calibration and rescue. In a frozen
300-query downstream evaluation, matched variants reduce context by 6-12%.
DeepSeek, GLM-5.2, MiniMax-M3, and majority-vote comparisons show no
statistically detectable correctness difference, while faithfulness remains
method-dependent and degrades for the tested BGE policy. Prompt compression
and reranking remain complementary. The supported contribution is a
geometry-guided, feedback-adaptive route controller with separate budget
calibration, not universal superiority over dense retrieval or proof that
geometry determines relevance.

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

We propose IntentRoute, a feedback-adaptive route-confidence and context-budget
controller. Its central operation is to use confidence to gate a multi-route
evidence pool and then apply a calibrated final-context budget. In our
retrieval-augmented QA implementation, the route surface includes dense
retrieval, BM25 lexical recall, and cluster-local retrieval. A bounded
piecewise relevance-manifold hypothesis motivates the local route construction:
fixed KMeans/MiniBatchKMeans regions form reproducible arms rather than a claim
that geometry alone defines relevance. Trust-weighted LinUCB updates arm values
from controlled feedback, turning user feedback into an adaptive estimate of
which local routes can be trusted. Low route confidence keeps dense retrieval
as a recall floor; the final budget is calibrated separately on the resulting
evidence rankings.
The name IntentRoute denotes route control conditioned on query intent, local
structure, and feedback state; it does not imply a separate intent-classification
stage.

Although the control problem appears in memory, graph, tree, and
retrieval-backed agents, our empirical validation instantiates it in
retrieval-augmented question answering. We therefore use the broader agent
framing as motivation and keep the demonstrated claims tied to retrieval-backed
evidence selection.

This design separates route construction, confidence estimation, and final
context control. Geometry defines a structured local route prior. LinUCB and
trust-weighted feedback adapt route confidence over repeated interactions.
Dense and BM25 rescue paths protect final recall. A separate calibration stage
chooses the final context-budget parameters. A late reranker can improve
candidate ordering, while a sentence or prompt compressor can remove redundant
text after evidence selection. IntentRoute occupies the upstream route-control
and budget-calibration layers and can be composed with those downstream
components.

The same distinction separates three cost layers that are often conflated in RAG
experiments: the number of source candidates considered during retrieval, the
rate at which global dense retrieval is invoked, and the final number of
retrieved context tokens sent to the generator. Our main efficiency claim uses
the third layer. Earlier candidate-count reductions are useful retrieval-stage
diagnostics, but they are not evidence of lower LLM context cost unless the
final context itself is reduced. Because these retrieved chunks enter the LLM
generator as input tokens, each percentage point of evidence-context reduction
translates directly into a proportional per-query inference-cost reduction, a
recurring saving that scales with deployment query volume.

We evaluate IntentRoute on multiple datasets and use LoTTE technology/search
as the main large-scale vertical-domain evidence benchmark. On LoTTE, we scale
from 100k to 638k corpus chunks and compare against dense-only retrieval using
`sentence-transformers/all-MiniLM-L6-v2` with exact cosine search. Our main
cost-quality evidence uses a calibration/test context-budget protocol: the
final-context policy is selected on calibration queries and frozen before test
evaluation. Under this protocol, calibration-eligible operating points at
100k, 200k, and 638k save 6-18% final evidence-context tokens, while a 400k
diagnostic point shows positive frozen-test behavior but does not satisfy the
calibration eligibility gate. A normalized five-fold follow-up yields 14.50%
mean saving with no mean Hit change at 400k, but retains substantial
policy-selection variance. Across these scales, IntentRoute avoids the
larger $\mathrm{Hit@10}$ losses observed under dense-only adaptive truncation,
although strict seed-level non-inferiority remains scale-dependent. A
conservative confidence-only policy provides a stable baseline, reducing final
retrieved context tokens by approximately 4.7-5.3% across all scales while
preserving dense-level query hit. We treat these as bounded operating points
rather than universal or statistically significant dominance claims.

We then test whether the mechanism survives stronger alternatives and direct
component controls. Matched-backbone BGE-base and E5-base comparisons retain
the quality-cost pattern beyond MiniLM, while a BGE quality-first policy shows
that the operating frontier can be moved toward higher retrieval quality at a
smaller token saving. Random-route, static-geometry, no-feedback, and arm-count
ablations separate route confidence from the dense/BM25 rescue surface:
geometry and feedback strongly affect route-level reward and cluster hit, but
final fused $\mathrm{Hit@10}$ can hide weak routes when rescue remains active.
Sentence-MMR and a Selective Context-style prompt-pruning baseline show that
compression is a strong shared downstream layer; a cross-encoder reranker
improves full-context support but can select longer contexts. A 300-query
answer-level evaluation finally compares matched BGE, E5, and SentMMR pipelines
under three LLM judges. No judge or shared-key majority finds a statistically
significant correctness difference, while faithfulness effects remain
method-dependent. LoTTE science/search and feedback-driven hard-case recovery
provide cross-domain and adaptive-recovery evidence, with domain calibration
and simulated-feedback caveats.

The contributions of this paper are:

1. We formulate retrieval-backed evidence selection as a
   confidence-gated-routing and calibrated-budget problem and introduce a
   controller that separates route confidence from final evidence-context size while
   retaining dense retrieval as a recall floor.
2. We operationalize local relevance structure as reproducible cluster arms
   and trust-weighted feedback as adaptive LinUCB route confidence. Geometry
   diagnostics, random/static controls, no-feedback ablations, and arm-count
   sensitivity identify what these components explain and what dense/BM25
   rescue masks.
3. We provide frozen calibration/test evidence from 100k to 638k LoTTE chunks,
   matched BGE/E5 backbones, and a tunable BGE quality-first point, separating
   token reduction from retrieval-quality non-inferiority with paired
   query-level statistics.
4. We compare against shared sentence and prompt compression plus
   cross-encoder reranking, showing that IntentRoute is an upstream controller
   that composes with rather than replaces these downstream layers.
5. We add a 300-query, three-judge answer-level evaluation, cross-domain LoTTE
   replication, controlled feedback recovery, and explicit limitation cases to
   bound the supported quality-cost claim.

The resulting claim is intentionally bounded. IntentRoute is not presented as
a universal replacement for dense retrieval, a proof of a relevance manifold,
or a statistically superior answer generator. It is a feedback-driven
controller that uses local geometry to structure routes, trust-weighted LinUCB
to adapt route confidence, and dense retrieval as a recall floor before a
separately calibrated final context budget. Reranking and context compression remain
compatible downstream layers rather than competing explanations.

---

# 2. Related Work

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
expensive and may become less faithful. IntentRoute is complementary to
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
rank-level fusion method [@cormack2009rrf]. Cross-encoder rerankers provide a
strong late-ranking layer because they jointly score a query and a candidate
passage, but they rerank a retrieved candidate pool rather than searching the
full corpus directly. In this paper, dense retrieval is a strong baseline and
an explicit recall floor, not a weak component to be replaced. BM25 contributes
lexical coverage, cluster-local dense retrieval contributes a structured local
search path, and reranking can be added after candidate generation. The
contribution is not that any single route is best, but that a controller can
learn when and how to combine routes under a final context budget.

## 2.3 Adaptive Retrieval and Contextual Bandits

Many retrieval-augmented systems are configured with fixed hyperparameters: a
fixed top-$k$, a fixed retriever mixture, a fixed reranker, or a fixed fallback
policy. Static configurations are easy to deploy but poorly matched to
heterogeneous query streams. Some queries require exact lexical anchors, others
require semantic expansion, and others can be answered from a smaller local
evidence region.

Several systems adapt retrieval behavior without using contextual bandits.
FLARE performs active retrieval during generation when predicted continuation
tokens have low confidence [@jiang2023flare]. Adaptive-RAG routes questions
among no-retrieval, single-step, and iterative retrieval strategies using a
learned question-complexity classifier [@jeong2024adaptiverag]. Self-RAG trains
a language model to retrieve and critique evidence on demand through reflection
tokens [@asai2024selfrag]. CRAG evaluates retrieved evidence and triggers
corrective actions when retrieval confidence is low [@yan2024crag]. These
methods establish that retrieval behavior should respond to query difficulty,
generation uncertainty, or evidence quality rather than remain fixed.

Contextual bandits provide a natural abstraction for adaptive route control. A
policy observes a context, selects an action, receives feedback, and updates its
future decisions. LinUCB is a simple and interpretable contextual bandit
algorithm that models each arm's expected reward as a linear function of the
context and adds an upper-confidence exploration bonus. It was originally
studied for personalized news recommendation [@li2010linucb], and contextual
bandits more broadly are a standard framework for sequential decision making
under partial feedback [@lattimore2020bandits].

MBA-RAG is the closest bandit-based comparison: it treats retrieval methods as
arms, dynamically selects a strategy according to question complexity, and
penalizes retrieval steps in its reward [@tang2025mbarag]. IntentRoute does not
claim to be the first use of bandits in retrieval-augmented generation. Its
focus is different: it studies fixed cluster-local routes over a domain corpus,
route-level credit assignment, trust-weighted feedback, dense rescue paths, and
the measured size of the final context. The LinUCB controller is not a
replacement retriever. It is an adaptive local-evidence routing policy that can
change route preference as feedback accumulates.

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

IntentRoute therefore treats geometry as one signal in a controller rather
than as a complete retrieval model. Dense retrieval and BM25 remain available as
rescue paths, and the geometry assumption is evaluated diagnostically through
$\mathrm{NearestClusterHit@K}$, $\mathrm{PCAvar@m}$, $\mathrm{PCAdim90}$, and
$\mathrm{ContextRetention@K}$.

## 2.5 Context Compression and Evidence Refinement

Reducing the context passed to a language model is related to, but distinct
from, choosing a retrieval route. Selective Context prunes redundant input
content, LLMLingua uses a coarse-to-fine prompt compression pipeline, and
LLMLingua-2 learns a task-agnostic token classifier for faithful compression
[@li2023selectivecontext; @jiang2023llmlingua; @pan2024llmlingua2]. DSLR
refines retrieved passages through sentence-level reranking and reconstruction
[@hwang2024dslr]. REPLUG shows another complementary direction: a frozen
black-box language model can be paired with a tuneable retrieval model
[@shi2024replug].

IntentRoute operates earlier in the pipeline. It selects evidence routes and
sets final-context budgets before generation rather than compressing tokens
inside already selected passages or tuning a retriever against language-model
likelihood. Its route-control and final-budget policies are therefore compatible with
prompt compression, sentence-level MMR selection, reranking, and black-box
generation methods. The strong-baseline experiments in this paper use this
decomposition explicitly: SentMMR is treated as a shared final-context
compressor, while the cross-encoder is treated as a late reranking layer over a
dense candidate pool. The paper measures final context tokens because
source-candidate counts, reranker scores, or retrieval depth alone do not
establish downstream context savings.

## 2.6 User Feedback, RLHF-Inspired Optimization, and Trust Weighting

User feedback can improve retrieval systems, but real feedback is delayed,
biased, sparse, and user-dependent. Earlier work on clickthrough and implicit
feedback shows that user behavior can train ranking systems, while also
requiring care because clicks and query reformulations are biased signals
[@joachims2002clickthrough; @radlinski2005querychains]. In language-model
systems, human-preference learning and RLHF-style optimization show how feedback
can shape model behavior [@christiano2017preferences; @ouyang2022instructgpt].

IntentRoute is inspired by this feedback-optimization paradigm, but it is not a
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
scales to keep the LinUCB state space comparable, even though larger corpora
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

For each query $q_t$, IntentRoute computes a context feature vector
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
the cluster-local retrieval path and provide confidence signals for route
gating and fallback.

### Feature Groups and Route Confidence

The LinUCB context vector is not intended to introduce a new representation
model. It collects signals that decide whether local routing is reliable for
the current query. The following summary lists the feature groups used by the
controller.

The feature groups are:

- query representation: normalized query embedding and PCA/context projection,
  used to place the query on the same local surface as corpus arms;
- dense confidence: dense score concentration, top-rank margin, and fallback
  availability, used to estimate whether global dense retrieval is already
  reliable;
- lexical confidence: BM25 candidate availability and lexical-match strength,
  used to protect queries that depend on exact terminology;
- route agreement: overlap among dense, BM25, and cluster-local candidates,
  used to detect when independent routes support the same evidence region;
- local geometry: nearest centroid similarity, selected arm identity, and
  semantic drift, used to estimate whether the query lies close to selected
  local arms;
- feedback state: selected-arm value, pull-count maturity, and recent route
  reward, used to estimate whether LinUCB has enough evidence to trust the
  local route;
- budget state: route confidence tier and fallback status, used by the older
  conservative `confidence_topk` diagnostic; the main calibrated budget does
  not map these features to a per-query token ratio.

Route confidence is computed from the selected-arm value estimate, the
top-versus-rest arm margin, and an arm-maturity term based on feedback count.
Semantic drift is defined as one minus the nearest selected-centroid similarity.
Low confidence or high drift keeps the dense fallback active; high confidence
and low drift can enable a lighter route. Only the conservative diagnostic
policy additionally uses this tier to reduce context size.

## 3.6 Trust-Weighted Feedback

IntentRoute models feedback as a noisy signal rather than a perfect oracle. In
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
ranking. IntentRoute therefore uses a stricter `cluster_only` reward
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

## 3.9 Final Context Budgeting and Conservative Confidence Baseline

Preliminary token-cost analysis showed that reducing source candidates does not
automatically reduce final context tokens. IntentRoute therefore combines
confidence-gated routing with an explicit calibrated budget policy, the central
quality-cost control interface.

Let $R_t$ be the ranking produced by the confidence-gated route surface. A
calibration policy $\pi_\phi$ selects a token ratio $r \in (0,1]$ and minimum
prefix $m$. The final context is the longest ranked prefix of at least $m$
chunks satisfying

$$
\mathrm{Tokens}(C_t) \le r\,\mathrm{Tokens}(R_t[:10]).
$$

The policy parameters $\phi$ are selected on calibration queries subject to a
retrieval-quality eligibility gate and then frozen before held-out test
evaluation. Geometry and feedback affect route construction, while the stronger
token saving arises when the separately calibrated length budget acts on the
routed ranking. The implementation does not learn a direct per-query mapping
from confidence to token ratio.

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
100k, 200k, 400k, and 638k while preserving dense-level query hit.

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

1. Embed $q_t$ and compute context features $x_t$.
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
   local region, use the updated arm state to choose a safer context budget or
   fallback path.

Output: final retrieved context $C_t$ and updated policy state.

## 3.12 Reproducibility Parameters

The following summary lists the main implementation parameters used in the
reported cost-aware LinUCB experiments. Scale-specific cache paths and dataset
sizes are reported in the experiment artifacts; these parameters define the
controller behavior.

The main controller parameters are:

- KMeans/MiniBatchKMeans arms: 32 fixed LinUCB arms;
- candidate arms per query: 3 cluster-local routes;
- context projection dimension: 64;
- LinUCB exploration: $\alpha=1.0$, decay 0.01, minimum 0.3;
- prequential epochs: 3 unless otherwise stated;
- feedback trust: default $\tau=0.75$ for noisy feedback updates;
- full-route candidate depths: dense/BM25/cluster = 100/100/100;
- lite-route depths: dense/BM25 = 20/20;
- dense safety floor: 5 full-route chunks and 2 lite-route chunks;
- route fusion: weighted reciprocal-rank fusion with $k=60$;
- full-route weights: dense 2.0, BM25 0.8, cluster 0.8;
- lite-route weights: dense 0.8, BM25 0.5, cluster 2.0;
- confidence thresholds: high 0.65 and mid 0.35;
- drift threshold: 1.0;
- token-budget grid: $r \in \{0.85,0.88,0.90,0.92,0.95,0.98\}$ and
  $m \in \{4,\ldots,8\}$.

The notation `token_budget_r0.85_m4` means that each query keeps a safe prefix
of at least four chunks and then admits additional chunks only while the final
context remains within 85% of the original dense top-10 token budget. The
policy is chosen on calibration queries and then frozen before held-out test
evaluation.

---

# 4. Experimental Setup

## 4.1 Datasets

The experiments use several datasets, but they have different evidentiary
roles. We do not treat all datasets as equal support for the main claim:

- **LoTTE technology/search** is the main large-scale vertical-domain evidence
  benchmark. We evaluate nested corpus scales from 100k to 638k chunks with
  596 test queries.
- **LoTTE science/search** is the cross-domain validation benchmark. It tests
  whether ranking and context-budget behavior transfer beyond technology/search
  at 20k/q200 and 100k scales.
- **PubMedQA and Banking77** are supporting feedback-adaptation checks.
  PubMedQA is an evidence-retrieval proof-of-concept with abstract-level ground
  truth, while Banking77 is an intent-routing proxy rather than a strict
  evidence-retrieval benchmark.
- **eManual and CUAD** are boundary cases. eManual exposes duplicate-text and
  strict chunk-id issues; CUAD is a sparse GT-anchored legal-domain smoke case.

This role separation keeps the main claim tied to LoTTE while preserving the
diagnostic value of the secondary datasets.

## 4.2 Baselines and Variants

The baseline family includes:

- BM25-only lexical retrieval.
- Dense-only retrieval with `sentence-transformers/all-MiniLM-L6-v2`.
- Matched dense and IntentRoute variants with BGE-base and E5-base embeddings.
- BM25 + dense hybrid retrieval using reciprocal-rank fusion.
- Full multi-route IntentRoute.
- Gated cost-aware IntentRoute.
- Conservative confidence-conditioned final-context baseline.
- Dense+Sentence-MMR final-context compression.
- Dense and IntentRoute plus SelectiveContext-lite prompt pruning.
- Cross-encoder reranking over dense top-50 candidates.
- Static geometry controls such as nearest-cluster routing.
- Naive controls such as random or epsilon-greedy arm selection.
- No-feedback and uniform-random route controls.
- Arm-count sensitivity over $K \in \{8,16,32,64,128\}$.

Dense-only retrieval is the primary quality baseline. The paper should avoid
weak baseline framing: dense is strong and remains a required recall floor in
the proposed method. Sentence-MMR, SelectiveContext-lite, and cross-encoder
reranking are reported as strong post-retrieval baselines. Sentence-MMR and
SelectiveContext-lite test whether downstream compression can explain the token
saving, while the cross-encoder tests whether a heavier late-ranking layer can
select a smaller context more simply. These are not mutually exclusive
alternatives to IntentRoute; they occupy different stages in the
retrieval-to-context pipeline.

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

The downstream evaluation additionally reports LLM-judge correctness and
faithfulness, strict chunk-id citation support, insufficient-context rate, and
context tokens per judged-correct answer. These metrics are secondary
answer-level validation of the route-and-budget claim, not evidence of
generator superiority.

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
\begin{aligned}
\mathrm{NearestClusterHit@K} &=
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}} \\
&\quad
\mathbb{1}
\left[
\mathcal{N}_K(q_t) \cap \mathcal{C}_t \neq \varnothing
\right].
\end{aligned}
$$

where $\mathcal{Q}_{GT}$ is the set of queries with at least one ground-truth
chunk in the evaluated corpus.

Finally, let $R_{t,\mathrm{ctx}}^K$ be the top-$K$ chunks retrieved by inner
product in the PCA/context space, and let $R_{t,\mathrm{dense}}^K$ be the
top-$K$ chunks retrieved by dense embedding similarity. We define:

$$
\begin{aligned}
\mathrm{ContextHit@K} &=
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}} \\
&\quad
\mathbb{1}
\left[
R_{t,\mathrm{ctx}}^K \cap G_t \neq \varnothing
\right],
\end{aligned}
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
cosine search. Matched-backbone checks use BGE-base and `intfloat/e5-base-v2`;
E5 applies the recommended `query:` and `passage:` prefixes. Embeddings and
retrieval artifacts are cached to avoid repeating deterministic computation.
Metrics are recomputed from saved rankings, not copied from prior summaries.
Historical experiment directories and machine-readable method labels retain the
legacy `IntentWeight` identifier so that existing hashes, selectors, and result
provenance remain reproducible; paper-facing terminology uses `IntentRoute`.

KMeans/MiniBatchKMeans uses 32 arms in the main scale experiments. A dedicated
100k sensitivity check evaluates 8, 16, 32, 64, and 128 arms. This supports
LinUCB comparability and tests engineering sensitivity, but it is not claimed
to identify a theoretically optimal clustering design.

The Sentence-MMR baseline starts from dense or IntentRoute evidence pools,
splits selected chunks into sentence-like units, and greedily selects
query-relevant but diverse sentences under a target token ratio or per-query
budget. SelectiveContext-lite is a deterministic Selective Context-style proxy
that scores sentence-like units with query overlap, IDF salience, bigram
overlap, source rank, and compactness; it is not presented as LLMLingua. The
cross-encoder baseline reranks dense top-50 candidates with
`cross-encoder/ms-marco-MiniLM-L-6-v2`; it is evaluated both as a full reranked
top-10 and as a same-budget variant constrained by the calibrated IntentRoute
per-query token budgets. Reranker compute cost is not charged in final context
tokens, so reranker results should be interpreted as retrieval-quality
baselines rather than end-to-end latency measurements.

## 4.7 Calibration and Paired Testing Protocol

The final-context budget experiments use a calibration/test split over queries.
For each scale, 30% of queries are used only to select a budget policy. The
selected policy is then frozen and evaluated on the remaining held-out test
queries. This avoids choosing a context budget after seeing test labels.

A budget policy name has the form `token_budget_rX_mY`. Here, `rX` is the
maximum final-context token ratio relative to the original top-10 context, and
`mY` is the minimum safe prefix kept before token-budget filtering. For example,
`token_budget_r0.85_m4` keeps at least four top-ranked chunks and then admits
additional chunks only while the final context remains within 85% of the
original top-10 token budget.

Calibration eligibility is defined using the mean calibration
$\mathrm{Hit@10}$ delta against dense top-10. The main calibration selection
uses a zero observed-hit-drop margin: a policy is eligible only when its mean
calibration hit delta is non-negative. Among eligible policies, the selected
policy is the one with the largest final-context token saving. If no policy is
eligible, the best diagnostic policy is still reported, but it is not treated
as a strict calibration-eligible main operating point.

Frozen test results are paired by query against dense top-10. We report
bootstrap confidence intervals for $\mathrm{Hit@10}$ deltas and final-context
token savings where available, and use a 1 percentage-point non-inferiority
margin for strict seed-level checks. This separates two claims: whether the
method preserves retrieval quality under a conservative paired criterion, and
whether it reduces the final evidence-context tokens sent to the generator.

Two additional audits test selection robustness. First, Dense and IntentRoute
independently select actions on the same 100k calibration split over a fine
ratio grid from 1.00 to 0.80 in 0.01 increments, so the comparison does not
force Dense to inherit the routed policy's nominal action. Second, the original
calibration grid is repeated over 20 deterministic 30/70 query partitions at each
scale. These overlapping partitions diagnose split sensitivity; they are not
treated as additional training seeds or independent inferential samples.

## 4.8 Downstream Answer-Level Protocol

The answer-level evaluation draws 300 deterministic queries from the 417-query
frozen test split. Seven methods cover MiniLM dense, BGE dense and IntentRoute,
E5 dense and IntentRoute, and matched Dense+SentMMR versus
IntentRoute+SentMMR. The `deepseek-v4-flash` configuration generates one answer
from each retrieved context. The fixed answers are independently judged by
`deepseek-v4-flash`, `glm-5.2`, and `minimax-m3` for correctness,
faithfulness, relevance, and citation support against reference evidence.

The run contains 2,100 generated answers and 6,265 schema-valid judgments:
2,100 each from DeepSeek and GLM-5.2 and 2,065 from MiniMax-M3. Thirty-five
MiniMax-M3 inputs are rejected by provider-side content filtering and are not
imputed. Cross-judge agreement uses the 2,065 query-method keys valid for all
three judges. Correctness and faithfulness differences use paired query-level
bootstrap intervals and exact McNemar tests within each judge and for the
three-judge majority. Raw ordinal scores are not pooled across judges. The
under-specified `insufficient_context_appropriate` field is retained in raw
artifacts but excluded from headline and agreement analyses. This protocol
supports multi-judge answer-level robustness, not human-rated superiority.

---

# 5. Results

## 5.1 Calibrated Token-Quality Frontier

The main cost result uses a calibrated token-budget policy. For each corpus
scale, the budget is selected on calibration queries and then frozen before
test evaluation. Cost is measured as final LLM evidence-context input tokens
relative to dense top-10, not retrieval-side candidate count.
Table~\ref{tab:1} reports the resulting scale-wise operating points.

**Table 1. Calibrated token-quality frontier on LoTTE technology/search.**

| Scale | Frozen policy | Calib. eligible | IntentRoute hit delta | NI seeds | IntentRoute token saving | Dense-trunc hit delta | Dense-trunc token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 0/3 | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 1/3 | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / diagnostic | +2.32 pp | 3/3 | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 0/3 | 17.53% | -3.84 pp | 21.90% |

The calibration-eligible 100k, 200k, and 638k operating points save 6-18%
final context tokens. The 400k row is retained as a diagnostic point because
no candidate met the zero-observed-hit-drop calibration gate, even though its
frozen-test result is positive. Dense-only adaptive truncation saves more
tokens but loses $\mathrm{Hit@10}$ at every scale. IntentRoute therefore
targets a more quality-preserving bounded frontier rather than maximum
compression.

An independently calibrated 100k audit gives Dense and IntentRoute the same
fine budget grid but lets each select its own action. Under the zero observed
calibration-drop rule, IntentRoute selects `r0.95/m4` and retains the
Table~\ref{tab:1}
result of `6.18%` test saving with `0.00pp` mean Hit delta; Dense selects
`r1.00/m4`, or no compression. Their mean test Hit is equal, although strict
IntentRoute non-inferiority is not established in any seed. A descriptive
same-saving interpolation over the held-out Pareto curves shows only small Hit
differences: `+0.47pp`, `+0.04pp`, `+0.22pp`, and `-0.01pp` at 5%, 10%, 15%,
and 20% saving, respectively. This supports a bounded conservative operating
point, not universal frontier dominance.

A 20-partition sensitivity audit further separates stable scales from split
sensitivity. Frozen selected policies retain mean Hit within `1pp` of dense on
all 20 test partitions at 200k and 638k, versus 14/20 at 100k and 17/20 at 400k.
The 100k mean range is `-2.00pp` to `+0.72pp`; 400k varies from `-2.08pp` to
`+2.80pp`. The original pre-specified split remains the primary result, while
the repeated partitions strengthen 200k/638k and keep 100k/400k interpretation
more cautious.

A normalized five-fold follow-up uses the same canonical query folds,
predefined budget grid, zero-drop gate, three route seeds, Dense fallback, and paired
statistics at every scale. Its out-of-fold IntentRoute Hit deltas and token
savings are respectively `-1.06pp/4.16%`, `+1.40pp/16.07%`,
`+0.00pp/14.50%`, and `+0.28pp/15.23%` from 100k through 638k. Independently
calibrated Dense finds no eligible compressed action in any fold and therefore
uses top-10 fallback. At 400k, all five IntentRoute folds are eligible, closing
the missing normalized follow-up, but they select five different policies and
strict non-inferiority remains `0/3` seeds. Appendix G4 reports the fold-level
results. This supports the average 400k trade-off without erasing the original
split failure or claiming stable policy selection.

Query-level paired bootstrap intervals and McNemar-style win/loss counts show
that token savings are more consistent than strict quality non-inferiority.
The conservative confidence-only policy remains a stable 4.7-5.3% saving
baseline; complete seed and policy details are reported in Appendix A and G.
Figure 2 visualizes the quality-cost frontier.

## 5.2 Matched-Backbone Robustness

Matched-backbone evaluation tests whether the controller pattern is specific
to MiniLM. Each IntentRoute row is compared with dense retrieval using the same
encoder and frozen test split.
Table~\ref{tab:2} summarizes the matched-backbone comparison.

**Table 2. Matched-backbone operating points on LoTTE technology/search 100k.**

| Backbone and policy | Dense $\mathrm{Hit@10}$ | IntentRoute $\mathrm{Hit@10}$ | Hit delta | Token saving |
|---|---:|---:|---:|---:|
| MiniLM calibrated | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE full multi-route | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| E5 full multi-route | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| BGE quality-first | 0.8993 | 0.9081 | +0.88 pp | 7.23% |

BGE and E5 full multi-route policies remain near their respective dense
baselines while saving about 12% context tokens. The BGE quality-first point
moves the same frontier toward higher retrieval hit at lower saving. The E5
scan did not produce an above-dense token-saving point, so positive-hit
tunability is BGE-specific rather than a universal claim. Appendix E reports
the supporting encoder details.

## 5.3 Route-Control Attribution

The route controls isolate geometry, feedback, and dense rescue. The
geometry-versus-random rows change arm selection under an otherwise matched
full rescue surface. The learned, static, and no-feedback rows test whether
LinUCB updates and gating explain route quality and final cost.
Table~\ref{tab:3} separates route-level effects from rescued final quality.

**Table 3. Geometry, feedback, and rescue-route controls on LoTTE 100k. Each row uses its paired frozen-protocol dense baseline.**

| Control | Route reward | Cluster hit | Dense rate | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Static nearest geometry | 0.8563 | 0.8870 | 1.0000 | +1.44 pp | 5.03% |
| Uniform random arms | 0.1499 | 0.1577 | 1.0000 | +1.04 pp | 11.92% |
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | -1.68 pp | 17.86% |
| Learned gated | 0.6790 | 0.5766 | 0.7377 | -5.20 pp | 11.83% |
| Static-nearest gated | 0.8563 | 0.8870 | 0.9586 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | -1.60 pp | 16.56% |

Static nearest geometry sharply exceeds random routing on route reward and
selected-cluster hit, but dense and BM25 rescue keep final fused hit high for
both. Feedback-updated LinUCB likewise improves route quality over the
no-feedback control, but the tested learned-gated threshold loses 5.20
percentage points of frozen-test hit. These results support geometry and
feedback as route-confidence signals; neither alone explains final fused
quality or justifies unconditional dense removal.

Feedback remains useful as a recovery trigger. Conservative same-query retry
recovers 23 of 76 budget-induced misses across the two LoTTE 100k domains, but
the stricter calibration-to-test effect is small and domain-dependent.
Appendix I and K contain the full recovery and control tables.

A frozen-trajectory route replay further isolates the confidence gate. Keeping
the selected arms and feedback state fixed, the original query-to-tier
assignment exceeds a shuffled-tier control with identical tier frequencies by
4.80 percentage points of Hit@10, both before and after the common
`r0.95/m4` budget; all three seed-level paired intervals exclude zero. It also
exceeds an always-cluster-primary route by 10.79 percentage points after
budgeting. Fixed full fusion remains 0.40 percentage points above dynamic
gating while saving 0.91 percentage points fewer tokens, and that hit
difference is not statistically detected. The result supports confidence as a
route/fallback assignment signal, not as a direct compression-safety score.

## 5.4 Arm Granularity And Geometry-To-Control Analysis

Arm-count sensitivity tests whether the fixed $K=32$ clustering choice is a
hidden optimum. Full multi-route quality remains stable over a 16-fold range,
whereas aggressive gated behavior changes substantially with arm granularity.
Table~\ref{tab:4} reports the tested arm-count grid.

**Table 4. Arm-count sensitivity on LoTTE technology/search 100k.**

| $K$ | Static route reward | Full hit delta | Full token saving | Gated dense rate | Gated hit delta |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.9128 | +1.44 pp | 6.23% | 0.4083 | -1.84 pp |
| 16 | 0.8826 | +0.80 pp | 10.49% | 0.6089 | -1.68 pp |
| 32 | 0.8563 | +0.56 pp | 4.68% | 0.7377 | -4.48 pp |
| 64 | 0.8272 | +0.40 pp | 11.19% | 0.8986 | -3.76 pp |
| 128 | 0.8479 | +1.20 pp | 10.23% | 0.9502 | -3.12 pp |

The full route surface stays above its paired dense baseline throughout the
grid, while gated dense use rises from 0.4083 to 0.9502 as $K$ grows. This
supports $K$ as an engineering parameter governing feedback sparsity and
fallback behavior, not a geometrically privileged constant.

Across LoTTE scales, nearest-cluster hit remains high while context retention
and PCA concentration vary. Figure 3 relates context retention to observed hit
delta and token saving. The small cross-scale sample does not show a
deterministic geometry-to-gain law: geometry identifies plausible local route
structure, while calibration, fusion, and dense rescue determine the final
operating point. Full diagnostics are retained in Appendix K.

## 5.5 Cross-Domain And Boundary Evidence

On LoTTE science/search, fixed top-10 IntentRoute reaches
$\mathrm{Hit@10}=0.9267$ versus 0.8950 for dense at 20k/q200 and 0.9077 versus
0.8926 at 100k. Frozen budget policies save 13-14% tokens at 20k/q200 while
remaining above dense. At 100k, the more aggressive policy saves 17-21% but
can introduce small hit losses. The ranking signal transfers, but compression
strength requires domain- and scale-specific calibration. Appendix H reports
the complete seed-level table.

PubMedQA and Banking77 provide supporting feedback-adaptation checks near
quality ceilings. eManual and CUAD remain boundary cases because duplicated
evidence text and sparse ground-truth anchors complicate strict chunk-level
evaluation. These datasets bound the claim rather than establish universal
dense-retrieval dominance.

## 5.6 Strong Post-Retrieval Baselines

Dense+Sentence-MMR preserves dense chunk-support
$\mathrm{Hit@10}=0.8705$ while saving 11.4-13.1% selected-sentence tokens.
When the same compressor is applied to both source pools,
IntentRoute+Sentence-MMR reaches 10.1-21.2% total saving because it starts from
a smaller evidence pool. SelectiveContext-lite similarly adds prompt pruning
after either source pool and reaches up to 30.57% total saving over dense for
the tested IntentRoute variants. These controls show that downstream
compression is complementary, not unique to IntentRoute.

A cross-encoder reranker improves dense full-top-10 support from
$\mathrm{Hit@10}=0.8705$ to 0.8777 and evidence recall from 0.7081 to 0.7332,
but increases context tokens by 21.9%. Under matched context budgets, its
$\mathrm{Hit@10}$ range of 0.8633-0.8729 does not uniformly dominate the
IntentRoute range of 0.8657-0.8777. Appendix J contains all compressor and
reranker tables.

## 5.7 Downstream Answer-Level Evaluation

The frozen downstream evaluation contains 300 queries, seven methods, 2,100
generated answers, and 6,265 valid judgments from DeepSeek, GLM-5.2, and
MiniMax-M3. Cross-judge results use the 2,065 query-method keys valid for all
three judges; 35 MiniMax-M3 judgments rejected by provider-side filtering are
not imputed.
Table~\ref{tab:5} reports the matched correctness and context-token results.

**Table 5. Matched downstream answer-quality and context-token comparisons.**

| Comparison | DeepSeek $\Delta$ | GLM $\Delta$ | MiniMax $\Delta$ | Majority $\Delta$ (95% CI) | Context saving (95% CI) |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs BGE dense | +0.00 pp | -3.00 pp | -2.42 pp | -3.46 pp [-6.92, 0.00] | 6.27% [4.22%, 8.26%] |
| E5 IntentRoute vs E5 dense | +0.33 pp | -1.33 pp | -2.77 pp | -2.08 pp [-5.88, +1.73] | 11.97% [9.78%, 14.17%] |
| IntentRoute+MMR vs Dense+MMR | +2.33 pp | +0.33 pp | +1.36 pp | +0.34 pp [-3.39, +4.07] | 6.75% [4.40%, 9.11%] |

All context-saving intervals are positive. Every individual-judge and
majority-vote correctness interval includes zero, and all correctness McNemar
tests are non-significant. Absolute judge calibration differs: pairwise raw
agreement is 89.88-92.15% for correctness, with Cohen's $\kappa$ of
0.503-0.653. This supports lower context without a statistically detectable
correctness difference, but not strict non-inferiority or significant
answer-quality improvement.

Faithfulness is not uniformly preserved. The three-judge majority estimates a
-4.15 pp BGE faithfulness change (95% CI [-6.92, -1.73], $p=0.0018$) and a
+4.07 pp change for the SentMMR composition (95% CI [+0.68, +7.46],
$p=0.0290$); E5 remains non-significant. Appendix F reports judge coverage,
agreement, full method-level results, and the mixed faithfulness boundary.

---

# 6. Discussion

## 6.1 Supported Claim

IntentRoute supports a bounded confidence-gated-route plus calibrated-budget claim. It estimates
confidence over dense, lexical, and geometry-defined local routes, adapts that
confidence through trust-weighted feedback, uses it to gate route usage, and
applies a separately frozen final-context policy. On LoTTE technology/search,
calibration/test validation shows that calibration-eligible operating points at
100k, 200k, and 638k save 6-18% final evidence-context tokens while avoiding
the larger $\mathrm{Hit@10}$ losses of dense-only adaptive truncation. The 400k
result is positive on frozen test but does not pass the original calibration
eligibility gate. A subsequent normalized five-fold audit selects compressed
IntentRoute policies in all 400k folds and yields 14.50% mean saving with no
mean Hit change, but fold-specific policies vary and strict seed-level
non-inferiority remains unestablished. A conservative
confidence-only policy provides a stable baseline, reducing final retrieved
context tokens by about 4.7-5.3% from 100k to 638k corpus chunks while
preserving dense-level query hit. Matched BGE/E5 experiments extend the
quality-cost pattern beyond MiniLM, and the 300-query, three-judge downstream
evaluation finds positive context savings without a statistically detectable
correctness change. The stricter judges produce negative BGE/E5 correctness
point estimates, and the three-judge majority detects a BGE faithfulness
decrease, so the result does not establish uniform answer-quality
non-inferiority. LoTTE science/search further supports ranking-side generalization, but
also shows that compression strength must be calibrated per domain and scale.

This result is not a claim that dense retrieval is weak. Dense retrieval remains
the primary quality baseline and an important recall floor. IntentRoute's value
is the explicit separation of adaptive route control, dense rescue, and
calibrated final-context compaction.

## 6.2 Role of Calibrated Context Budgeting

A static combination of dense, BM25, and cluster-local retrieval can improve
coverage, but it does not automatically reduce final context tokens. In fact,
static dense+BM25 hybrid retrieval can use more context tokens than dense-only
retrieval because it surfaces longer or noisier chunks. The token-saving
mechanism is therefore not "more routes." It is the calibrated budget applied
after confidence-gated route construction.

The confidence-only policy is intentionally conservative. It compresses only
high-confidence cases to $k=8$ and keeps mid-confidence cases at $k=10$. This is
why the saving is modest but stable. The calibrated token-budget policies use a
frozen calibration/test protocol to expose a stronger operating frontier, while
dense-only adaptive truncation shows that saving more tokens by simply reducing
dense top-$k$ can cause visible $\mathrm{Hit@10}$ loss. The conservative policy
should therefore be interpreted as a stable empirical baseline, not the
highest-compression configuration or a per-query safety guarantee.

The cross-fitted comparison also clarifies why route quality matters to budget
control. Under the same zero-drop gate, prefix-only Dense truncation cannot
select a compressed action in any fold at any tested scale, whereas
IntentRoute selects one in every 200k, 400k, and 638k fold. This is evidence of
calibration headroom created by the routed evidence ranking, not evidence that
all route policies or partitions are safe.

## 6.3 Reranking and Final-Context Control

A cross-encoder reranker is a natural stronger ranking baseline, but it solves
a different subproblem from final-context budgeting. A reranker applied after
dense or multi-route retrieval can reorder a candidate pool and improve the
quality of the top-ranked evidence, but it does not expand recall beyond the
candidate pool and it does not by itself control LLM input length. In the LoTTE
technology/search 100k check, reranking dense top-50 candidates with a
cross-encoder improves the full top-10 support metrics
($\mathrm{Hit@10}=0.8777$ and $\mathrm{EvidenceRecall@10}=0.7332$, versus
dense top-10 at $0.8705$ and $0.7081$). However, the reranked top-10 contains
longer chunks on average, increasing selected evidence-context tokens by about
21.9% relative to dense top-10.

This clarifies the intended system decomposition. Reranking is useful as a late
ranking layer, SentMMR and SelectiveContext-lite are downstream prompt-context
compression layers, and IntentRoute controls the upstream evidence pool and
budget passed to them. When the cross-encoder output is
forced under the same per-query token budgets used by IntentRoute, its
$\mathrm{Hit@10}$ range does not uniformly dominate the calibrated
IntentRoute policies. The appropriate comparison is therefore not
"IntentRoute versus reranking" as mutually exclusive choices, but whether a
pipeline can combine candidate generation, reranking, and budgeted context
selection while keeping the quality-cost frontier explicit.

## 6.4 Feedback Improves the Policy Field

Dense and BM25 fallback can saturate final $\mathrm{Hit@10}$. This can hide the
effect of feedback in final fused retrieval metrics. The clearer feedback
signal appears in route-policy metrics such as selected-cluster hit and last
true reward.

Trust weighting improves these policy metrics under controlled simulated
feedback. Dedicated controls place the learned route reward at $0.6790$, above
the no-feedback/random level of about $0.15$ but below the $0.8563$ static
nearest-geometry prior. This supports feedback as adaptive route-confidence
estimation, not as the sole source of final fused quality. However, the current
feedback is simulated and
ground-truth-derived. Production systems still need real feedback collection,
trust scoring, delayed-feedback handling, and safeguards against unreliable or
adversarial signals.

The hard-case recovery experiment adds a more operational interpretation of
feedback. When aggressive compression loses evidence, arm-level feedback can
repair a meaningful fraction of affected queries through a safer retry or
fallback policy. This should be treated as a controlled recovery mechanism. It
does not mean that feedback should blindly boost the same arm for all future
queries.

A frozen-trajectory counterfactual clarifies where route confidence acts.
Shuffling confidence tiers while preserving their frequency lowers Hit@10 by
4.80 percentage points, whereas the original assignment sends high-confidence
queries to a cluster-primary route with mean source Hit@10 of 0.924 and retains
full fallback for the low-confidence group, where forced cluster-primary Hit@10
falls to 0.240. Confidence therefore has a supported controlled role in
route-shape assignment. This role precedes and is distinct from final-context
budgeting.

## 6.5 Geometry Is Useful but Not Sufficient

The geometry diagnostics support a piecewise relevance-manifold framing.
$\mathrm{NearestClusterHit@3}$ remains high across LoTTE scales, and local
geometry provides useful routing information. However, context retention
declines with scale, and geometry alone is not a complete retrieval model. If a
cluster route prunes too early, correct evidence can be lost.

IntentRoute therefore uses geometry as one signal in a controller. Dense
retrieval remains a fallback, BM25 provides lexical anchors, and LinUCB learns
route confidence over repeated interactions.

The random-route control is important to this interpretation. Static geometry
strongly improves route reward and selected-cluster hit over random routing,
but final fused hit remains protected in both cases by dense/BM25 rescue. Mixed
small-sample correlations between geometry diagnostics and final token-quality
gain further show that geometry guides route construction without fully
determining the end result. The gain belongs to the complete calibrated
controller, not geometry in isolation.

A factorial safe-compression audit holds the dense top-10 ranking, split,
budget grid, and seeds fixed while crossing geometry versus a randomized
partition with feedback versus no feedback. Geometry with feedback does not
outperform random-partition feedback in held-out failure discrimination (mean
AUROC $0.434$ versus $0.573$); at an approximately 10% saving target their
Hit@10 difference is only $+0.08$ percentage points and every seed-level paired
bootstrap interval includes zero. Safe-action labels are highly imbalanced
($97.8\%$ safe), so this is boundary evidence rather than proof of inverse
prediction. It prevents attributing the stronger 6--18% token frontier directly
to per-query confidence precision.

The same frozen replay finds mean Spearman correlation $-0.056$ between route
confidence and oracle safe-token headroom, with every seed-level interval
including zero. Dynamic routing also contains fewer relevant top-10 chunks than
fixed full fusion (2.121 versus 2.315). These results rule out a simple account
in which confidence gating improves compression by creating greater evidence
redundancy. Its measured benefit is assigning route shapes without the severe
quality loss of shuffled or unconditional cluster-primary routing.

## 6.6 Evidence Completeness Versus Usable Evidence

The main retrieval headline is query-level $\mathrm{Hit@10}$. This metric asks
whether at least one relevant chunk appears in the final context. It is
appropriate for many RAG settings where one good supporting chunk is enough to
ground an answer. However, context compaction can reduce
$\mathrm{EvidenceRecall@10}$, the fraction of all GT chunks retrieved.

This is an expected trade-off. IntentRoute optimizes usable evidence under a
smaller context budget, not exhaustive evidence collection. For legal review,
medical synthesis, or compliance workflows where complete evidence coverage is
required, the system should use a more conservative context policy or disable
compaction.

## 6.7 Production Interpretation

The measured 6-18% calibrated evidence-context token reduction applies to the
most expensive recurring component of a retrieval-augmented answer: LLM input
tokens. At enterprise query volumes, even the conservative end of this range can
compound into meaningful cumulative inference-cost reduction. The older
4.7-5.3% confidence-only policy is best interpreted as a stable conservative
baseline, while calibrated budgets show the stronger operating frontier. In
production, repeated query patterns and richer post-fusion features may support
a dedicated compression-safety estimator. Route confidence alone is not
established as such an estimator by the current experiments. This remains a
hypothesis for production evaluation rather than a current claim.

The correct deployment interpretation is therefore:

- keep dense retrieval as a recall floor;
- optionally add reranking as a late ranking layer before final context
  selection;
- use feedback and confidence for route control, and calibrate the final
  context budget separately;
- use negative feedback to trigger safer local fallback for risky regions;
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

The hard-case recovery experiment also uses GT-derived simulated feedback.
Same-query retry should be interpreted as an engineering recovery test after a
failed compressed answer, not as first-pass IID held-out improvement. The result
shows that feedback can repair a meaningful fraction of affected queries when
the evidence remains reachable through the candidate pool and arm structure; it
does not imply universal recovery.

## 7.2 Limited Generation Evaluation

The downstream evaluation expands to 300 frozen-test queries, seven methods,
2,100 generated answers, and 6,265 valid judgments from three LLM judges. It
finds positive context-token savings for matched BGE, E5, and SentMMR
comparisons without a statistically detectable correctness change. However,
all answers are generated by one model, DeepSeek also serves as one of the
judges, no human ratings are collected, and the benchmark covers one LoTTE
domain. MiniMax-M3 rejects 35 judgments through provider-side content
filtering; cross-judge analyses exclude rather than impute them. Judge
calibration differs, and majority-vote faithfulness decreases for BGE while
increasing for the SentMMR composition. The result therefore supports bounded
answer-level correctness robustness, not strict non-inferiority, uniform
faithfulness preservation, generated-answer superiority, or user satisfaction.

## 7.3 Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentRoute should not be
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

## 7.5 Context Budget Requires Domain Calibration

The LoTTE science/search replication shows that fixed top-10 ranking gains can
transfer to a second domain, but context-budget strength does not transfer
automatically. At science/search 100k, an aggressive budget still saves
17-21% final context tokens but can introduce small $\mathrm{Hit@10}$ drops on
the frozen test split. Compression should therefore be calibrated per domain
and scale, with dense fallback retained for low-confidence or high-risk local
regions.

Calibration is also sensitive to the query partition. Across 20 deterministic
partitions, selected-policy mean Hit remains within `1pp` of dense on every 200k and
638k test partition, but only 70% of 100k and 85% of 400k partitions. These
partitions overlap and therefore measure sensitivity rather than independent
replication. The pre-specified frozen split remains valid, but production use
should prefer repeated or nested calibration and should not infer a universal
no-loss policy from one partition.

The five-fold cross-fitted follow-up uses disjoint test folds and identical
canonical query assignments across scales. It improves the 400k average result
to 14.50% saving at effectively zero mean Hit delta, but fold-level deltas
remain heterogeneous and the selected policy changes in every 400k fold. It
therefore reduces the missing-calibration concern without establishing
split-invariant deployment behavior.

## 7.6 Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
$\mathrm{NearestClusterHit@3}$, PCA spectrum, and context retention. These
diagnostics do not prove a mathematical manifold theorem. They show that local
geometry is informative for routing on LoTTE, while dense retrieval remains
necessary.

## 7.7 Fixed Routing Arms Are an Experimental Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and
the experiments need reproducible, scalable arms. This is not a claim that
KMeans is the best clustering method for all RAG systems. HDBSCAN or
graph-based clusters may perform better in some deployments, but dynamic arm
counts complicate the current LinUCB setup. The tested $K=8$-$128$ grid shows
stable full multi-route quality but sensitive gated routing, so $K=32$ remains
an engineering operating point rather than an optimum.

## 7.8 Limited Encoder and Domain Coverage

The paper evaluates matched MiniLM, BGE-base, and E5-base dense/IntentRoute
backbones, plus a QA-tuned MiniLM-family check and a cross-encoder reranker.
This establishes backbone-level robustness within the tested LoTTE setting,
but it does not cover domain-specific encoders, late-interaction models, or
proprietary embedding systems. The above-dense quality-first point is currently
demonstrated for BGE only; E5 supports a near-dense token-saving point instead.

LoTTE technology/search is the main positive large-scale domain. LoTTE
science/search strengthens external validity but does not replace evaluation on
additional vertical corpora.

## 7.9 Seed Count and 400k Variance

The stability analysis uses the fixed seeds 13, 17, and 19 across the main
LoTTE route experiments. These are engineering stability diagnostics, not a
claim that a large seed population has been sampled. Query-level paired tests
provide the main inferential evidence. The LoTTE 400k
token-saving interval is notably wider than the other scales and should be
interpreted as seed-level operating-point variance across routed rankings and
context-budget control. In the original calibrated-budget experiment, the 400k
frozen-test result is positive but the selected policy is not
calibration-eligible under the zero-observed-hit-drop gate. The completed
cross-fitted follow-up is positive on average, but uses five distinct fold
policies and establishes strict non-inferiority in 0/3 seeds. The original
failure and the follow-up instability both remain part of the reported
boundary.

## 7.10 Future Work

The factorial safe-compression attribution audit finds no held-out
discrimination advantage for geometry-feedback confidence over a matched
random-partition feedback control under a fixed dense candidate pool and
compression action. Only about $2.2\%$ of dense-hit test queries are unsafe for
the diagnostic action, so AUROC intervals are wide and AUPRC, Brier, and ECE are
strongly affected by class imbalance. The current evidence supports
confidence-gated routing and a separately calibrated budget, not a learned
per-query confidence-to-token-ratio mapping.

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- multi-model and human-rated answer-quality and citation-faithfulness studies;
- stronger dense encoders, rerankers, and late-interaction retrieval models;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- repeated evaluations on additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.
- recovery policies evaluated with real delayed feedback rather than
  GT-derived same-query retry.

---

# 8. Conclusion

This paper presents IntentRoute, a feedback-adaptive
confidence-gated route and calibrated-budget controller motivated by local relevance structure
in vertical-domain data. In the evaluated retrieval-backed QA implementation,
geometry defines reproducible cluster-local routes, trust-weighted LinUCB
updates route confidence, dense and BM25 provide rescue paths, and a calibrated
policy separately controls the final evidence-context budget.

The main evidence comes from LoTTE technology/search at 100k to 638k corpus
chunks. Under calibration/test budget selection, calibration-eligible operating
points at 100k, 200k, and 638k reduce final LLM evidence-context input tokens
by 6-18%; the original 400k point remains calibration-ineligible. A normalized
five-fold follow-up at 400k yields 14.50% mean saving with no mean Hit change,
while retaining policy instability and no strict seed-level non-inferiority.
Across these scales, IntentRoute avoids the larger
$\mathrm{Hit@10}$ losses of dense-only adaptive truncation, while strict
seed-level non-inferiority remains scale-dependent. A conservative
confidence-only policy remains a stable 4.7-5.3% saving baseline. Split
sensitivity checks strengthen the 200k and 638k operating points while showing
that 100k and especially 400k policy selection is more partition-dependent.
Additional diagnostics and controls show that local geometry provides useful route signal
over random routing and trust-weighted feedback improves route confidence over
no-feedback controls, without implying that either alone explains fused
quality. Matched BGE/E5 comparisons retain near-dense retrieval quality with
about 12% context saving, while a BGE quality-first point demonstrates frontier
tunability. A 300-query evaluation with three LLM judges finds approximately
6-12% matched context savings without a statistically detectable correctness
change, while exposing method-dependent faithfulness effects and retaining the
lack of strict answer-level non-inferiority.
LoTTE science/search provides cross-domain ranking support with a clear
compression-calibration boundary. Hard-case recovery experiments further show
that simulated feedback can repair part of the tail failures caused by
aggressive context compression.

Strong post-retrieval baselines refine rather than weaken the conclusion.
Sentence-level MMR and SelectiveContext-lite are effective shared downstream
compressors, and cross-encoder reranking can improve top-ranked evidence
support. However,
reranking alone can increase final context tokens, and same-budget reranking
does not uniformly dominate the calibrated IntentRoute policies. These results
support a layered interpretation: candidate generation, reranking, compression,
route control, and budget calibration are separate system functions that can be
composed.

The result is intentionally bounded. IntentRoute is not a universal dense
replacement, a universal compressor replacement, or a universal reranker
replacement, and it does not prove that geometry alone solves retrieval. Dense
retrieval remains an important recall floor. The contribution is a calibrated
controller that combines geometry- and feedback-informed route control with a
separately calibrated final context budget, trading compact context against retrieval risk while
remaining compatible with late reranking and prompt compression. The manifold
hypothesis remains the motivation for local route structure, not a
theorem-level claim.

---

# Appendix

## A. Conservative Baseline and Seed Stability Diagnostics

The conservative confidence-only context policy is the stable baseline for
context compaction. The main text reports calibrated token-budget policies as
the primary cost result; this appendix keeps the earlier confidence-only scale
table and seed diagnostics. These intervals are engineering stability
diagnostics, not strong inferential proof: each scale has only three
observations.
Tables~\ref{tab:a1} and~\ref{tab:a2} report quality and token stability.

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
interval should be interpreted as operating-point variance across the routed
ranking and context policy, not hidden as a uniform result.

## B. Static Retrieval Baselines

Dense retrieval is the primary quality baseline. BM25 supplies lexical
coverage, but it is weaker as a standalone retriever on LoTTE. Static
dense-plus-BM25 reciprocal-rank fusion is competitive at some scales but does
not consistently dominate dense.
Table~\ref{tab:b1} reports these static baselines.

**Appendix Table B1. Static LoTTE retrieval baselines across corpus scale.**

| Scale | Corpus chunks | BM25 $\mathrm{Hit@10}$ | Dense $\mathrm{Hit@10}$ | Static hybrid $\mathrm{Hit@10}$ |
|---|---:|---:|---:|---:|
| 100k | 101311 | 0.7232 | 0.8674 | 0.8624 |
| 200k | 201010 | 0.6292 | 0.7970 | 0.8003 |
| 400k | 400674 | 0.5721 | 0.7718 | 0.7617 |
| 638k | 638509 | 0.5084 | 0.7282 | 0.7181 |

The declining dense score as corpus scale grows motivates adaptive context
control, but it does not make dense retrieval obsolete. Dense remains an
important recall floor and fallback route in IntentRoute.

## C. Cost Metric Separation

The experiments separate three efficiency layers:

1. source candidate cost: candidates considered before final fusion;
2. dense invocation rate: fraction of queries using global dense retrieval;
3. final context tokens: retrieved chunk tokens sent to the generator.

The main paper claim uses the third layer. Historical routing experiments
showed that reducing candidate counts does not automatically reduce final
context tokens when the final context remains fixed at top-10.
Table~\ref{tab:c1} records the correction audit that motivated this separation.

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

This audit motivated explicit final-context control. The conservative historical
policy reduces context size in high-confidence cases, while the stronger main
result uses an independently calibrated length budget. Neither candidate-count
savings nor route confidence alone establishes prompt-token savings.

## D. Secondary Datasets and Boundary Cases

The secondary datasets have different roles and should not be pooled into the
main LoTTE evidence claim.

- **PubMedQA** is an evidence-retrieval proof-of-concept near a dense ceiling.
  Dense reaches $\mathrm{Hit@10}=0.9930$; trust-weighted feedback reaches
  $\mathrm{Hit@10}=0.9940$, last reward $0.8727$, and selected-cluster hit
  $0.8860$. The ground truth is abstract-level context, not a strict answer
  sentence.
- **Banking77** is an intent-routing proxy rather than an evidence-retrieval
  benchmark. Dense/reference $\mathrm{Hit@10}$ is $0.9805$; trust-weighted
  feedback reaches $\mathrm{Hit@10}=0.9844$, last reward $0.9805$, and
  selected-cluster hit $0.9983$. It supports the feedback mechanism, not the
  main evidence-retrieval headline.
- **eManual** is a duplicate-text limitation case. Strict dense
  $\mathrm{Hit@10}$ is $0.3231$, text-equivalent dense $\mathrm{Hit@10}$ is
  $0.5615$, and deduplicated dense $\mathrm{Hit@10}$ rises to $0.8615$. Strict
  chunk IDs can therefore understate useful retrieval.
- **CUAD** is a sparse legal smoke/stress case. Dense/reference
  $\mathrm{Hit@10}$ is $0.0759$ and the trust-weighted smoke reaches
  $\mathrm{Hit@10}=0.0886$. It is a GT-anchored sample, not positive
  full-corpus evidence.

### D.1 eManual Duplicate-Text Diagnostic

eManual contains 18,812 corpus chunks but only 1,729 unique text strings.
Strict chunk-id evaluation can therefore mark semantically equivalent
retrievals as incorrect.
Table~\ref{tab:d1} quantifies the strict, text-equivalent, and deduplicated views.

**Appendix Table D1. eManual strict, text-equivalent, and deduplicated
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
Tables~\ref{tab:e1} and~\ref{tab:e2} report encoder-family and matched-backbone robustness.

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

**Appendix Table E2. Matched-backbone context-budget robustness on the frozen
LoTTE technology/search 100k split.**

| Backbone | Route mode | Dense $\mathrm{Hit@10}$ | Method $\mathrm{Hit@10}$ | Hit delta | Token saving |
|---|---|---:|---:|---:|---:|
| MiniLM | calibrated multi-route | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE-base | full multi-route | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| E5-base | full multi-route | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| BGE-base | quality-first | 0.8993 | 0.9081 | +0.88 pp | 7.23% |

The full multi-route rows show that the quality-cost pattern is not tied to the
MiniLM backbone. More aggressive gated BGE/E5 variants lose more hit and are
treated as boundary settings. The BGE quality-first row demonstrates that the
frontier is tunable; an equivalent above-dense E5 point was not found on this
split.

## F. Downstream Answer-Level Evaluation

The formal downstream evaluation uses 300 deterministic queries from the
frozen LoTTE technology/search 100k test split. Seven methods produce 2,100
answers with `deepseek-v4-flash`. The fixed answers receive 2,100 DeepSeek,
2,100 GLM-5.2, and 2,065 MiniMax-M3 schema-valid judgments. Cross-judge
statistics use the 2,065 query-method keys shared by all judges.
Tables~\ref{tab:f1}, \ref{tab:f2}, \ref{tab:f3}, \ref{tab:f4},
and~\ref{tab:f5} report method results, paired tests, judge coverage,
agreement, and majority-vote comparisons.

**Appendix Table F1. DeepSeek-judged downstream answer and context results.**

| Method | Correct | Faithful | Strict citation support | Insufficient context | Avg context tokens | Tokens / correct |
|---|---:|---:|---:|---:|---:|---:|
| MiniLM dense | 0.9200 | 0.9533 | 0.3533 | 0.0967 | 1461 | 1588 |
| BGE dense | 0.9167 | 0.9433 | 0.3567 | 0.0767 | 1698 | 1852 |
| BGE IntentRoute | 0.9167 | 0.9200 | 0.3700 | 0.0767 | 1596 | 1741 |
| E5 dense | 0.9167 | 0.9300 | 0.4100 | 0.0700 | 1525 | 1663 |
| E5 IntentRoute | 0.9200 | 0.9333 | 0.3633 | 0.0567 | 1341 | 1458 |
| Dense+MMR | 0.8900 | 0.9100 | 0.0733 | 0.0800 | 1240 | 1393 |
| IntentRoute+MMR | 0.9133 | 0.9267 | 0.0833 | 0.0900 | 1157 | 1267 |

**Appendix Table F2. Original DeepSeek-judged paired downstream comparisons.**

| Comparison | Correct delta | 95% CI | McNemar $p$ | Token saving | 95% CI |
|---|---:|---:|---:|---:|---:|
| BGE IntentRoute vs dense | +0.00 pp | [-2.67, +2.67] pp | 1.000 | 6.00% | [4.01%, 7.97%] |
| E5 IntentRoute vs dense | +0.33 pp | [-3.00, +3.67] pp | 1.000 | 12.04% | [9.93%, 14.16%] |
| IntentRoute+MMR vs Dense+MMR | +2.33 pp | [-1.67, +6.33] pp | 0.324 | 6.65% | [4.28%, 8.97%] |

The context-saving intervals are positive while correctness intervals include
zero. The multi-judge extension below tests whether this conclusion depends on
the original DeepSeek judge.

**Appendix Table F3. Multi-judge coverage and calibration.**

| Judge | Valid | Coverage | Correctness mean | Correct | Faithfulness mean | Faithful | Citations supported |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek | 2,100 | 100.00% | 4.672 | 91.33% | 4.782 | 93.10% | 89.57% |
| GLM-5.2 | 2,100 | 100.00% | 4.551 | 88.24% | 4.734 | 92.81% | 92.14% |
| MiniMax-M3 | 2,065 | 98.33% | 4.293 | 85.71% | 4.633 | 95.45% | 94.48% |

MiniMax-M3 rejects 35 query-method inputs spanning 18 queries through
provider-side content filtering. These values are not imputed. Absolute score
calibration differs across judges, so raw ordinal scores are not pooled.

**Appendix Table F4. Pairwise agreement on 2,065 shared judgments.**

| Field | Judge pair | Raw agreement | Cohen's $\kappa$ |
|---|---|---:|---:|
| Correct | DS / GLM | 91.04% | 0.508 |
| Correct | DS / MM | 89.88% | 0.503 |
| Correct | GLM / MM | 92.15% | 0.653 |
| Faithful | DS / GLM | 91.72% | 0.364 |
| Faithful | DS / MM | 93.27% | 0.374 |
| Faithful | GLM / MM | 93.41% | 0.405 |

Here DS denotes DeepSeek and MM denotes MiniMax-M3. Three-judge unanimity is
86.54% for correctness and 89.20% for faithfulness.
The corresponding majority-positive rates are 88.96% and 95.35%. High raw
faithfulness agreement coexists with lower $\kappa$ because positive judgments
are highly prevalent.

**Appendix Table F5. Three-judge-majority paired comparisons.**

| Comparison | $n$ | Correct delta (95% CI) | McNemar $p$ | Faithful delta (95% CI) | McNemar $p$ | Context saving (95% CI) |
|---|---:|---:|---:|---:|---:|---:|
| BGE IntentRoute vs dense | 289 | -3.46 pp [-6.92, 0.00] | 0.0755 | -4.15 pp [-6.92, -1.73] | 0.0018 | 6.27% [4.22%, 8.26%] |
| E5 IntentRoute vs dense | 289 | -2.08 pp [-5.88, +1.73] | 0.3616 | -0.69 pp [-3.81, +2.42] | 0.8238 | 11.97% [9.78%, 14.17%] |
| IntentRoute+MMR vs Dense+MMR | 295 | +0.34 pp [-3.39, +4.07] | 1.0000 | +4.07 pp [+0.68, +7.46] | 0.0290 | 6.75% [4.40%, 9.11%] |

No individual judge or majority-vote comparison finds a significant
correctness difference. This supports a bounded correctness-robustness claim,
not strict non-inferiority. Faithfulness is mixed: the BGE majority result is
negative, while the SentMMR composition is positive. The evaluation remains
LLM-as-judge evidence rather than human evaluation. The under-specified
`insufficient_context_appropriate` field is retained in raw artifacts but
excluded from headline analysis.

## G. Calibration/Test Context-Budget Validation

The calibration/test protocol selects the final-context budget on calibration
queries and freezes it before evaluation on held-out test queries.
Tables~\ref{tab:g1}, \ref{tab:g2}, \ref{tab:g3}, and~\ref{tab:g4} report the
frozen split, independent calibration, partition sensitivity, and normalized
five-fold audit.

**Appendix Table G1. Frozen context-budget validation on LoTTE technology/search.**

| Scale | Selected policy | Calibration eligible | Hit delta vs dense | Token saving | Dense adaptive hit delta | Dense adaptive token saving |
|---|---|---:|---:|---:|---:|---:|
| 100k | `token_budget_r0.95_m4` | True | +0.00 pp | 6.18% | -1.44 pp | 13.83% |
| 200k | `token_budget_r0.85_m4` | True | +1.20 pp | 16.00% | -2.40 pp | 21.95% |
| 400k | `token_budget_r0.98_m4` | False / original split | +2.32 pp | 6.57% | -0.24 pp | 11.44% |
| 638k | `token_budget_r0.85_m4` | True | -0.08 pp | 17.53% | -3.84 pp | 21.90% |

The calibrated policies should be compared against dense-only adaptive
truncation because both reduce final context size. IntentRoute preserves
substantially more $\mathrm{Hit@10}$ at a still meaningful token saving level.
The 400k row is diagnostic rather than calibration-eligible in the original
artifact set. Appendix Table G4 reports the completed cross-fitted follow-up.

**Appendix Table G2. Independently calibrated 100k quality constraints.**

| Calibration Hit margin | IntentRoute policy | IR test Hit delta | IR saving | Dense policy | Dense test Hit delta | Dense saving |
|---:|---|---:|---:|---|---:|---:|
| 0.0pp | `r0.95/m4` | +0.00pp | 6.18% | `r1.00/m4` | +0.00pp | 0.00% |
| 0.5pp | `r0.93/m4` | -0.32pp | 7.97% | `r1.00/m4` | +0.00pp | 0.00% |
| 1.0pp | `r0.84/m4` | -1.28pp | 17.13% | `r1.00/m4` | +0.00pp | 0.00% |
| 2.0pp | `r0.80/m4` | -1.60pp | 20.90% | `r0.82/m4` | -2.40pp | 25.22% |

The zero-margin row preserves equal mean test Hit while selecting nonzero
IntentRoute saving, but strict seed-level non-inferiority remains 0/3. Held-out
same-saving interpolation is descriptive only and finds small IntentRoute-minus-
Dense Hit differences from `+0.47pp` at 5% saving to `-0.01pp` at 20%.

**Appendix Table G3. Calibration-partition sensitivity over 20 overlapping splits.**

| Scale | Eligible splits | Test Hit range | Mean test Hit delta | Saving range | Within 1pp of dense |
|---|---:|---:|---:|---:|---:|
| 100k | 12/20 | [-2.00, +0.72]pp | -0.45pp | [6.18%, 17.73%] | 14/20 |
| 200k | 19/20 | [+0.56, +3.52]pp | +1.53pp | [5.33%, 17.29%] | 20/20 |
| 400k | 16/20 | [-2.08, +2.80]pp | +0.45pp | [6.57%, 18.27%] | 17/20 |
| 638k | 19/20 | [-0.88, +2.24]pp | +0.44pp | [7.85%, 17.91%] | 20/20 |

These partitions reuse the same frozen rankings and overlap in their query
membership. They diagnose policy-selection sensitivity and must not be counted
as 20 independent experiments. The result supports stronger split stability at
200k/638k, moderate sensitivity at 100k, and continued diagnostic treatment of
400k.

**Appendix Table G4. Normalized five-fold out-of-fold calibration using identical canonical query folds and policy rules across scales.**

| Scale | Eligible folds | Mean Hit delta | Mean token saving | Strict NI seeds | Selected-policy count | Dense compressed folds |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 2/5 | -1.06pp | 4.16% | 0/3 | 2 | 0/5 |
| 200k | 5/5 | +1.40pp | 16.07% | 2/3 | 1 | 0/5 |
| 400k | 5/5 | +0.00pp | 14.50% | 0/3 | 5 | 0/5 |
| 638k | 5/5 | +0.28pp | 15.23% | 0/3 | 3 | 0/5 |

Each canonical LoTTE query is held out exactly once and remains in the same
fold at every corpus scale. Dense and IntentRoute independently select from
the predefined budget grid; when no policy satisfies the zero-drop gate,
the method uses Dense top-10 fallback. The 400k result closes the missing
normalized calibration check, but its five distinct policies and 0/3 strict
non-inferiority result retain the partition-sensitivity boundary. The 100k row
similarly shows that positive original-split behavior does not imply uniform
cross-fitted behavior.

## H. Cross-Domain Validation

LoTTE science/search is used as a second-domain validation, not as a replacement
for the main LoTTE technology/search scale-up.
Tables~\ref{tab:h1} and~\ref{tab:h2} separate ranking transfer from frozen-budget behavior.

**Appendix Table H1. Science/search fixed top-10 ranking validation.**

| Domain/scale | Corpus chunks | Queries | Dense $\mathrm{Hit@10}$ | IntentRoute $\mathrm{Hit@10}$ | Hit delta |
|---|---:|---:|---:|---:|---:|
| science/search 20k/q200 | 20,490 | 200 | 0.8950 | 0.9267 | +3.17 pp |
| science/search 100k | 101,187 | 596 | 0.8926 | 0.9077 | +1.51 pp |

**Appendix Table H2. Science/search frozen context-budget validation.**

| Domain/scale | Budget policy | Seed | Frozen test hit delta vs dense | Token saving | Strict NI by CI |
|---|---|---:|---:|---:|---:|
| 20k/q200 | `token_budget_r0.85_m4` | 13 | +2.86 pp | 13.18% | True |
| 20k/q200 | `token_budget_r0.85_m4` | 17 | +1.43 pp | 14.31% | False |
| 20k/q200 | `token_budget_r0.85_m4` | 19 | +0.71 pp | 13.91% | False |
| 100k | `token_budget_r0.85_m4` | 13 | -1.20 pp | 19.21% | False |
| 100k | `token_budget_r0.85_m4` | 17 | +0.00 pp | 17.53% | False |
| 100k | `token_budget_r0.85_m4` | 19 | -0.96 pp | 20.53% | False |

The fixed top-10 ranking gains transfer, while aggressive final-context budgets
require domain and scale calibration.

## I. Feedback-Driven Hard-Case Recovery

Hard-case recovery focuses on affected queries where dense top-10 retrieves at
least one GT chunk but the budgeted IntentRoute context misses.
Tables~\ref{tab:i1} and~\ref{tab:i2} distinguish same-query repair from held-out recovery.

**Appendix Table I1. Same-query feedback recovery on affected queries.**

| Domain | Retry method | Affected queries | Recovered | Recovery rate | Avg token saving vs dense |
|---|---|---:|---:|---:|---:|
| science 100k | arm boost | 34 | 5 | 14.71% | 17.40% |
| science 100k | arm boost + conservative budget | 34 | 14 | 41.18% | 5.76% |
| science 100k | full-context fallback | 34 | 17 | 50.00% | -8.07% |
| technology 100k | arm boost | 42 | 8 | 19.05% | 13.68% |
| technology 100k | arm boost + conservative budget | 42 | 9 | 21.43% | 11.75% |
| technology 100k | full-context fallback | 42 | 12 | 28.57% | 0.96% |

Same-query retry is post-feedback repair evidence. It is not a first-pass
generalization result.

**Appendix Table I2. Calibration-to-test recovery generalization.**

| Domain | Frozen test recovery policy | Mean hit delta versus budgeted-before-feedback | Avg token saving vs dense |
|---|---|---:|---:|
| science 100k | conservative budget on learned risky arms after calibration | +0.16 pp | 16.13% |
| science 100k | full-context fallback on learned risky arms after calibration | +0.48 pp | 13.09% |
| technology 100k | conservative budget on learned risky arms after calibration | -0.16 pp | 5.88% |
| technology 100k | full-context fallback on learned risky arms after calibration | +0.16 pp | 4.25% |

The held-out effect is small and domain-dependent. Feedback should therefore be
used as a controlled fallback trigger rather than as unconditional global
reranking.

## J. Strong Post-Retrieval Baselines

These baselines test whether simpler post-retrieval operations explain the
main final-context result.
Tables~\ref{tab:j1}, \ref{tab:j2}, \ref{tab:j3}, and~\ref{tab:j4} report
matched compression, reranking, and prompt-pruning controls.

**Appendix Table J1. Dense+Sentence-MMR same-budget baseline on LoTTE
technology/search 100k.**

| Budget target | $\mathrm{Hit@10}$ | Hit delta vs dense | $\mathrm{EvidenceRecall@10}$ | Avg context tokens | Token saving vs dense |
|---|---:|---:|---:|---:|---:|
| Dense top-10 | 0.8705 | 0.0000 | 0.7081 | 1470.1 | 0.00% |
| SentMMR seed13 budget | 0.8705 | 0.0000 | 0.7081 | 1287.8 | 12.40% |
| SentMMR seed17 budget | 0.8705 | 0.0000 | 0.7075 | 1278.0 | 13.07% |
| SentMMR seed19 budget | 0.8705 | 0.0000 | 0.7081 | 1302.1 | 11.43% |

Dense+Sentence-MMR preserves dense chunk-support on this split while reducing
selected sentence tokens. It is therefore a strong final-context compression
baseline, not a weak control.

**Appendix Table J2. Compressor-normalized comparison on LoTTE
technology/search 100k.**

| Source pool | Method | Ratio | $\mathrm{Hit@10}$ range | Saving vs dense |
|---|---|---:|---:|---:|
| Dense | top-10 | - | 0.8705 | 0.00% |
| Dense | SentMMR | 0.95 | 0.8705 | 5.33% |
| Dense | SentMMR | 0.90 | 0.8705 | 10.22% |
| Dense | SentMMR | 0.85 | 0.8705 | 15.16% |
| IntentRoute | target | - | 0.8657-0.8777 | 4.98-7.14% |
| IntentRoute | SentMMR | 0.95 | 0.8657-0.8777 | 10.07-12.14% |
| IntentRoute | SentMMR | 0.90 | 0.8657-0.8777 | 14.72-16.68% |
| IntentRoute | SentMMR | 0.85 | 0.8657-0.8777 | 19.41-21.24% |

Applying the same compressor to dense and IntentRoute evidence pools supports
the route-and-budget controller framing. The compressor is shared; the evidence
pool and budget controller determine the starting point.

**Appendix Table J3. Cross-encoder reranker baseline on LoTTE
technology/search 100k.**

| Method | $\mathrm{Hit@10}$ | $\mathrm{EvidenceRecall@10}$ | Avg context tokens | Token saving vs dense |
|---|---:|---:|---:|---:|
| Dense top-10 | 0.8705 | 0.7081 | 1470 | 0.00% |
| Cross-encoder top-10 | 0.8777 | 0.7332 | 1792 | -21.91% |
| IntentRoute target | 0.8657-0.8777 | 0.6766-0.6871 | 1365-1397 | 4.98-7.14% |
| Cross-encoder same budget | 0.8633-0.8729 | 0.6975-0.7044 | 1360-1390 | 5.43-7.49% |

The cross-encoder reranker improves full top-10 support metrics, but that full
reranked context is longer on average. Under the same per-query token budgets
as IntentRoute, reranking does not uniformly dominate the calibrated
controller.

**Appendix Table J4. SelectiveContext-lite prompt-pruning baseline.**

| Source pool | Ratio | $\mathrm{Hit@10}$ | Token saving vs dense | Extra saving vs source |
|---|---:|---:|---:|---:|
| Dense | 0.95 | 0.8705 | 5.66% | 5.66% |
| Dense | 0.90 | 0.8705 | 10.42% | 10.42% |
| Dense | 0.85 | 0.8705 | 15.31% | 15.31% |
| Dense | 0.75 | 0.8705 | 25.19% | 25.19% |
| IntentRoute | 0.95 | 0.8657-0.8777 | 10.38-12.42% | 5.62-5.69% |
| IntentRoute | 0.90 | 0.8657-0.8777 | 14.92-16.87% | 10.46-10.48% |
| IntentRoute | 0.85 | 0.8657-0.8777 | 19.53-21.40% | 15.31-15.35% |
| IntentRoute | 0.75 | 0.8657-0.8777 | 28.95-30.57% | 25.20-25.23% |

SelectiveContext-lite is a deterministic local proxy, not LLMLingua. Its role
is to show that prompt pruning can be stacked after either evidence pool and
does not replace upstream route control or final-budget calibration.

## K. Route-Control Attribution and Arm Sensitivity

Tables~\ref{tab:k1}, \ref{tab:k2}, \ref{tab:k3}, and~\ref{tab:k4} isolate
geometry, feedback, arm granularity, and frozen-trajectory route mediation.

**Appendix Table K1. Static geometry versus uniform-random route control.**

| Setting | Full top-10 hit | Route reward | Selected-cluster hit | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Static nearest geometry | 0.8764 | 0.8563 | 0.8870 | +1.44 pp | 5.03% |
| Uniform random control | 0.8842 | 0.1499 | 0.1577 | +1.04 pp | 11.92% |

Dense/BM25 rescue keeps final fused hit high in both rows, while route reward
and selected-cluster hit separate meaningful local routing from random arm
selection. Geometry is therefore supported as a route-control signal, not a
standalone explanation of final fused quality.

**Appendix Table K2. Feedback and static route controls.**

| Setting | Route reward | Selected-cluster hit | Dense rate | Test hit delta | Token saving |
|---|---:|---:|---:|---:|---:|
| Learned full multi-route | 0.6790 | 0.5766 | 1.0000 | -1.68 pp | 17.86% |
| Learned gated | 0.6790 | 0.5766 | 0.7377 | -5.20 pp | 11.83% |
| Static nearest gated | 0.8563 | 0.8870 | 0.9586 | -2.40 pp | 12.01% |
| No-feedback gated | 0.1504 | 0.1570 | 1.0000 | -1.60 pp | 16.56% |

Feedback-updated LinUCB improves route quality over no-feedback/random controls,
but the learned gated threshold is a cost-aggressive boundary. Static geometry
remains a strong prior, while dense fallback explains part of the fused result.

**Appendix Table K3. Arm-count sensitivity.**

| $K$ | Static route reward | Full test hit delta | Full token saving | Gated dense rate | Gated hit delta |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.9128 | +1.44 pp | 6.23% | 0.4083 | -1.84 pp |
| 16 | 0.8826 | +0.80 pp | 10.49% | 0.6089 | -1.68 pp |
| 32 | 0.8563 | +0.56 pp | 4.68% | 0.7377 | -4.48 pp |
| 64 | 0.8272 | +0.40 pp | 11.19% | 0.8986 | -3.76 pp |
| 128 | 0.8479 | +1.20 pp | 10.23% | 0.9502 | -3.12 pp |

Full multi-route quality is stable across the tested grid, whereas gated
dense-saving behavior depends on arm granularity. Cross-scale correlations
between geometry diagnostics and final quality-cost gain are mixed and
small-sample; final behavior belongs to the complete calibrated controller.

**Appendix Table K4. Frozen-trajectory dynamic route mediation; Save is relative
to uncompressed dense.**

| Route | Src. Hit | Budget Hit | Save |
|---|---:|---:|---:|
| Gated | 0.8793 | 0.8705 | 6.18% |
| Full | 0.8841 | 0.8745 | 5.27% |
| Shuffled | 0.8313 | 0.8225 | 6.54% |
| Cluster | 0.7698 | 0.7626 | 6.93% |
| Dense | 0.8705 | 0.8561 | 13.83% |

The replay freezes selected arms and feedback state, and exactly reproduces the
original dynamic ranking before changing route shapes. Dynamic gating exceeds
the shuffled-tier control by 4.80 percentage points before and after the common
budget, with 3/3 paired intervals excluding zero. It does not exceed fixed full
fusion; instead, it exposes a bounded quality-cost trade-off. Route confidence
has no detected association with oracle safe-token headroom, so the result
supports route assignment rather than direct compression-safety prediction.

## L. Reproducibility and Reporting Guardrails

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
