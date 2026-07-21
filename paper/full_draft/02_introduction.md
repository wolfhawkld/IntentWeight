# 1. Introduction

Knowledge-augmented agents condition language-model responses on external
evidence, commonly supplied by retrieval-augmented generation (RAG)
[@lewis2020rag]. The broader
control problem is deciding which structured domain knowledge enters a limited
context. Missing evidence is difficult for the generator to recover, whereas
excess evidence increases latency, context cost, and distracting noise.
Practical systems must therefore decide which route to trust and how much
evidence is safe.

Dense retrieval is a strong baseline because it recovers semantically related
passages despite surface-form mismatch [@karpukhin2020dpr]. As a fixed route,
however, it does not
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
prompt compressors remain composable downstream components
[@hwang2024dslr; @pan2024llmlingua2].

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
