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
controller. Its central operation is to convert confidence over a multi-route
evidence pool into the final amount of context sent to the generator. In our
retrieval-augmented QA implementation, the route surface includes dense
retrieval, BM25 lexical recall, and cluster-local retrieval. A bounded
piecewise relevance-manifold hypothesis motivates the local route construction:
fixed KMeans/MiniBatchKMeans regions form reproducible arms rather than a claim
that geometry alone defines relevance. Trust-weighted LinUCB updates arm values
from controlled feedback, turning user feedback into an adaptive estimate of
which local routes can be trusted. Low route confidence keeps dense retrieval
as a recall floor; high confidence allows a calibrated final context budget.
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
Dense and BM25 rescue paths protect final recall. The budget policy consumes
these signals and chooses the final context size. A late reranker can improve
candidate ordering, while a sentence or prompt compressor can remove redundant
text after evidence selection. IntentRoute occupies the upstream
route-confidence-to-budget layer and can be composed with those downstream
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
calibration eligibility gate. Across these scales, IntentRoute avoids the
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
and finds positive context-token savings without a statistically detectable
correctness change. LoTTE science/search and feedback-driven hard-case recovery
provide cross-domain and adaptive-recovery evidence, with domain calibration
and simulated-feedback caveats.

The contributions of this paper are:

1. We formulate retrieval-backed evidence selection as a
   route-confidence-to-budget problem and introduce a calibrated policy that
   converts multi-route confidence into final evidence-context size while
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
5. We add a 300-query answer-level evaluation, cross-domain LoTTE replication,
   controlled feedback recovery, and explicit limitation cases to bound the
   supported quality-cost claim.

The resulting claim is intentionally bounded. IntentRoute is not presented as
a universal replacement for dense retrieval, a proof of a relevance manifold,
or a statistically superior answer generator. It is a feedback-driven
controller that uses local geometry to structure routes, trust-weighted LinUCB
to adapt route confidence, and dense retrieval as a recall floor before mapping
confidence to a final context budget. Reranking and context compression remain
compatible downstream layers rather than competing explanations.
