# Task24 Academic Audit Fixes

Updated: 2026-05-21

Task24 converts the academic audit into concrete fixes before paper writing. The goal is not to add a new headline result, but to remove avoidable reviewer risks in metric naming, ablation completeness, protocol wording, cost claims, and feedback/manifold interpretation.

## Implemented Fixes

1. Metric naming is now explicit:
   - `hit@k`: query-level success, equal to the legacy `recall@k` field used in earlier result files.
   - `evidence_recall@k`: standard evidence recall, the fraction of all GT chunks retrieved.
   - `recall@k`: retained as a backward-compatible alias for historical summaries.
2. Static and naive online ablations were added to `linucb_cost_aware_routing.py`:
   - `static_nearest_ensemble`: same dense/BM25/cluster weighted RRF and dense floor, but cluster arms are selected by nearest centroid and no policy update is applied.
   - `uniform_random_ensemble`: same retrieval surface, random cluster arms, no policy update.
   - `epsilon_greedy_ensemble`: same retrieval surface, non-contextual epsilon-greedy arm learning.
3. Tests were updated for the new metric semantics and new routing modes.
4. The paper-facing interpretation is tightened:
   - prequential results are simulated test-time adaptation, not an IID held-out evaluation after offline training;
   - cost reduction is relative to full multi-route retrieval, not dense-only retrieval;
   - manifold wording should be framed as an assumption plus diagnostics, not a proven theorem;
   - simulated trust-weighted feedback validates controllability of the policy layer, not real human feedback behavior.

## 638k Audit Ablation Snapshot

All rows use LoTTE technology/search full `638509` corpus, `596` held-out test queries, `top_k=10`, `seeds=13,17,19`, and shared scale-store/artifact caches where applicable.

| Method | Hit@10 | Evidence Recall@10 | MRR@10 | nDCG@10 | Last True Reward | Selected Cluster Hit | Source Cost | Dense Query Rate | Learning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BM25-only | 0.5084 | n/a | 0.2910 | 0.2451 | n/a | n/a | 100 | 0.0000 | none |
| Dense-only | 0.7282 | n/a | 0.5102 | 0.4303 | n/a | n/a | 100 | 1.0000 | none |
| Hybrid RRF | 0.7181 | n/a | 0.4675 | 0.3954 | n/a | n/a | 200 | 1.0000 | none |
| Full multi-route LinUCB | 0.7612 | 0.5192 | 0.5153 | 0.4358 | 0.5034 | 0.5136 | 300.00 | 1.0000 | contextual LinUCB |
| Gated cost-aware LinUCB | 0.7343 | 0.4932 | 0.5089 | 0.4233 | 0.4636 | 0.4965 | 236.22 | 0.9146 | contextual LinUCB |
| Static nearest ensemble | 0.7612 | 0.5154 | 0.5151 | 0.4354 | 0.7030 | 0.9016 | 300.00 | 1.0000 | none |
| Uniform random ensemble | 0.7634 | 0.5170 | 0.5155 | 0.4352 | 0.0990 | 0.1473 | 300.00 | 1.0000 | none |
| Epsilon-greedy ensemble | 0.7578 | 0.5131 | 0.5144 | 0.4339 | 0.2136 | 0.2582 | 300.00 | 1.0000 | non-contextual bandit |

## Interpretation

The new ablations change the claim boundary.

First, final Hit@10 alone is not enough to isolate the value of LinUCB when global dense, BM25, cluster-local retrieval, weighted RRF, and dense floor are all active. The full retrieval surface is strong enough that random or simple arm selection can still produce similar final Hit@10, because global dense/BM25 candidates protect the final list.

Second, arm quality metrics reveal a different picture. Uniform random and epsilon-greedy baselines have much lower selected-cluster quality (`0.1473` and `0.2582`) than static nearest centroid (`0.9016`). This means final retrieval quality is partly masked by the dense floor. The paper should therefore report both downstream retrieval metrics and policy/arm metrics.

Third, static nearest centroid is a strong geometry baseline on LoTTE 638k. This supports the manifold/geometry assumption, but it also means the paper should not claim that LinUCB is the only reason full multi-route retrieval improves over dense. A safer claim is that dense/BM25/cluster multi-route retrieval provides robust coverage, while LinUCB turns this retrieval surface into a feedback-adaptive and cost-aware controller.

Fourth, the cost-aware result remains useful but must be written carefully. Gated cost-aware LinUCB remains above dense-only Hit@10 (`0.7343` vs `0.7282`) while reducing source candidate cost relative to full multi-route (`236.22` vs `300.00`, about `21.3%`). It is not cheaper than dense-only in absolute source candidates.

## Paper Wording Fix

Use this bounded claim:

> IntentWeight does not unconditionally dominate dense retrieval. Instead, it builds a multi-route retrieval surface with dense as a recall floor and uses feedback-driven contextual bandit routing to learn when cluster-local and lightweight routes are reliable enough to reduce dense-heavy retrieval cost. On LoTTE 638k, full multi-route retrieval improves Hit@10 over dense-only, while gated LinUCB preserves a smaller quality gain with lower source-candidate cost relative to full multi-route.

Avoid this overclaim:

> LinUCB is solely responsible for the retrieval-quality gain over dense.

## Remaining Risk

The strongest unresolved ablation is a static nearest-centroid cost-gated baseline, such as nearest-cluster plus BM25-lite/dense-lite without LinUCB confidence. If reviewers ask whether the cost gate itself needs LinUCB, this should be the next targeted experiment. It is not required before drafting, but the limitation should be acknowledged if not run.

## Source Files

- Metric code: `paper/experiments/scripts/retrieval_metrics.py`
- Routing code: `paper/experiments/scripts/linucb_cost_aware_routing.py`
- Static ablation: `paper/experiments/results/task24_static_ensemble_638k/`
- Naive online ablations: `paper/experiments/results/task24_online_baselines_638k/`
- Existing 638k LinUCB formal run: `paper/experiments/results/task22_9_lotte_638k_linucb_formal/`
