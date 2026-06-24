# Task55 Backbone Stability Summary

Task55 is a no-rerun stability summary over existing Task38, Task53, and Task54 artifacts.
It uses the common seeds `13,17,19` and treats paired query-level bootstrap/McNemar
statistics as the primary evidence, with seed-level variance as a stability check.

The purpose is not to search for a favorable seed. Seeds are fixed replicate
conditions used to test whether the route-and-budget claims remain stable and
statistically checkable under random clustering/order/feedback variation.

## Aggregate Stability

| setting | policy | seeds | baseline Hit@10 | method Hit@10 | hit delta mean | hit delta SD | seed 95% CI | token saving mean | token saving SD | NI seeds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM gated | `token_budget_r0.95_m4` | 13,17,19 | 0.8705 | 0.8705 | +0.00 pp | +0.63 pp | [-1.58 pp, +1.58 pp] | 6.18% | 1.10% | 0/3 |
| BGE full | `token_budget_r0.92_m4` | 13,17,19 | 0.8993 | 0.8985 | -0.08 pp | +0.37 pp | [-0.99 pp, +0.83 pp] | 11.99% | 0.46% | 0/3 |
| BGE gated | `token_budget_r0.88_m4` | 13,17,19 | 0.8993 | 0.8745 | -2.48 pp | +0.50 pp | [-3.72 pp, -1.24 pp] | 16.21% | 0.84% | 0/3 |
| E5 full | `token_budget_r0.88_m7` | 13,17,19 | 0.8753 | 0.8689 | -0.64 pp | +0.14 pp | [-0.98 pp, -0.30 pp] | 12.20% | 0.60% | 0/3 |
| E5 gated | `token_budget_r0.95_m4` | 13,17,19 | 0.8753 | 0.8409 | -3.44 pp | +0.91 pp | [-5.69 pp, -1.18 pp] | 6.83% | 1.44% | 0/3 |
| BGE positive | `token_budget_r0.97_m4` | 13,17,19 | 0.8993 | 0.9081 | +0.88 pp | +0.14 pp | [+0.54 pp, +1.22 pp] | 7.23% | 0.81% | 3/3 |

## Per-Seed Paired Evidence

| setting | seed | method Hit@10 | baseline Hit@10 | hit delta | paired CI low | paired CI high | token saving | McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM gated | 13 | 0.8681 | 0.8705 | -0.24 pp | -2.40 pp | +1.92 pp | 6.43% | 1 |
| MiniLM gated | 17 | 0.8657 | 0.8705 | -0.48 pp | -2.40 pp | +1.20 pp | 7.14% | 0.8036 |
| MiniLM gated | 19 | 0.8777 | 0.8705 | +0.72 pp | -1.44 pp | +3.12 pp | 4.98% | 0.69 |
| BGE full | 13 | 0.8993 | 0.8993 | +0.00 pp | -1.44 pp | +1.44 pp | 12.43% | 1 |
| BGE full | 17 | 0.8945 | 0.8993 | -0.48 pp | -2.16 pp | +1.20 pp | 12.03% | 0.7905 |
| BGE full | 19 | 0.9017 | 0.8993 | +0.24 pp | -1.20 pp | +1.68 pp | 11.50% | 1 |
| BGE gated | 13 | 0.8801 | 0.8993 | -1.92 pp | -4.08 pp | +0.24 pp | 16.72% | 0.09625 |
| BGE gated | 17 | 0.8705 | 0.8993 | -2.88 pp | -5.04 pp | -0.72 pp | 16.67% | 0.0169 |
| BGE gated | 19 | 0.8729 | 0.8993 | -2.64 pp | -4.56 pp | -0.72 pp | 15.24% | 0.01273 |
| E5 full | 13 | 0.8681 | 0.8753 | -0.72 pp | -2.40 pp | +0.48 pp | 12.77% | 0.5078 |
| E5 full | 17 | 0.8681 | 0.8753 | -0.72 pp | -2.16 pp | +0.48 pp | 12.25% | 0.5078 |
| E5 full | 19 | 0.8705 | 0.8753 | -0.48 pp | -2.16 pp | +0.96 pp | 11.58% | 0.7744 |
| E5 gated | 13 | 0.8369 | 0.8753 | -3.84 pp | -6.47 pp | -1.44 pp | 5.27% | 0.005223 |
| E5 gated | 17 | 0.8345 | 0.8753 | -4.08 pp | -6.47 pp | -1.92 pp | 8.11% | 0.0009105 |
| E5 gated | 19 | 0.8513 | 0.8753 | -2.40 pp | -4.56 pp | -0.24 pp | 7.12% | 0.04139 |
| BGE positive | 13 | 0.9089 | 0.8993 | +0.96 pp | -0.48 pp | +2.40 pp | 8.11% | 0.3438 |
| BGE positive | 17 | 0.9065 | 0.8993 | +0.72 pp | -0.72 pp | +2.16 pp | 7.07% | 0.5488 |
| BGE positive | 19 | 0.9089 | 0.8993 | +0.96 pp | -0.24 pp | +2.40 pp | 6.50% | 0.2891 |

## Interpretation

- BGE full multi-route is stable as a near-dense token-saving operating point: mean Hit@10 delta is about -0.08pp with 0.37pp seed SD and about 11.99% token saving.
- BGE positive-hit tuning is stable as a quality-first operating point: mean Hit@10 delta is about +0.88pp with 0.14pp seed SD and about 7.23% token saving.
- E5 full multi-route is stable but slightly below its dense baseline: mean Hit@10 delta is about -0.64pp with 0.14pp seed SD and about 12.20% token saving.
- BGE/E5 gated-cost variants show stable negative Hit@10 deltas, so they should be presented as cost-aggressive boundary evidence rather than the main quality-preserving result.
- Do not describe this as a large multi-repeat experiment or seed search. The defensible wording is fixed three-seed stability plus paired query-level statistical checks.
