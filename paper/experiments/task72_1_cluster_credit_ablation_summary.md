# Task72.1 Cluster-Credit Feedback Ablation Summary

Updated: 2026-07-13

## Objective and Protocol

Task72.1 isolates the feedback mechanism after Task72 showed that final-fused
Dense/BM25/cluster reward masks cluster-route credit. It reuses the unchanged,
predeclared Task72 A-to-B-to-A event streams for LoTTE technology/search 100k
and science/search 100k: 212 events and 152 unique query IDs per domain, with
controller seeds 13, 17, and 19.

All five treatments use the same selected cluster-arm retrieval surface:
Dense depth, BM25 depth, and Dense floor are zero; cluster depth is 100; the
cluster ranking alone supplies the fixed final top-10. Feedback is derived from
that same cluster-only ranking (`reward_attribution=cluster_only`). The
treatments are static-nearest, cold LinUCB without updates, equal-noisy
feedback, trust-weighted feedback, and oracle feedback. No answer, response,
or final-context cache is used.

The protocol completed `6,360 = 2 domains x 212 events x 5 treatments x 3
seeds` event rows. It validates complete event coverage, zero Dense/BM25 calls,
zero updates for static/cold controls, and nonzero feedback-induced policy
updates for equal-noisy, trust-weighted, and oracle treatments.

## Cluster-Only Retrieval Outcomes

The following are descriptive event means over the three controller seeds.
They are not pooled IID estimates; all formal comparisons remain separated by
domain, stream condition, and seed with query-ID block bootstrap intervals.

| Domain | Treatment | Hit@10 | EvidenceRecall@10 | MRR@10 | Selected-cluster hit |
|---|---|---:|---:|---:|---:|
| science/search 100k | static-nearest | 0.811 | 0.620 | 0.676 | 0.860 |
| science/search 100k | cold no-feedback | 0.123 | 0.072 | 0.107 | 0.131 |
| science/search 100k | equal-noisy | 0.266 | 0.179 | 0.221 | 0.285 |
| science/search 100k | trust-weighted | 0.412 | 0.290 | 0.354 | 0.439 |
| science/search 100k | oracle | 0.522 | 0.363 | 0.446 | 0.546 |
| technology/search 100k | static-nearest | 0.832 | 0.621 | 0.701 | 0.914 |
| technology/search 100k | cold no-feedback | 0.134 | 0.072 | 0.120 | 0.145 |
| technology/search 100k | equal-noisy | 0.228 | 0.138 | 0.194 | 0.252 |
| technology/search 100k | trust-weighted | 0.259 | 0.155 | 0.229 | 0.281 |
| technology/search 100k | oracle | 0.561 | 0.388 | 0.477 | 0.608 |

Oracle feedback has a positive Hit@10 difference from cold in every tested
domain, condition, and controller seed. The per-seed query-block bootstrap
intervals are strictly positive: science has `+18.8pp` to `+56.2pp`, and
technology has `+20.3pp` to `+62.5pp`. This establishes that the fixed
cluster-only policy surface has learnable improvement capacity when the
feedback observation is perfectly aligned with its cluster-route objective.

Trust-weighted noisy feedback improves over cold in important but not all
trajectories. On science, its repeated and nearby gains are clearly positive
for seeds 13/17 but not seed 19; unseen-tail gains are positive for seeds
13/17 and inconclusive for seed 19. On technology, repeated-query results are
mixed, nearby gains are positive for seeds 13/19, and unseen-tail gains are
positive for seeds 17/19. Equal-noisy feedback is similarly heterogeneous and
weaker on average.

Trust-weighting itself is not a stable superiority result over equal-noisy
feedback: it is strongly positive in some science seed-13 conditions, negative
in technology seed-13 repeated queries, and inconclusive in several remaining
cells. Static-nearest remains substantially stronger than every learned
treatment on both domains. Therefore, this experiment does not establish that
the current trust rule dominates a static geometry prior.

## What This Establishes

Together with Task72, the evidence separates two claims that must not be
merged:

1. **Controlled route-learning capacity:** when feedback reward is attributed
   to the cluster route that the policy actually selects, simulated feedback
   can materially improve cluster-only retrieval over a cold controller. The
   oracle treatment verifies this mechanism cleanly; noisy feedback shows
   conditional, not universal, improvement.
2. **Full-fusion boundary:** the same result does not imply that feedback
   reliably improves final fused Dense+BM25+cluster retrieval. Task72 found no
   such stable final-retrieval effect because global rescue routes alter the
   credit signal and can mask route differences.

The valid paper-facing formulation is consequently narrow: controlled
simulated feedback demonstrates an adaptive cluster-route correction mechanism
under aligned credit, while its practical benefit depends on feedback quality,
corpus/stream structure, and its integration with stronger static geometry and
global retrieval routes. It is not real-user RLHF validation, a claim of
universal feedback superiority, or evidence that the method replaces Dense.

## Traceability

- Protocol: `task72_1_cluster_credit_ablation_plan.md`
- Executable: `scripts/task72_1_cluster_credit_ablation.py`
- Full coverage and invariants: `results/task72_1_cluster_credit_ablation/validation.json`
- Event metrics: `results/task72_1_cluster_credit_ablation/event_rows.csv`, `summary.csv`
- Per-condition paired inference: `results/task72_1_cluster_credit_ablation/paired.csv`
- Learning and recovery diagnostics: `adaptation.csv`, `recovery.csv`, `controller_updates.csv`
- Full-fusion companion boundary: `task72_recurrent_feedback_stream_summary.md`
