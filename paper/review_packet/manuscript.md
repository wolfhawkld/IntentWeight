# IntentRoute: Geometry-Guided and Feedback-Adaptive Route Confidence for Efficient Evidence Selection

<!-- Generated review packet. Edit source chapters under paper/full_draft/. -->

# Abstract

Retrieval-augmented systems must balance evidence coverage, noise, and
language-model context cost. IntentRoute separates feedback-adaptive route
control from calibrated context budgeting. Dense, BM25, and geometry-defined
cluster-local routes produce evidence; trust-weighted LinUCB estimates route
confidence; independent calibration sets final context size; and Dense remains
a recall floor. A piecewise
relevance-manifold hypothesis motivates local routes, with geometry treated as
diagnostic rather than proof of relevance.

We evaluate nine dataset settings across eight domain areas. LoTTE
technology/search supplies 100k-638k scale evidence; science/search tests
domain and scale transfer; preregistered recreation/search and writing/search
100k studies test domain heterogeneity; and biomedical, banking, manual, and
legal settings provide transfer, mechanism, and boundary checks. At
calibration-eligible technology/search points, IntentRoute reduces final
evidence-context tokens by 6-18% while preserving near-dense query-level
$\mathrm{Hit@10}$ and avoiding the larger losses of dense-only adaptive
truncation. On 300 frozen queries, matched variants reduce
context by 6-12% with no statistically detectable correctness difference
across three judges, although faithfulness is not uniformly preserved. In the
preregistered expansion, no-feedback routes save 10.09% with a +0.12pp mean Hit
change on writing/search, but 5.42% with -0.76pp and 0/3 strict
non-inferiority seeds on recreation/search; trust-weighted calibration falls
back to Dense in both. Both retain cluster-local signal, showing domain
heterogeneity rather than a direct geometry-to-compression guarantee.
Controlled feedback supports repeated-interaction adaptation and conditional
recovery, not a universal first-pass gain on unseen queries. These results
support a bounded quality-efficiency controller, not a universal dense
replacement.

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

We evaluate IntentRoute across nine dataset settings with deliberately tiered
evidentiary roles. LoTTE technology/search supplies the full-stack,
large-scale quality-efficiency evaluation from 100k to 638k chunks. A separate
LoTTE science/search study tests cross-domain transfer at 20k, 100k, and 200k
corpus scales. Preregistered LoTTE recreation/search and writing/search 100k
studies apply the same common protocol to test domain heterogeneity rather than
to select another favorable replication. PubMedQA and CovidQA-RAG test biomedical evidence-retrieval
transfer under near-ceiling and more discriminative dense baselines,
respectively; Banking77 tests feedback adaptation in banking-intent routing;
and eManual and CUAD expose duplicate-text, strict chunk-identity, and
sparse-ground-truth boundaries in manual and legal retrieval. We do not pool
these settings as if their tasks, labels, and evidence strength were
interchangeable. Instead, LoTTE technology/search anchors the complete
retrieval-and-budget claim, science/search tests cross-domain and scale
transfer, recreation/search and writing/search test the heterogeneity of the
same 100k operating frontier, and the other datasets test transfer, mechanism,
and failure boundaries.

On LoTTE technology/search, we scale from 100k to 638k corpus chunks and
compare against dense-only retrieval using
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
method-dependent. LoTTE science/search provides cross-domain evidence;
recreation/search and writing/search show that cluster-local route signal can
persist while independently calibrated token saving and strict seed-level
non-inferiority remain domain-dependent;
PubMedQA and CovidQA-RAG provide biomedical transfer checks; Banking77 provides
an intent-routing feedback check; and eManual and CUAD expose evaluation and
data-quality boundaries. Together with feedback-driven hard-case recovery,
these settings broaden the transfer, mechanism, and boundary evidence without
extending the LoTTE token-saving headline to incomparable tasks.

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
3. We provide frozen calibration/test evidence from 100k to 638k LoTTE
   technology/search chunks, cross-domain LoTTE science/search replication,
   preregistered recreation/search and writing/search 100k external-validity
   tests, matched BGE/E5 backbones, and a tunable BGE quality-first point,
   separating token reduction from retrieval-quality non-inferiority with
   paired query-level statistics.
4. We compare against shared sentence and prompt compression plus
   cross-encoder reranking, showing that IntentRoute is an upstream controller
   that composes with rather than replaces these downstream layers.
5. We add a 300-query, three-judge answer-level evaluation, controlled
   feedback recovery, PubMedQA and CovidQA-RAG biomedical transfer checks,
   Banking77 mechanism checks, and eManual and CUAD boundary analyses to
   evaluate the controller across nine dataset settings without conflating
   their evidentiary roles.

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

Recent work sharpens this distinction between internal and external adaptation
signals. SeaKR activates retrieval from uncertainty extracted from language
model internal states [@yao2025seakr], whereas an LLM-independent study compares
external query features as lightweight retrieval triggers [@marina2025llm].
These methods primarily decide whether or how to invoke retrieval from a
single-query signal. IntentRoute instead keeps dense retrieval as a recall
floor, routes among fixed corpus-local evidence paths, and updates route
confidence from controlled feedback over repeated interactions.

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

More recent adaptive compressors vary retained context from model attention or
input complexity rather than applying one fixed compression rate
[@luo2025attncomp; @guo2025adaptivecompression]. These approaches operate on
the retrieved context and commonly require an attention-based or hierarchical
compression component. They are complementary rather than direct replacements
for IntentRoute's upstream evidence-route selection and independently
calibrated chunk-budget policy.

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

---

# 4. Experimental Setup

## 4.1 Datasets

The experiments cover nine dataset settings across eight domain areas:
technology, science, recreation, writing, biomedical QA, banking intents,
product manuals, and legal contracts. They have different tasks, ground-truth
semantics, and evidentiary roles, so we do not treat them as equal support for
the main claim:

- **LoTTE technology/search** is the main large-scale vertical-domain evidence
  benchmark. We evaluate nested corpus scales from 100k to 638k chunks with
  596 test queries.
- **LoTTE science/search** is the cross-domain validation benchmark. It tests
  whether ranking and context-budget behavior transfer beyond technology/search
  at 20k/q200, 100k, 200k, and 400k scales. The 400k row is retained as a
  scale boundary rather than a lossless-compression replication.
- **LoTTE recreation/search and writing/search** are preregistered 100k
  external-validity tests with 924 and 1,071 positive-qrel queries,
  respectively. Both use the full common protocol and remain in the analysis
  after the preregistered lexicality ordering is contradicted by the measured
  query-positive overlap.
- **PubMedQA and CovidQA-RAG** are biomedical transfer checks. PubMedQA is an
  evidence-retrieval proof-of-concept with abstract-level ground truth and a
  near-ceiling dense baseline; CovidQA-RAG is a more discriminative native-full
  RAGBench evidence-retrieval row.
- **Banking77** is a supporting feedback-adaptation check for intent routing
  rather than a strict evidence-retrieval benchmark.
- **eManual and CUAD** are boundary cases. eManual exposes duplicate-text and
  strict chunk-id issues; CUAD is a sparse GT-anchored legal-domain smoke case.

This hierarchy separates full-stack evidence, cross-domain transfer, mechanism
transfer, and boundary analysis. The complete quality-efficiency claim is
anchored in LoTTE technology/search, science/search tests domain transfer, and
recreation/search and writing/search test domain heterogeneity under a matched
100k protocol. The secondary datasets test whether feedback behavior transfers,
whether a biomedical evidence-retrieval transfer row remains discriminative,
or where corpus duplication and sparse labels limit inference.

The supplementary protocol registry records the dataset/query scope, route-feedback
protocol, context-budget endpoint, and evidentiary role for each result family.
It distinguishes the common evidence-retrieval protocol from the Banking77
intent proxy, the CUAD sparse-GT boundary, and historical fixed-split
diagnostics. This prevents unlike evaluation families from being treated as
pooled replications.

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

MRR@K uses the reciprocal rank of the first relevant chunk, and nDCG@K uses
binary relevance with logarithmic rank discount and the standard ideal-DCG
normalization. Supplementary Section S12 gives the explicit formulas and the
zero-relevance convention.

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
adaptation analysis. They are not IID held-out generalization results.

The formal frozen-policy audit makes the complementary first-pass boundary
explicit. It trains route state on four disjoint query folds, freezes policy and
feedback memory, and ranks the fifth fold once without held-out updates. Across
LoTTE technology/search and science/search 100k, learned full routing remains
near or above Dense but does not exceed matched static-nearest or cold
no-feedback full routing; learned gating is significantly below Dense in all
three route seeds. This audit is retrieval-only and does not evaluate
final-context token saving or answer quality.

## 4.6 Implementation Notes

The main dense baseline uses Sentence Transformers `all-MiniLM-L6-v2` with exact
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
margin as a strict seed-level engineering guardrail. On the original 417-query
frozen test split, one percentage point corresponds to roughly four query-hit
outcomes; on the 596-query out-of-fold population, it corresponds to roughly
six. Passing this diagnostic is not treated as formal equivalence, and failing
it does not erase the descriptive paired result. This separates two claims:
whether the method preserves retrieval quality under a conservative paired
criterion, and whether it reduces the final evidence-context tokens sent to
the generator.

The frozen calibration/test comparisons and the normalized five-fold scale
results are the primary evidence families. Fine-grid action selection,
overlapping-partition sensitivity, same-saving interpolation, arm-count and
geometry controls, feedback recovery, transfer datasets, and multi-judge
analysis are mechanism, robustness, or boundary analyses. We report their
paired statistics where available, but do not pool heterogeneous conditions or
use an unadjusted cross-condition $p$-value to assert a global superiority
claim. They are interpreted conditionally and labeled accordingly.

The preregistered domain expansion applies the normalized five-fold protocol to all
924 recreation/search and 1,071 writing/search positive-qrel queries. Each
domain uses the same MiniLM backbone, $K=32$, route seeds 13/17/19, eight
prequential epochs, fixed top-10 endpoint, predefined budget grid, zero-drop
eligibility gate, Dense fallback, paired bootstrap, McNemar analysis, and 1pp
seed-level non-inferiority guardrail. The domains are calibrated and reported
separately; no cross-domain pooled effect is computed.

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
strict non-inferiority remains `0/3` seeds. Supplementary Table S16 reports the fold-level
results. This supports the average 400k trade-off without erasing the original
split failure or claiming stable policy selection.

Query-level paired bootstrap intervals and McNemar-style win/loss counts show
that token savings are more consistent than strict quality non-inferiority.
The conservative confidence-only policy remains a stable 4.7-5.3% saving
baseline; complete seed and policy details are reported in Supplementary Sections S1 and S7.
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
tunability is BGE-specific rather than a universal claim. Supplementary Section S5 reports
the supporting encoder details.

## 5.3 Route-Control Attribution

The route controls isolate geometry, feedback, and dense rescue. The
geometry-versus-random rows change arm selection under an otherwise matched
full rescue surface. The learned, static, and no-feedback rows test whether
LinUCB updates and gating explain route quality and final cost.
Table~\ref{tab:3} separates route-level effects from rescued final quality.

**Table 3. Geometry, feedback, and rescue-route controls on LoTTE technology/search 100k. Each row uses its paired frozen-protocol dense baseline.**

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
recovers 23 of 76 budget-induced misses across the technology/search and
science/search 100k settings, but
the stricter calibration-to-test effect is small and domain-dependent.
Supplementary Sections S9 and S11 contain the full recovery and control tables.

The formal frozen-policy audit separates this repeated-interaction evidence from
first-pass transfer to unseen queries. Across five folds and seeds 13/17/19,
learned full routing is above Dense on average in technology/search 100k
(+1.17pp) and science/search 100k (+0.78pp), but it does not exceed matched
cold no-feedback full routing (-0.11pp and -0.39pp) or static-nearest full
routing (+0.28pp and -0.56pp); no such paired comparison is significant across
all seeds. Learned gated routing is instead significantly below Dense by 4.08pp
and 5.59pp in the two domains. Thus, the full rescue surface transfers, whereas
controlled feedback is supported as repeated-query adaptation and conditional
recovery rather than a universal frozen first-pass improvement.

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

Across LoTTE technology/search scales, nearest-cluster hit remains high while context retention
and PCA concentration vary. Figure 3 relates context retention to observed hit
delta and token saving. The small cross-scale sample does not show a
deterministic geometry-to-gain law: geometry identifies plausible local route
structure, while calibration, fusion, and dense rescue determine the final
operating point. Full diagnostics are retained in Supplementary Section S11.

## 5.5 Cross-Domain, Mechanism, And Boundary Evidence

On LoTTE science/search, fixed top-10 IntentRoute reaches
$\mathrm{Hit@10}=0.9267$ versus 0.8950 for dense at 20k/q200 and 0.9077 versus
0.8926 at 100k. Frozen budget policies save 13-14% tokens at 20k/q200 while
remaining above dense. At 100k, the more aggressive policy saves 17-21% but
can introduce small hit losses. The ranking signal transfers, but compression
strength requires domain- and scale-specific calibration. Supplementary Section S8 reports
the complete seed-level table.

The matched five-fold protocol makes this boundary explicit on the
shared 596-query science/search population. At 100k, 200k, and 400k, the mean
IntentRoute $\mathrm{Hit@10}$ deltas are -0.11pp, -0.67pp, and -0.67pp, with
16.88%, 10.75%, and 3.15% final-context token saving, respectively; strict
1pp non-inferiority is `0/3` seeds at every scale. At 400k, only one of five
folds selects a compressed policy. Its recovery replay has only 3-6
budget-induced affected queries per seed, so it closes a protocol endpoint but
does not overturn the scale-boundary interpretation. The supplementary protocol
registry records the matched protocol and evidence roles without pooling these rows into
the technology/search headline.

The preregistered recreation/search and writing/search 100k expansion tests
whether this heterogeneity persists under a matched protocol. Both domains
show usable static cluster-local signal: $\mathrm{NearestClusterHit@3}$ is
0.8366 on recreation/search and 0.8655 on writing/search. Their independently
calibrated no-feedback frontiers differ. Recreation/search selects compression
in four of five folds, with a -0.76pp mean $\mathrm{Hit@10}$ change, 5.42%
token saving, and strict 1pp non-inferiority in 0/3 seeds. Writing/search
selects compression in all five folds, with a +0.12pp mean Hit change, 10.09%
saving, and strict non-inferiority in 2/3 seeds. Trust-weighted calibration
selects no compressed fold in either domain and therefore uses Dense fallback.
The preregistered assumption that recreation/search was more lexical is
directionally reversed by measured query-positive overlap, so it is not used
to explain the frontier contrast. Supplementary Table S30 reports the matched
domain and controller rows. The result extends the geometry and
quality-context evidence beyond technology/science while establishing domain
heterogeneity, not universal strict non-inferiority or a direct
geometry-to-compression causal link.

The supporting transfer checks cover different retrieval abstractions and dense
ceilings. On PubMedQA, dense retrieval reaches $\mathrm{Hit@10}=0.9930$, while
the trust-weighted policy reaches $0.9940$ with selected-cluster hit $0.8860$.
CovidQA-RAG is more discriminative: dense reaches $\mathrm{Hit@10}=0.6095$,
trust-weighted fixed top-10 IntentRoute reaches $0.6300$, and a five-fold
budgeted evaluation saves 8.34% final-context tokens with a -0.21 percentage
point mean hit delta versus dense. The strict 1pp non-inferiority rule remains
unmet on CovidQA-RAG, so this row supports transfer of the quality-efficiency
trade-off rather than a guaranteed non-inferior result. On the Banking77
intent-routing proxy, the corresponding dense and trust-weighted scores are
$0.9805$ and $0.9844$, and selected-cluster hit reaches $0.9983$. The
near-ceiling PubMedQA and Banking77 final scores limit claims about aggregate
improvement, but the route diagnostics support feedback adaptation beyond the
LoTTE task format.

The two boundary datasets explain why benchmark construction matters. eManual
contains 18,812 chunks but only 1,729 unique text strings: dense
$\mathrm{Hit@10}$ increases from $0.3231$ under strict chunk identity to
$0.5615$ under text-equivalent matching and $0.8615$ after corpus
deduplication. On the GT-anchored CUAD sample, dense reaches $0.0759$ and the
trust-weighted smoke run reaches $0.0886$; sparse evidence anchors prevent this
sample from serving as full-corpus positive evidence. Supplementary Sections
S4 and S8 retain the complete tables. These datasets support mechanism,
transfer, and boundary analysis rather than replacing the LoTTE token-saving
headline or establishing universal dense-retrieval dominance.

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
IntentRoute range of 0.8657-0.8777. Supplementary Section S10 contains all compressor and
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
$p=0.0290$); E5 remains non-significant. Supplementary Section S6 reports judge coverage,
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
The preregistered recreation/search and writing/search expansion sharpens this
boundary: both domains retain cluster-local route signal, but only
writing/search supplies a useful 10.09% cross-fitted saving point with a
slightly positive mean Hit change, and even that point passes the strict
seed-level guardrail in only 2/3 seeds. Recreation/search is a weaker boundary,
and trust-weighted calibration safely falls back to Dense in both domains.

The broader nine-setting evaluation keeps external-validity, mechanism, and
benchmark-boundary evidence separate. Recreation/search and writing/search map
heterogeneity under the complete 100k common protocol. PubMedQA shows that
trust-weighted route adaptation is observable in biomedical evidence retrieval
near a dense ceiling, while CovidQA-RAG provides a more discriminative
biomedical transfer row with measurable final-context savings and a small mean
hit loss under the strict cross-fitted budget. Banking77 shows analogous
feedback behavior in an intent-routing proxy. eManual and CUAD expose how
duplicated evidence, strict chunk identifiers, and sparse ground-truth anchors
can dominate measured retrieval quality. These results do not form a pooled
cross-dataset score or nine equivalent replications. Instead, they separate the
controller's full-stack LoTTE evidence from transfer, mechanism, and
benchmark-boundary evidence.

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

The additional 100k domains make the same distinction operational. The
no-feedback writing/search route admits compression in all folds, whereas
recreation/search does so in four and the trust-weighted controller does so in
none. A Dense fallback is therefore a valid calibrated outcome, not a missing
result; route signal and a safe budget frontier must be established separately
for each domain.

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
estimation, not as the sole source of final fused quality. The
simulated-feedback and deployment boundaries are consolidated in Section 7.1.

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
$\mathrm{NearestClusterHit@3}$ remains high across LoTTE technology/search scales, and local
geometry provides useful routing information. The added recreation/search and
writing/search domains likewise reach 0.8366 and 0.8655, respectively. However,
context retention and calibrated savings vary by scale and domain, and geometry
alone is not a complete retrieval model. If a cluster route prunes too early,
correct evidence can be lost.

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

The formal frozen-policy audit reinforces this boundary. After route state is
trained on disjoint history folds and then frozen, learned full routing does not
outperform matched static-nearest or cold no-feedback full routing on unseen
queries in either tested LoTTE domain. Learned gating is significantly below
Dense in all three seeds of both domains. Feedback is therefore supported as a
controlled repeated-interaction and recovery mechanism, not as a demonstrated
universal first-pass gain on arbitrary unseen queries.

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

The preregistered 100k domain expansion confirms that this is not only a scale
effect. Writing/search yields a useful no-feedback frontier at 10.09% mean
saving and +0.12pp mean Hit change, but strict non-inferiority holds in only
2/3 seeds. Recreation/search yields 5.42% saving at -0.76pp and 0/3 strict
non-inferiority seeds. Trust-weighted calibration falls back to Dense in every
fold in both domains. These rows support domain-dependent calibrated operating
points, not a universal quality-preserving token-saving guarantee.

The route stability checks use the fixed seeds 13, 17, and 19 as engineering
replicates; query-level paired tests provide the main inferential evidence. The
400k seed-level saving interval remains wider than at other scales, and the
cross-fitted follow-up establishes strict non-inferiority in 0/3 seeds.

The fixed `1pp` threshold is a conservative engineering guardrail for the
headline hit event, not a formal equivalence theorem: it represents only about
four original-split or six out-of-fold query-hit outcomes. The paper also
contains multiple scales, controls, backbones, datasets, and judges. These
analyses map heterogeneity and mechanism boundaries rather than form an IID
replication pool, so secondary $p$-values are not used to support a global
superiority conclusion or mechanically aggregated into one claim.

## 7.6 Geometry and Fixed-Arm Scope

The piecewise relevance-manifold framing is supported by diagnostics such as
$\mathrm{NearestClusterHit@3}$, PCA spectrum, and context retention. These
diagnostics do not prove a mathematical manifold theorem. They show that local
geometry is informative for routing across the tested LoTTE domains, while
dense retrieval remains necessary. In particular, the strong cluster-local
signals in recreation/search and writing/search coexist with different budget
outcomes, so geometry is not a direct compression-safety predictor.

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and
the experiments need reproducible, scalable arms. This is not a claim that
KMeans is the best clustering method for all RAG systems. HDBSCAN or
graph-based clusters may perform better in some deployments, but dynamic arm
counts complicate the current LinUCB setup. The tested $K=8$-$128$ grid shows
stable full multi-route quality but sensitive gated routing, so $K=32$ remains
an engineering operating point rather than an optimum.

## 7.7 Limited Encoder and Domain Coverage

The paper evaluates matched MiniLM, BGE-base, and E5-base dense/IntentRoute
backbones, plus a QA-tuned MiniLM-family check and a cross-encoder reranker.
This establishes backbone-level robustness within the tested LoTTE setting,
but it does not cover domain-specific encoders, late-interaction models, or
proprietary embedding systems. The above-dense quality-first point is currently
demonstrated for BGE only; E5 supports a near-dense token-saving point instead.

The study spans nine dataset settings, but only LoTTE technology/search
receives the complete multi-scale, matched-baseline, calibration/test, and
downstream-generation protocol. LoTTE science/search strengthens cross-domain
and scale validity; recreation/search and writing/search add complete 100k
common-protocol retrieval and budget rows but no multi-scale or generated-answer
evaluation. PubMedQA and CovidQA-RAG test biomedical evidence-retrieval transfer
under different dense ceilings; Banking77 tests feedback adaptation as an
intent-routing proxy; and eManual and CUAD expose benchmark boundaries. This
breadth should not be interpreted as nine independent full-stack replications.
More complete repeated evaluations on additional vertical corpora remain
necessary.

## 7.8 Future Work

The safe-compression attribution boundary and class imbalance are analyzed in
Section 6.5. They motivate, but do not currently validate, a learned per-query
confidence-to-token-ratio predictor.

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

The evaluation spans nine dataset settings with different evidentiary roles.
The main full-stack evidence comes from LoTTE technology/search at 100k to 638k
corpus chunks. Under calibration/test budget selection, calibration-eligible operating
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
compression-calibration boundary. A preregistered recreation/search and
writing/search expansion finds usable cluster-local route signal in both
domains but different calibrated frontiers: writing/search saves 10.09% tokens
with a +0.12pp mean Hit change and 2/3 strict non-inferiority seeds, whereas
recreation/search saves 5.42% at -0.76pp and 0/3 strict seeds; trust-weighted
calibration falls back to Dense in both. This supports domain-dependent
external validity without turning geometry into a direct compression guarantee
or claiming universal strict non-inferiority. Hard-case recovery experiments further show
that simulated feedback can repair part of the tail failures caused by
aggressive context compression. A formal frozen-policy audit separates this
result from first-pass unseen-query transfer: learned full routing remains near
Dense but does not exceed matched static or cold full controls, while learned
gating is unsafe in the two tested domains. Feedback is consequently interpreted
as controlled repeated-query adaptation and conditional recovery.
PubMedQA and CovidQA-RAG extend the evidence-retrieval transfer checks to
biomedical QA under near-ceiling and more discriminative dense baselines,
respectively; Banking77 extends the feedback-adaptation check to
banking-intent routing; and eManual and CUAD expose duplicate-text and
sparse-ground-truth limits. These supporting settings broaden the transfer,
mechanism, and boundary evidence without being treated as equivalent
replications of the LoTTE quality-efficiency frontier.

Strong post-retrieval baselines refine rather than weaken the conclusion.
Sentence-level MMR and Selective Context-lite are effective shared downstream
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
