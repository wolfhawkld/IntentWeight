# Task53 Embedding Backbone Generalization Summary

Updated: 2026-06-24

## Objective

Test whether the IntentWeight quality-cost pattern is tied to the original
MiniLM dense backbone or holds under matched embedding backbones. Each
IntentWeight variant is compared against the dense baseline produced by the
same embedding model on the same LoTTE technology/search 100k corpus and the
Task38 frozen held-out split.

## Artifacts

- Summary script:
  `paper/experiments/scripts/task53_embedding_backbone_generalization.py`
- Aggregate summary:
  `paper/experiments/results/task53_embedding_backbone_generalization.md`
- Per-seed CSV:
  `paper/experiments/results/task53_embedding_backbone_generalization.per_seed.csv`
- E5 dense baseline:
  `paper/experiments/results/task53_e5_base_100k_dense/`
- BGE and E5 matched-backbone context-budget outputs:
  `paper/experiments/results/task53_bge_base_100k_*`
  and `paper/experiments/results/task53_e5_base_100k_*`

## Main Result

| Backbone | Route mode | Selected policy | Dense Hit@10 | Method Hit@10 | Mean hit delta | Mean token saving |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MiniLM | gated_cost_aware | `token_budget_r0.95_m4` | 0.8705 | 0.8705 | +0.00 pp | 6.18% |
| BGE-base | full_multi_route | `token_budget_r0.92_m4` | 0.8993 | 0.8985 | -0.08 pp | 11.99% |
| BGE-base | gated_cost_aware | `token_budget_r0.88_m4` | 0.8993 | 0.8745 | -2.48 pp | 16.21% |
| E5-base | full_multi_route | `token_budget_r0.88_m7` | 0.8753 | 0.8689 | -0.64 pp | 12.20% |
| E5-base | gated_cost_aware | `token_budget_r0.95_m4` | 0.8753 | 0.8409 | -3.44 pp | 6.83% |

The BGE and E5 full multi-route variants are the positive matched-backbone
evidence: they preserve or nearly preserve dense Hit@10 on average while
reducing final context tokens by about 12%. The gated-cost variants are useful
boundary evidence: they reduce retrieval-stage dense usage but lower Hit@10
under BGE and E5.

## E5 Runtime Note

The E5 dense baseline used `intfloat/e5-base-v2` with `query: ` and `passage: `
prefixes. The first full 100k dense embedding/ranking run used `.venv-rocm` and
AMD ROCm, completed in 1273.572 seconds, and produced local embedding/model
caches under `paper/experiments/data/`. Those caches are local-only and should
not be committed.

## Paper-Use Guidance

Task53 supports the stronger robustness framing:

> IntentWeight is best presented as a matched-backbone route-and-budget layer
> that can reduce final context tokens under controlled quality change, rather
> than as a MiniLM-specific dense replacement.

Do not claim universal strict non-inferiority. The 1pp CI non-inferiority check
is not established for the single-scale seed rows in Task53. The safer wording
is quality-cost trade off with backbone-level robustness, using full
multi-route as the quality-preserving point and gated-cost routing as the
cost-aggressive boundary.
