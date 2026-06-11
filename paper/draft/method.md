# Method Draft

Updated: 2026-06-11

## Problem Formulation

Let a RAG corpus be a set of chunks `D = {d_i}` and a query stream be
`Q = {q_t}`. A retrieval system returns an ordered context
`C_t = [d_1, ..., d_k]` for each query. The objective is to maximize retrieval
quality while controlling retrieval cost and final context cost.

IntentWeight treats retrieval as a route-control problem. For each query, the
system chooses how much to rely on global dense retrieval, lexical BM25 recall,
and cluster-local retrieval. The final response generator is outside the current
experiment scope; the paper evaluates retrieval quality and the token count of
the retrieved context that would be sent to the generator.

## Piecewise Relevance-Manifold Assumption

The method is motivated by a bounded assumption:

> In vertical-domain RAG, query-document relevance often follows a piecewise
> local structure induced by domain terminology, semantic neighborhoods,
> document organization, and user intent.

This does not mean that the corpus geometry is sufficient by itself. Instead,
IntentWeight uses geometry as one routing signal among several. Dense retrieval
remains a global recall floor, BM25 provides lexical anchors, and cluster-local
retrieval provides local evidence patches.

## Multi-Route Retrieval Surface

IntentWeight uses three retrieval routes:

1. **Dense route.** Global dense retrieval over the selected corpus using cosine
   similarity in embedding space.
2. **BM25 route.** Global lexical retrieval over the selected corpus, used as an
   exact-match and terminology-sensitive recall path.
3. **Cluster-local route.** Dense retrieval restricted to LinUCB-selected
   cluster arms.

The routes are fused by a weighted ranking strategy in the retrieval layer. The
system can run in a full multi-route mode, a gated cost-aware mode, or a final
context compaction mode.

## Routing Arm Construction

Corpus chunk embeddings are clustered with KMeans or MiniBatchKMeans. This is a
deliberate experimental choice:

- LinUCB requires a fixed number of arms.
- Fixed arms improve reproducibility across seeds and scales.
- The same arm count is used across LoTTE scales to keep the LinUCB state space
  comparable, even though larger corpora therefore contain more chunks per arm.
- KMeans is fast enough for large-scale LoTTE runs.

The paper should not claim that KMeans is the best clustering algorithm for
retrieval. It is used because it gives a stable arm space for contextual bandit
experiments.

Each cluster arm represents a local region of the retrieval surface. The
cluster route searches inside selected arms, while dense and BM25 routes can
rescue cases where the cluster route misses relevant evidence.

## LinUCB Route Policy

For each query `q_t`, IntentWeight computes a context feature vector `x_t`.
Features include query embedding projections, route confidence signals, and
local geometry signals. For each arm `a`, LinUCB maintains a linear value model:

```text
theta_a = A_a^{-1} b_a
score(q_t, a) = theta_a^T x_t + alpha * sqrt(x_t^T A_a^{-1} x_t)
```

Here `alpha` controls the exploration-exploitation balance: larger values give
more weight to arms whose value estimate is uncertain and encourage exploration
of under-sampled local regions.

The policy selects the top candidate arms by score. The selected arms define the
cluster-local retrieval path and also provide confidence signals for later
context compaction.

The evaluation uses a no-leakage prequential protocol: each query is ranked and
evaluated before the simulated feedback for that query updates the policy. The
feedback for `q_t` can only affect later queries through the next policy state;
it cannot change the ranking already produced for `q_t`. This should be
described as simulated test-time adaptation, not as offline IID held-out
generalization.

The main repeated-feedback experiments use multiple prequential epochs over the
same query stream to simulate repeated interactions. Each pass still preserves
the same ordering discipline: the current query is ranked and evaluated before
its feedback updates later policy state. The multi-epoch result should therefore
be interpreted as controlled repeated-interaction adaptation, not as a
single-pass held-out generalization score.

## Trust-Weighted Feedback

IntentWeight models feedback as a noisy signal rather than a perfect oracle. In
the trust-weighted mode, each simulated user feedback event is assigned a trust
weight. Higher-trust feedback contributes more to the arm update and local
feedback memory. Lower-trust feedback has a weaker effect.

Conceptually:

```text
reward_t = quality_signal_t - cost_penalty_t
weighted_reward_t = trust_t * reward_t
A_a <- A_a + trust_t * x_t x_t^T
b_a <- b_a + weighted_reward_t * x_t
```

The experiments do not claim that real human feedback was collected. They show
that under controlled simulated feedback, the route policy can self-improve.
The strongest feedback evidence is visible in policy metrics such as last true
reward and selected-cluster hit rate.

## Route-Level Credit Assignment

Early experiments used final fused retrieval success as the reward signal. This
can over-credit the selected cluster arm when dense or BM25 rescue the final
ranking. Task25 introduced a stricter `cluster_only` reward attribution mode:
the LinUCB arm is updated using the quality of its own cluster-local route.

This distinction is important for the paper. The final fused ranking measures
the system outcome, while cluster-only reward measures whether LinUCB is
learning a better route.

## Confidence-Based Final Context Compaction

Task28 showed that reducing source candidates does not automatically reduce
final context tokens. IntentWeight therefore adds an explicit final context
policy.

The conservative `confidence_topk` policy works as follows:

1. If route confidence is low or semantic drift is high, keep dense fallback and
   the normal top-k context.
2. If LinUCB confidence is high, reduce final context size from the default
   top-10 to `k=8`.
3. If confidence is mid-level, keep `k=10` as a safety tier rather than calling
   it true compression.
4. Report the actual retrieved context token count, not only candidate counts.

For Task29-C, the effective compaction rate is therefore the high-confidence
compression rate, not the broader rate of queries that enter a non-fallback
route. Hybrid-lite can reduce dense influence in fusion while retaining dense
candidates as a safety net; it should not be described as reducing dense
computation unless the global dense route is actually skipped.

The main paper result uses the conservative Task29-C policy. It reduces final
context tokens by about 4.7-5.3% across LoTTE 100k/200k/400k/638k while
preserving dense-level Hit@10, with mean above-dense Hit@10 on 200k, 400k, and
638k.

## Feedback-Triggered Recovery

IntentWeight can also use feedback as a recovery signal after a compressed
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

## Algorithm Sketch

```text
Input: query q_t, corpus D, route artifacts, LinUCB state

1. Embed q_t and compute context features x_t.
2. Score cluster arms with LinUCB.
3. Retrieve candidates from:
   a. global dense route,
   b. global BM25 route,
   c. dense search within selected cluster arms.
4. Fuse route rankings.
5. Apply confidence-based final context policy.
6. Evaluate retrieval quality for q_t.
7. Only after evaluation, convert the ground-truth label into simulated
   feedback and update LinUCB for later queries.
8. If the interaction is a post-feedback retry or a later query in a risky
   local region, use the updated arm state to choose a safer context budget or
   fallback path.

Output: final retrieved context C_t and updated policy state
```

## Implementation Notes for the Paper

- Dense baseline uses `sentence-transformers/all-MiniLM-L6-v2`.
- The main LoTTE experiments use cached embeddings and retrieval artifacts only
  to avoid repeated deterministic computation; final metrics are recomputed
  from saved rankings, not copied from prior summaries.
- The retrieval metrics use query-level `Hit@K` as the primary headline. Legacy
  `Recall@K` fields are treated as equivalent to Hit@K in historical files.
- `evidence_recall@K` should be reported separately when multi-evidence recall
  is needed. Context compaction can preserve query-level Hit@K while lowering
  evidence completeness when multiple GT chunks are expected.
