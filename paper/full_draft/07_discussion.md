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
