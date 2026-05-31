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
