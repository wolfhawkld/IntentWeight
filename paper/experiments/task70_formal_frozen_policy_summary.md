# Task70 Formal Frozen Unseen-Query Evaluation

Updated: 2026-07-13

## Status

Complete. This is the formal replacement for the earlier one-seed, one-epoch
Task70 smoke. It evaluates whether route-policy state learned from disjoint
history queries transfers to previously unseen query folds.

## Protocol

- Datasets: LoTTE technology/search 100k and science/search 100k.
- Five canonical folds, 596 queries per dataset, and seeds 13/17/19.
- Learned full and learned gated policies train for eight prequential epochs
  on four folds. The fifth fold is ranked once with policy matrices, feedback
  memory, route statistics, and reward history frozen.
- Baselines: static-nearest full/gated, cold no-feedback full/gated, and
  Dense top-10.
- Metrics: Hit@10, EvidenceRecall@10, MRR@10, nDCG@10, seed summaries,
  10,000-sample query-paired bootstrap intervals, and exact McNemar tests.
- Held-out test feedback updates are zero for every one of the 180
  fold-method-seed cells.

## Out-of-Fold Results

| Dataset | Dense Hit@10 | Learned full | Static full | Cold no-feedback full | Learned gated |
|---|---:|---:|---:|---:|---:|
| technology/search 100k | 0.8674 | 0.8792 | 0.8764 | 0.8803 | 0.8266 |
| science/search 100k | 0.8926 | 0.9004 | 0.9060 | 0.9044 | 0.8367 |

## Primary Paired Findings

| Dataset | Learned full vs cold full | Learned full vs static full | Learned gated vs Dense |
|---|---:|---:|---:|
| technology/search 100k | -0.11pp, no McNemar-significant seed | +0.28pp, no McNemar-significant seed | -4.08pp, significant in 3/3 seeds |
| science/search 100k | -0.39pp, no McNemar-significant seed | -0.56pp, no McNemar-significant seed | -5.59pp, significant in 3/3 seeds |

The full-route learned policy is above Dense on average in both domains, but
its paired advantage is not stable enough to establish a universal
unseen-query improvement. More importantly, learned feedback does not exceed
the matched cold or static-nearest controls: it is slightly lower than cold
full routing in both domains and lower than static full routing on science.

## Supported and Unsupported Claims

Supported:

- The full multi-route surface, including dense/BM25 rescue, transfers to
  unseen queries with near- or above-Dense Hit@10 in both tested domains.
- Static local geometry remains a competitive unseen-query route signal.
- Learned cost-aware gating is unsafe as a frozen first-pass policy in these
  two domains; its Hit@10 loss is statistically detected in every seed.

Not supported:

- A transferable first-pass advantage of trust-weighted learned feedback over
  static-nearest or cold no-feedback routing.
- A claim that feedback learning makes frozen unseen-query gating safe.
- Any final-context token-saving, answer-quality, real-human-feedback, or
  universal non-inferiority conclusion. Task70 is retrieval-only.

## Paper Use Decision

The manuscript must position feedback as controlled repeated-query adaptation
and hard-case recovery, not as demonstrated first-pass generalization to new
queries. Geometry-guided route construction, Dense/BM25 rescue, and the
independently calibrated context budget remain intact. The title may retain
Feedback-Adaptive as an architectural descriptor only if the abstract and
main claims explicitly state this boundary; otherwise title wording requires
a separate author decision before modification.

## Artifacts and Validation

- `results/task70_formal_technology_100k.*`
- `results/task70_formal_science_100k.*`
- `results/task70_formal_validation.json` and `.md`
- `scripts/task70_frozen_policy_generalization.py`
- `scripts/task70_validate_frozen_policy.py`
- `cache/test_linucb_frozen_policy.py`

The independent Task70 validator confirms, for both datasets: 596-query
ranking coverage for every method/seed, 90 complete fold-method-seed cells,
18 required paired rows, five complete checkpoints, eight learned history
epochs, and zero held-out feedback updates.
