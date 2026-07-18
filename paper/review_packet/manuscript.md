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
domain and scale transfer; prospectively specified recreation/search and writing/search
100k studies test domain heterogeneity; and biomedical, banking, manual, and
legal settings provide transfer, mechanism, and boundary checks. At
calibration-eligible technology/search points, IntentRoute reduces final
evidence-context tokens by 6-18% while preserving near-dense query-level
$\mathrm{Hit@10}$ and avoiding the larger losses of dense-only adaptive
truncation. On 300 frozen queries, matched variants reduce
context by 6-12% with no statistically detectable correctness difference
across three judges, although faithfulness is not uniformly preserved. In the
prospective expansion, no-feedback routes save 10.09% with a +0.12pp mean Hit
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

Knowledge-augmented agents condition language-model responses on external
evidence, commonly supplied by retrieval-augmented generation (RAG). The broader
control problem is deciding which structured domain knowledge enters a limited
context. Missing evidence is difficult for the generator to recover, whereas
excess evidence increases latency, context cost, and distracting noise.
Practical systems must therefore decide which route to trust and how much
evidence is safe.

Dense retrieval is a strong baseline because it recovers semantically related
passages despite surface-form mismatch. As a fixed route, however, it does not
decide when lexical matching or local cluster structure is informative, when
global dense retrieval should rescue a route, or when the final context can be
compacted. These decisions matter in large, terminology-heavy vertical corpora
shaped by recurring workflows, entities, and user intents.

We study a bounded hypothesis: vertical-domain evidence often has piecewise
relevance structure, forming local regions induced by concepts, lexical anchors,
workflows, and user behavior rather than being uniformly distributed in
embedding space. Dense neighborhood search in one representation may miss
lexical constraints, cluster-level routing, or user-specific relevance. Geometry
alone is also insufficient: early cluster pruning can miss correct evidence, so
dense retrieval remains a recall floor.

We propose IntentRoute, a feedback-adaptive route-confidence and context-budget
controller. It gates a multi-route evidence pool and then applies a calibrated
final-context budget. In our retrieval-augmented QA implementation, dense, BM25,
and cluster-local retrieval form the route surface. The bounded piecewise
relevance-manifold hypothesis motivates fixed KMeans/MiniBatchKMeans regions as
reproducible arms, not as geometry-defined relevance. Trust-weighted LinUCB
updates arm values from controlled feedback; low route confidence retains dense
retrieval as a recall floor, and the final budget is calibrated separately on
the routed rankings. IntentRoute denotes control conditioned on query intent,
local structure, and feedback state, not a separate intent-classification stage.

Although the control problem also appears in memory-, graph-, and tree-backed
agents, our empirical claims remain tied to the evaluated retrieval-augmented QA
setting.

The design separates route construction, confidence estimation, and final
context control: geometry supplies a local route prior, LinUCB feedback adapts
route confidence over repeated interactions, Dense/BM25 protect recall, and
calibration chooses final-budget parameters. Late rerankers and sentence or
prompt compressors remain composable downstream components.

We likewise separate source candidates, global-dense invocation rate, and final
retrieved context tokens. The efficiency claim uses only the last: candidate
reductions are retrieval diagnostics unless the generator input also shrinks.
At a declared provider input-token price, the measured percentage saving applies
to the input-price component for that evidence, not total serving cost, latency,
memory, energy, output tokens, or retrieval overhead.

We evaluate nine dataset settings with tiered roles. LoTTE technology/search
anchors the 100k--638k full-stack quality-efficiency claim; science/search tests
cross-domain and scale transfer; and prospectively specified recreation/search
and writing/search 100k studies test frontier heterogeneity under the same
protocol. PubMedQA and CovidQA-RAG provide near-ceiling and discriminative
biomedical transfer checks, Banking77 tests banking-intent feedback adaptation,
and eManual and CUAD expose duplicate-text, strict chunk-identity, and
sparse-ground-truth boundaries. Their tasks, labels, and evidence strengths are
not pooled as interchangeable replications.

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

We also test stronger alternatives and component controls. Matched BGE-base and
E5-base comparisons retain the pattern beyond MiniLM, while a BGE quality-first
policy trades some saving for higher hit. Random-route, static-geometry,
no-feedback, and arm-count ablations show that geometry and feedback affect
route reward and cluster hit, although Dense/BM25 rescue can mask weak routes in
fused $\mathrm{Hit@10}$. Sentence-MMR establishes a shared downstream
compression baseline; cross-encoder reranking improves full-context
support but can select longer contexts. Across 300 queries and three LLM judges,
matched BGE, E5, and SentMMR pipelines show no statistically detectable
correctness difference, with method-dependent faithfulness. Cross-domain,
biomedical, intent-routing, recovery, and boundary checks broaden the evidence
without extending the LoTTE token-saving headline to incomparable tasks.

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
   prospectively specified recreation/search and writing/search 100k external-validity
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

The claim is bounded: IntentRoute is neither a universal dense replacement, a
manifold theorem, nor a statistically superior answer generator. It uses local
geometry to structure routes, trust-weighted LinUCB to adapt confidence, and
dense retrieval as a recall floor before a separately calibrated context budget;
reranking and compression remain compatible downstream layers.

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

Work published in 2026 further separates adjacent routing objectives. R3AG
learns query-specific retriever preferences from retrieval quality and
generation utility, while QuDAR assigns query-specific weights across
sparse/dense retrievers and original/expanded queries
[@zhao2026r3ag; @kim2026qudar]. RouteRAG instead learns multi-turn text/graph
retrieval and generation through an end-to-end reinforcement-learning policy
[@guo2026routerag]. These systems adapt a retriever, source, or reasoning
action. IntentRoute does not claim novelty for adaptive RAG itself: it retains
global Dense/BM25 rescue, defines corpus-local arms from geometry, studies
controlled repeated-feedback updates, and calibrates the final evidence budget
independently so route, fusion, and context effects remain attributable.

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

Budget-Aware Routing for Long Clinical Text directly studies subset selection
under strict token budgets, using relevance, coverage, and diversity over units
of long clinical documents [@qureshi2026budget]. It is closest to IntentRoute at
the budget-control layer, but addresses within-document unit selection rather
than geometry-defined multi-route retrieval with repeated feedback and a global
Dense/BM25 rescue surface. Its domain-specific budget findings reinforce the
need to report calibrated operating points rather than assume one universal
compression policy.

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

## 2.6 Relevance Feedback and Trust-Weighted Route Adaptation

User feedback can improve retrieval systems, but real feedback is delayed,
biased, sparse, and user-dependent. Earlier work on clickthrough and implicit
feedback shows that user behavior can train ranking systems, while also
requiring care because clicks and query reformulations are biased signals
[@joachims2002clickthrough; @radlinski2005querychains]. This retrieval setting
maps directly to contextual-bandit updates: an observed evidence outcome can
adjust later route preferences, while its reliability determines update
strength.

The current experiments use ground-truth-derived controlled feedback to isolate
that route-state mechanism under oracle, noisy, trust-weighted, and no-feedback
conditions. Ground truth is revealed only after the current ranking is scored,
so it cannot improve that query. Trust weighting models unequal signal
reliability; it is not evidence that production clicks, corrections, or user
ratings have already been collected or debiased.

---

# 3. Method

## 3.1 Problem Formulation

In the retrieval-backed implementation evaluated here, let an evidence corpus
be a set of chunks $D = \{d_i\}_{i=1}^{N}$ and a query stream
$Q = \{q_t\}_{t=1}^{T}$. For each query $q_t$, a retrieval system returns an
ordered context $C_t = [d_{t,1}, \ldots, d_{t,k}]$ that will be passed to a
downstream generator. The objective is to preserve retrieval quality while
controlling route use and the final evidence-input context size.

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
policy-derived confidence and a selected-arm centroid mismatch safeguard as
separate route-gating signals. With normalized query context $x_t$ and selected
arm set $\mathcal{A}_t$, the latter is
$1-\max_{a\in\mathcal{A}_t}\cos(x_t,\mu_a)$. It measures mismatch to the chosen
centroids; it is not temporal or distribution drift. These signals determine
whether the system retains the full dense/BM25/cluster fusion surface or permits
a lighter route with a Dense floor. Dense and BM25 rankings are constructed and
fused after the route decision; their score concentration, lexical strength,
and route overlap are not inputs to the tested LinUCB vector. Neither signal
sets the final token ratio, which remains a separately calibrated action.

## 3.6 Trust-Weighted Route-State Updates

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
attribution mode in Supplementary Table S22.

This distinction matters because final fused reward measures the system outcome,
while cluster-only reward isolates the cluster-route component. Neither mode
allows Dense/BM25 rescue to be omitted from the interpretation of final quality.

## 3.8 Prequential Adaptation Protocol

For each query $q_t$, the policy state is frozen before retrieval. The system
ranks candidates and evaluates the resulting evidence before converting the
observed ground-truth outcome into simulated feedback. The update can therefore
change only the route state used by $q_{t+1}$ and later interactions:

$$
\text{rank}(q_t;\theta_t)\rightarrow o_t\rightarrow
\theta_{t+1}=U(\theta_t,x_t,o_t,w_t).
$$

The current query never sees its own label before ranking. Experimental Setup
specifies the oracle, noisy, trust-weighted, repeated-interaction, and frozen
unseen-query controls used to test this order.

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

1. If route confidence is low or selected-arm centroid mismatch is high, keep
   dense fallback and the normal top-10 context.
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

For the conservative `confidence_topk` baseline only, centroid mismatch triggers
fallback in roughly 1--2% of interactions under the configured threshold, so
context-size decisions are primarily confidence-conditioned. The fixed-pool
factorial audit does not show that this confidence predicts compression safety
better than matched controls; the baseline is an empirical operating point
rather than a validated causal mechanism.

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
use other epoch counts and attribution modes; Supplementary Table S22 records
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
- **LoTTE recreation/search and writing/search** are prospectively specified 100k
  external-validity tests with 924 and 1,071 positive-qrel queries,
  respectively. Both use the full common protocol and remain in the analysis
  after the prospectively specified lexicality ordering is contradicted by the measured
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
- Cross-encoder reranking over dense top-50 candidates.
- Static geometry controls such as nearest-cluster routing.
- Naive controls such as random or epsilon-greedy arm selection.
- No-feedback and uniform-random route controls.
- Arm-count sensitivity over $K \in \{8,16,32,64,128\}$.

Dense-only retrieval is the primary quality baseline and remains a required
recall floor in the proposed method. Sentence-MMR is the matched downstream
compression baseline, while the cross-encoder tests whether a heavier late
ranking layer can select a smaller context more simply. These components are
not mutually exclusive alternatives to IntentRoute; they occupy different
stages in the retrieval-to-context pipeline.

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

Following the update order in Section 3.8, ground truth becomes a controlled
feedback proxy only after the current result is scored. Oracle feedback is a
learning upper bound; equal-noisy and trust-weighted modes model imperfect
signals with different reliability; no-feedback, static-nearest, and random-arm
controls separate adaptation from fixed or uninformative routing. Trust changes
update strength, never current-query label availability. This design tests
whether route state responds coherently to a declared signal, not whether
production feedback has already been collected or debiased.

Some experiments use multiple prequential epochs over the same query stream to
simulate repeated interaction. Every epoch preserves rank-then-update order;
these are route-adaptation studies, not IID held-out generalization.

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
budget. The cross-encoder baseline reranks dense top-50 candidates with
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

The prospectively specified domain expansion applies the normalized five-fold protocol to all
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

| Scale | Frozen context action | Calibration status | IntentRoute hit delta | NI seeds | IntentRoute token saving | Dense-trunc hit delta | Dense-trunc token saving |
|---|---|---:|---:|---:|---:|---:|---:|
| 100k | 95% budget; minimum 4 chunks | Eligible | +0.00 pp | 0/3 | 6.18% | -1.44 pp | 13.83% |
| 200k | 85% budget; minimum 4 chunks | Eligible | +1.20 pp | 1/3 | 16.00% | -2.40 pp | 21.95% |
| 400k | 98% budget; minimum 4 chunks | Diagnostic only | +2.32 pp | 3/3 | 6.57% | -0.24 pp | 11.44% |
| 638k | 85% budget; minimum 4 chunks | Eligible | -0.08 pp | 0/3 | 17.53% | -3.84 pp | 21.90% |

The calibration-eligible 100k, 200k, and 638k operating points save 6-18%
final context tokens. The 400k row is retained as a diagnostic point because
no candidate met the zero-observed-hit-drop calibration gate, even though its
frozen-test result is positive. Dense-only adaptive truncation saves more
tokens but loses $\mathrm{Hit@10}$ at every scale. IntentRoute therefore
targets a more quality-preserving bounded frontier rather than maximum
compression.

The artifact identifiers for these four actions are, respectively,
`token_budget_r0.95_m4`, `token_budget_r0.85_m4`,
`token_budget_r0.98_m4`, and `token_budget_r0.85_m4`; the journal-facing labels
state the same ratio and mandatory-prefix parameters directly.

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
strict non-inferiority remains `0/3` seeds. Supplementary Table S12 reports the fold-level
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

Arm-count sensitivity tests whether the fixed $K=32$ choice is a hidden
optimum. Figure 3 combines three evidence layers. Panel A shows that
nearest-cluster hit remains high across the measured technology/search and
science/search scales while context retention and PCA concentration vary.
Panel B shows the large static-geometry advantage over uniform-random arms in
route reward and selected-cluster hit, alongside their much smaller difference
in rescued final fused Hit. Panel C shows that gated Dense use rises from
0.4083 to 0.9502 over $K=8$--$128$, while every gated point loses Hit.

The complete arm-count grid is retained in Supplementary Table S20. Full
multi-route quality remains stable across that grid, so $K=32$ is a reproducible
engineering point governing route granularity, feedback sparsity, and fallback,
not a geometrically privileged optimum. The composite figure supports local
structure as a route-control surface; it does not posit a deterministic
geometry-to-token-saving law.

## 5.5 Cross-Domain, Mechanism, And Boundary Evidence

Table~\ref{tab:4} puts every completed dataset-scale endpoint in one evidence
matrix. The rows remain separate because they differ in query population,
ground-truth semantics, protocol, and evidentiary role; no pooled effect is
computed.

**Table 4. Cross-dataset and cross-domain evidence matrix. Five-fold rows use independently calibrated frozen budgets; the science 20k row is a legacy fixed-split diagnostic. Dashes denote no common final-context endpoint, and no rows are pooled.**

| Dataset | Scale | Dense Hit@10 | IntentRoute Hit@10 | Hit delta | Token saving | Strict NI seeds | Evidentiary role |
|---|---|---:|---:|---:|---:|---:|---|
| LoTTE technology/search | 100k | 0.8674 | 0.8568 | -1.06 pp | 4.16% | 0/3 | Full-stack scale |
| LoTTE technology/search | 200k | 0.7970 | 0.8110 | +1.40 pp | 16.07% | 2/3 | Full-stack scale |
| LoTTE technology/search | 400k | 0.7718 | 0.7718 | +0.00 pp | 14.50% | 0/3 | Split-sensitive scale |
| LoTTE technology/search | 638k | 0.7282 | 0.7310 | +0.28 pp | 15.23% | 0/3 | Full-stack scale |
| LoTTE science/search | 20k/q200 | 0.8929 | 0.9095 | +1.67 pp | 13.80% | 1/3 | Legacy cross-domain diagnostic |
| LoTTE science/search | 100k | 0.8926 | 0.8915 | -0.11 pp | 16.88% | 0/3 | Cross-domain |
| LoTTE science/search | 200k | 0.8574 | 0.8507 | -0.67 pp | 10.75% | 0/3 | Cross-domain scale |
| LoTTE science/search | 400k | 0.8238 | 0.8171 | -0.67 pp | 3.15% | 0/3 | Scale boundary |
| LoTTE recreation/search | 100k | 0.8496 | 0.8420 | -0.76 pp | 5.42% | 0/3 | External-validity boundary |
| LoTTE writing/search | 100k | 0.8739 | 0.8752 | +0.12 pp | 10.09% | 2/3 | External-validity frontier |
| PubMedQA | Native full | 0.9930 | 0.9930 | +0.00 pp | 0.00% | 3/3 | Dense-ceiling transfer |
| CovidQA-RAG | Native full | 0.6112 | 0.6091 | -0.21 pp | 9.00% | 0/3 | Biomedical transfer |
| eManual deduplicated | Native full | 0.8615 | 0.8590 | -0.26 pp | 16.20% | 0/3 | Corrected boundary |
| Banking77 | Native full | 0.9805 | 0.9844 | +0.39 pp | -- | -- | Intent-routing mechanism |
| CUAD GT-anchored | 10k sample | 0.0759 | 0.0886 | +1.27 pp | -- | -- | Sparse-GT boundary |

The common five-fold rows expose domain heterogeneity rather than a universal
no-loss rule. Science/search saving falls from 16.88% at 100k to 3.15% at 400k,
where only one fold compresses. Recreation/search yields 5.42% saving at
-0.76pp, whereas writing/search yields 10.09% at +0.12pp; trust-weighted
calibration selects Dense fallback in every fold of both domains. Their
$\mathrm{NearestClusterHit@3}$ values of 0.8366 and 0.8655 nevertheless show
that useful local-route structure can coexist with different safe budget
frontiers. Supplementary Table S23 retains their complete route and calibration
controls.

PubMedQA is a Dense-ceiling transfer row rather than evidence of additional
compression. CovidQA-RAG and deduplicated eManual provide non-ceiling transfer
and corrected-boundary results, while Banking77 and CUAD have no comparable
final-context endpoint. The latter two therefore support route mechanism or
benchmark-boundary analysis only. Supplementary Sections S4, S8, and S12 retain
the corresponding dataset, seed, and protocol details.

## 5.6 Strong Post-Retrieval Baselines

Dense+Sentence-MMR preserves dense chunk-support
$\mathrm{Hit@10}=0.8705$ while saving 11.4-13.1% selected-sentence tokens.
When the same compressor is applied to both source pools,
IntentRoute+Sentence-MMR reaches 10.1-21.2% total saving because it starts from
a smaller evidence pool. This matched control shows that downstream compression
is complementary rather than unique to IntentRoute; an official LLMLingua-2
comparison remains untested.

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

IntentRoute supports a bounded confidence-gated-route plus calibrated-budget
claim. It gates dense, lexical, and geometry-defined local routes using
trust-weighted adaptive confidence, then applies a separately frozen
final-context policy. On LoTTE technology/search, eligible 100k, 200k, and 638k
points save 6--18% evidence-context tokens while avoiding the larger
$\mathrm{Hit@10}$ losses of dense-only truncation. The original 400k point is
calibration-ineligible despite a positive frozen-test result; a normalized
five-fold audit yields 14.50% mean saving with no mean Hit change, but varying
policies and no strict seed-level non-inferiority. The conservative
confidence-only policy provides a stable 4.7--5.3% saving baseline.

Matched BGE/E5 results extend the quality-cost pattern beyond MiniLM. The
300-query, three-judge evaluation finds positive savings without a statistically
detectable correctness change, but negative BGE/E5 point estimates from stricter
judges and a majority-detected BGE faithfulness decrease preclude uniform
answer-quality non-inferiority. Science/search supports ranking transfer while
requiring domain- and scale-specific budget calibration. Recreation/search and
writing/search retain local route signal, yet only writing/search provides a
useful 10.09% cross-fitted saving point with a slightly positive mean Hit change
and only 2/3 strict non-inferiority seeds; trust-weighted calibration safely falls back to Dense
in both.

The nine settings retain distinct evidentiary roles. PubMedQA shows biomedical
route adaptation near a dense ceiling; CovidQA-RAG adds a discriminative
transfer row with savings and a small mean hit loss; Banking77 supplies an
intent-routing feedback proxy; and eManual/CUAD expose duplicate, identity, and
sparse-label boundaries. They are transfer, mechanism, and boundary evidence,
not a pooled score or nine equivalent full-stack replications.

Dense retrieval remains the primary quality baseline and recall floor;
IntentRoute's contribution is separating adaptive route control, dense rescue,
and calibrated final-context compaction.

## 6.2 Role of Calibrated Context Budgeting

A static dense, BM25, and cluster-local combination can improve coverage yet use
more final-context tokens by surfacing longer or noisier chunks. Savings come
from the calibrated budget after confidence-gated route construction, not from
adding routes alone.

The conservative policy compresses only high-confidence cases to $k=8$ and
keeps mid-confidence cases at $k=10$, producing modest but stable savings. Frozen
calibrated budgets expose a stronger frontier, whereas simply truncating dense
top-$k$ causes visible $\mathrm{Hit@10}$ loss. The conservative result is an
empirical baseline, not a maximum-compression or per-query safety guarantee.

Under the same cross-fitted zero-drop gate, prefix-only Dense selects no
compressed action at any scale, whereas IntentRoute selects one in every 200k,
400k, and 638k fold. This indicates calibration headroom in the routed ranking,
not safety for every route or partition.

At 100k, no-feedback writing/search admits compression in all folds,
recreation/search in four, and the trust-weighted controller in none. Dense
fallback is therefore a valid calibrated outcome: route signal and a safe
budget frontier must be established separately by domain.

## 6.3 Reranking and Final-Context Control

A cross-encoder reranker reorders a candidate pool but neither expands its
recall nor controls LLM input length. On LoTTE technology/search 100k, reranking
dense top-50 improves full top-10 $\mathrm{Hit@10}$ and
$\mathrm{EvidenceRecall@10}$ from 0.8705/0.7081 to 0.8777/0.7332, while selecting
21.9% more evidence-context tokens than dense top-10.

Thus IntentRoute controls the upstream evidence pool and budget, reranking is a
late ranking layer, and SentMMR compresses downstream.
Under IntentRoute's per-query budgets, cross-encoder $\mathrm{Hit@10}$ does not
uniformly dominate calibrated IntentRoute. The components should be evaluated
as a composable pipeline with an explicit quality-cost frontier, not as mutually
exclusive alternatives.

## 6.4 Feedback Updates Route State under Controlled Credit

Dense/BM25 fallback can saturate fused $\mathrm{Hit@10}$, so feedback is clearer
in selected-cluster hit and last-true-reward metrics.

Under controlled simulated feedback, route reward reaches 0.6790, above the
no-feedback/random level near 0.15 but below the 0.8563 static-nearest prior.
Cluster-credit controls show learnable oracle capacity and conditional noisy
gains, but no stable trust-weighted advantage over static geometry. Feedback is
therefore a controlled route-state update, not the sole source of fused quality
or a universal gain (Section 7.1).

The supported ordering is deliberately limited: an observed outcome updates
later LinUCB route state; that state and the geometry-defined arms influence
route selection, confidence, and fallback; an independently calibrated budget
then acts on the fused ranking. Neither feedback nor route confidence directly
sets a per-query compression ratio, so the token-saving frontier belongs to the
complete controller rather than to a single causal arrow.

When aggressive compaction loses evidence, arm-level feedback can repair a
meaningful fraction of affected queries through safer retry or fallback. This
controlled recovery does not justify globally boosting the same arm for future
queries.

A frozen-trajectory counterfactual locates this effect. Frequency-preserving
confidence-tier shuffling lowers Hit@10 by 4.80pp. The original assignment sends
high-confidence queries to a cluster-primary route with source Hit@10 0.924 and
retains fallback for low-confidence queries, whose forced cluster-primary Hit@10
is 0.240. Confidence supports route-shape assignment before, and separately
from, final-context budgeting.

## 6.5 Geometry Is Useful but Not Sufficient

Geometry diagnostics support the piecewise relevance-manifold framing:
$\mathrm{NearestClusterHit@3}$ remains high across technology/search scales and
reaches 0.8366/0.8655 in recreation/search and writing/search. Yet context
retention and calibrated savings vary by scale and domain, and early cluster
pruning can lose evidence.

Geometry is therefore one controller signal alongside dense fallback, BM25
lexical anchors, and LinUCB confidence adaptation.

Static geometry strongly improves route reward and cluster hit over random
routing, while Dense/BM25 rescue protects fused hit in both. Mixed small-sample
correlations with final token-quality gain confirm that geometry guides route
construction but does not determine the calibrated controller's outcome.

A factorial audit fixes dense top-10, split, budget grid, and seeds while
crossing geometry/random partitions with feedback/no feedback. Geometry with
feedback does not beat random-partition feedback in failure discrimination
(mean AUROC 0.434 versus 0.573); near 10% saving, their Hit@10 differs by only
+0.08pp and every seed-level paired bootstrap interval includes zero. Because
97.8% of actions are safe, this is boundary evidence, not inverse prediction;
the 6--18% frontier cannot be attributed directly to per-query confidence
precision.

The replay also finds mean Spearman $-0.056$ between confidence and oracle
safe-token headroom, with all seed intervals including zero; dynamic routing has
fewer relevant top-10 chunks than fixed fusion (2.121 versus 2.315). Confidence
therefore assigns route shapes without the severe loss of shuffled or
unconditional cluster-primary routing, rather than creating redundancy that
directly predicts safe compaction.

## 6.6 Evidence Completeness Versus Usable Evidence

Query-level $\mathrm{Hit@10}$ asks whether the final context contains any
relevant chunk; $\mathrm{EvidenceRecall@10}$ measures coverage of all GT chunks.
Compaction can preserve the former while reducing the latter. IntentRoute thus
targets usable, not exhaustive, evidence; legal, medical, or compliance tasks
requiring completeness should use conservative budgets or disable compaction.

## 6.7 Production Interpretation

The measured 6--18% reduction lowers generation-stage evidence input; at a
declared provider input-token price, the same percentage applies only to that
price component. Total serving cost also includes prompts, outputs, model
execution, retrieval, routing, caching, and infrastructure; latency, memory, and
energy were not measured. The 4.7--5.3% confidence-only policy is a stable
input baseline, while calibrated budgets expose the stronger bounded frontier.
Richer post-fusion features may support a future safety estimator, but route
confidence alone is not one here.

The correct deployment interpretation is therefore:

- keep dense retrieval as a recall floor and optionally rerank before final
  context selection;
- use feedback and confidence for route control, while calibrating the final
  context budget separately;
- use negative feedback for safer retry or fallback rather than as a direct
  compression-ratio signal;
- monitor evidence quality and fallback rates, and disable aggressive
  compaction for complete-evidence tasks;
- treat evidence-input saving as a controllable frontier and measure total
  system cost separately.

---

# 7. Limitations and Future Work

## 7.1 Simulated Feedback

The experiments derive simulated feedback from ground truth under controlled
noise and trust. They test policy response to a feedback signal, not behavior
under delayed, biased, adversarial, low-quality, or non-stationary human input.
The GT-derived hard-case experiment is likewise a recovery test after a failed
compacted answer, not first-pass IID improvement. It repairs some cases whose
evidence remains reachable through the candidate pool and arms, without
implying universal recovery.

After training route state on disjoint history folds and freezing it, learned
full routing does not outperform matched static-nearest or cold no-feedback
full routing on unseen queries in either LoTTE domain; learned gating is
significantly below Dense in all three seeds of both. Feedback is therefore a
controlled repeated-interaction and recovery mechanism, not a demonstrated
universal first-pass gain.

## 7.2 Limited Generation Evaluation

Across 300 frozen-test queries, seven methods, 2,100 answers, and 6,265 valid
three-judge ratings, matched BGE, E5, and SentMMR comparisons save context
without a statistically detectable correctness change. However, one model
generates all answers, DeepSeek is also a judge, no human ratings are available,
and only one LoTTE domain is covered. MiniMax-M3 content filtering rejects 35
judgments, which cross-judge analyses exclude rather than impute. Calibration
differs across judges, and majority faithfulness falls for BGE but rises for
SentMMR. The evidence supports bounded correctness robustness, not strict
non-inferiority, uniform faithfulness, answer superiority, or user satisfaction.

## 7.3 Dense Baseline, Evidence Completeness, and Domain Calibration

Dense-only retrieval remains a strong baseline and recall floor, not a route
that IntentRoute universally replaces. Moreover, preserving query-level
$\mathrm{Hit@10}$ does not guarantee coverage of all ground-truth chunks.
Legal review, medical synthesis, and other complete-evidence tasks may require
a conservative policy or no compaction. The supported result is therefore a
calibrated quality-context frontier, not universal Dense replacement or
lossless evidence compression.

LoTTE science/search transfers fixed top-10 ranking gains, but not budget
strength: at 100k, an aggressive budget saves 17--21% while introducing small
frozen-test $\mathrm{Hit@10}$ drops. Budgets require domain- and scale-specific
calibration with dense fallback for low-confidence or high-risk regions.

Across 20 deterministic partitions, selected-policy mean Hit remains within
`1pp` of dense on every 200k/638k test partition, but only 70%/85% of 100k/400k
partitions. Because partitions overlap, they measure sensitivity rather than
independent replication. The original frozen split remains valid, but deployment
should prefer repeated or nested calibration over a universal no-loss inference.

The disjoint five-fold follow-up yields 14.50% mean 400k saving at effectively
zero mean Hit delta, yet fold deltas remain heterogeneous and every fold selects
a different policy. It addresses missing calibration without establishing
split-invariant behavior.

The prospectively specified 100k expansion confirms domain effects. No-feedback
writing/search yields 10.09% saving, +0.12pp mean Hit, and 2/3 strict
non-inferiority seeds; recreation/search yields 5.42%, -0.76pp, and 0/3.
Trust-weighted calibration falls back to Dense in every fold of both. These are
domain-specific operating points, not a universal quality-preserving token-saving guarantee.

Seeds 13/17/19 are engineering replicates; query-level paired tests provide the
main inference. The 400k saving interval remains wider than at other scales, and
cross-fitting establishes strict non-inferiority in 0/3 seeds.

The fixed `1pp` threshold is an engineering guardrail, not an equivalence
theorem: it represents about four original-split or six out-of-fold hit events.
Scales, controls, backbones, datasets, and judges map heterogeneous mechanisms
rather than form an IID replication pool, so secondary $p$-values are neither
aggregated nor used for global superiority.

## 7.4 Geometry and Fixed-Arm Scope

Nearest-cluster hit, PCA spectrum, and context retention support informative
local routing geometry, not a manifold theorem. Dense retrieval remains
necessary, and strong cluster-local signals in recreation/search and
writing/search coexist with different budget outcomes; geometry is not a direct
compression-safety predictor.

KMeans/MiniBatchKMeans supplies the fixed, reproducible, scalable arm space
required by the tested LinUCB setup, not a universally optimal clustering
method. HDBSCAN or graph clusters may suit deployments but introduce dynamic
arm management. Across $K=8$--$128$, full multi-route quality is stable and
gating is sensitive, making $K=32$ an engineering point rather than an optimum.

## 7.5 Limited Baseline, Encoder, and Domain Coverage

Matched MiniLM, BGE-base, and E5-base backbones and a cross-encoder support
robustness within LoTTE, but exclude domain-specific, late-interaction, and
proprietary encoders. Only BGE has an above-dense quality-first point; E5
supplies a near-dense saving point. Sentence-MMR is the shared downstream
compressor; the official open-source LLMLingua-2 compressor has not been run,
so the paper does not claim parity with learned token-level prompt compression.

Of nine settings, only LoTTE technology/search receives the complete
multi-scale, matched-baseline, calibration/test, and generation protocol.
Science/search adds domain and scale transfer; recreation/search and
writing/search add common-protocol 100k retrieval/budget rows without multi-scale
or answer evaluation; biomedical datasets, Banking77, eManual, and CUAD test
transfer, mechanism, or boundaries. They are not nine independent full-stack
replications, and more repeated vertical-corpus evaluations remain necessary.

## 7.6 Future Work

The attribution boundary and class imbalance in Section 6.5 motivate, but do
not validate, a learned per-query confidence-to-token-ratio predictor.

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- multi-model and human-rated answer-quality and citation-faithfulness studies;
- stronger dense encoders, rerankers, and late-interaction retrieval models;
- matched Dense/IntentRoute evaluation with official LLMLingua-2 compression;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- repeated evaluations on additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable;
- recovery policies evaluated with real delayed feedback rather than
  GT-derived same-query retry.

---

# 8. Conclusion

This paper presents IntentRoute, a feedback-adaptive route controller motivated
by local relevance structure. Geometry defines reproducible cluster-local
routes, trust-weighted LinUCB updates route state under controlled feedback,
Dense and BM25 provide rescue paths, and an independent calibration policy sets
the final evidence-context budget.

The evaluation spans nine dataset settings across eight domain areas, with
distinct full-stack, transfer, mechanism, and benchmark-boundary roles.

The main full-stack evaluation covers LoTTE technology/search from 100k to 638k
chunks. Calibration-eligible 100k, 200k, and 638k policies reduce final
evidence-input tokens by 6-18% while avoiding the larger $\mathrm{Hit@10}$
losses of Dense-only adaptive truncation. The normalized 400k follow-up yields
14.50% mean saving with no mean Hit change, but its selected policies remain
unstable and strict seed-level non-inferiority is not established. Matched BGE
and E5 comparisons retain near-Dense quality at about 12% saving, and the BGE
quality-first point demonstrates frontier tunability. On 300 frozen queries,
three LLM judges find 6-12% matched context savings without a statistically
detectable correctness difference, while faithfulness remains method-dependent.

Cross-domain results define the boundary rather than a universal guarantee.
Science/search shows that route signal can transfer while safe budget strength
changes with domain and scale. In the prospectively specified 100k expansion,
writing/search saves 10.09% at a +0.12pp mean Hit change and 2/3 strict seeds;
recreation/search saves 5.42% at -0.76pp and 0/3 strict seeds; trust-weighted
calibration falls back to Dense in both. Biomedical, banking, manual, and legal
settings provide transfer, mechanism, and benchmark-boundary checks without
being pooled as equivalent replications.

The controls separate the source of these outcomes. Geometry improves local
route metrics over random routing but does not directly predict compression
safety. Controlled feedback updates route state and can repair some same-query
tail failures, yet it does not beat matched static or cold full routing on the
formal frozen unseen-query audit. Sentence-MMR remains an effective shared
downstream compressor, while cross-encoder reranking can improve
evidence support but may increase context length. Route control, rescue,
reranking, compression, and final-budget calibration are therefore composable
system functions.

IntentRoute is not a universal Dense replacement or a theorem-level manifold
result. Its contribution is a bounded, auditable quality-context controller:
local geometry structures routes, controlled feedback adapts route state,
Dense remains the recall floor, and independent calibration trades compact
evidence input against retrieval risk. Total serving cost and real-user
feedback effectiveness remain deployment questions beyond the measured claim.
