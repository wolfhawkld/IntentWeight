# Task33.4 Protocol Defense

Updated: 2026-05-26

Task33.4 records the paper-facing defense of the prequential feedback protocol.
The purpose is to avoid a common reviewer misunderstanding: the LinUCB
experiments use ground-truth-derived simulated feedback, but the feedback for a
query is not used to rank that same query.

## Core Protocol Statement

IntentWeight evaluates adaptive retrieval under a no-leakage prequential
protocol. For each query `q_t` in the stream:

1. the current retrieval policy state `S_t` is frozen;
2. the system ranks candidates and returns the final context for `q_t`;
3. retrieval metrics for `q_t` are computed from the produced ranking;
4. only after the ranking has been evaluated, the ground-truth label for `q_t`
   is converted into simulated feedback;
5. LinUCB updates its arm statistics to produce the next state `S_{t+1}`;
6. later queries may benefit from this update, but `q_t` itself cannot.

Therefore, the experiment is not offline IID training followed by a held-out
test. It is simulated test-time adaptation over a query stream.

## What Is Allowed

- The corpus, embeddings, BM25 artifacts, KMeans clusters, and dense rankings
  may be precomputed because they are deterministic retrieval artifacts and do
  not use feedback from future queries.
- The policy state may use feedback from earlier queries in the stream.
- Ground truth may be used after a query is evaluated to simulate explicit or
  implicit feedback for later updates.
- Multiple epochs are interpreted as repeated controlled interaction over the
  same benchmark stream, not as a hidden offline test set.

## What Is Not Allowed

- The feedback or ground truth for `q_t` is not used to rank `q_t`.
- Future query feedback is not used to rank earlier queries.
- Final reported metrics are computed from saved rankings produced before the
  corresponding query update.
- The experiment does not claim that real human feedback has been collected.
- The experiment does not claim offline IID generalization from a separately
  trained bandit policy.

## Paper Wording

Recommended wording:

> We evaluate IntentWeight with a prequential simulated-feedback protocol. For
> each query, the current policy first produces a ranking and the ranking is
> evaluated. Only then is the query's ground-truth-derived feedback used to
> update the LinUCB state for subsequent queries. This protocol evaluates
> controlled test-time adaptation and prevents future-label leakage into the
> current ranking.

Recommended limitation wording:

> Because feedback is simulated from ground truth, the experiment validates the
> adaptive route-learning mechanism under controlled feedback quality. It does
> not replace a deployment study with real users, delayed feedback, or biased
> implicit behavior.

Avoid wording:

> The policy is trained on the test set and then evaluated.

Avoid wording:

> Simulated feedback proves real human feedback will produce the same effect.

## Why This Matters

The main claims rely on separating two facts:

- retrieval quality for each query is measured before that query updates the
  policy;
- policy quality can improve over the stream because earlier feedback changes
  later route choices.

This distinction lets the paper claim feedback-driven adaptation without
claiming standard offline supervised generalization. It also explains why
feedback gains may be clearer in route-policy metrics such as selected-cluster
hit rate and last true reward than in final Hit@10, where dense and BM25
fallback routes already provide strong protection.
