# Task53 Embedding Backbone Generalization

## Aggregate Matched-Backbone Results

| backbone | route_mode | selected_policy | calib eligible | baseline Hit@10 | method Hit@10 | mean hit delta | mean token saving | NI seeds |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BGE-base | full_multi_route | token_budget_r0.92_m4 | True | 0.8993 | 0.8985 | -0.08 pp | 11.99% | 0/3 |
| BGE-base | gated_cost_aware | token_budget_r0.88_m4 | False | 0.8993 | 0.8745 | -2.48 pp | 16.21% | 0/3 |
| E5-base | full_multi_route | token_budget_r0.88_m7 | True | 0.8753 | 0.8689 | -0.64 pp | 12.20% | 0/3 |
| E5-base | gated_cost_aware | token_budget_r0.95_m4 | False | 0.8753 | 0.8409 | -3.44 pp | 6.83% | 0/3 |
| MiniLM | gated_cost_aware | token_budget_r0.95_m4 | True | 0.8705 | 0.8705 | +0.00 pp | 6.18% | 0/3 |

## Per-Seed Frozen Test Results

| backbone | route_mode | seed | method Hit@10 | baseline Hit@10 | hit delta | CI low | CI high | token saving | McNemar p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM | gated_cost_aware | 13 | 0.8681 | 0.8705 | -0.24 pp | -2.40 pp | +1.92 pp | 6.43% | 1 |
| MiniLM | gated_cost_aware | 17 | 0.8657 | 0.8705 | -0.48 pp | -2.40 pp | +1.20 pp | 7.14% | 0.8036 |
| MiniLM | gated_cost_aware | 19 | 0.8777 | 0.8705 | +0.72 pp | -1.44 pp | +3.12 pp | 4.98% | 0.69 |
| BGE-base | full_multi_route | 13 | 0.8993 | 0.8993 | +0.00 pp | -1.44 pp | +1.44 pp | 12.43% | 1 |
| BGE-base | full_multi_route | 17 | 0.8945 | 0.8993 | -0.48 pp | -2.16 pp | +1.20 pp | 12.03% | 0.7905 |
| BGE-base | full_multi_route | 19 | 0.9017 | 0.8993 | +0.24 pp | -1.20 pp | +1.68 pp | 11.50% | 1 |
| BGE-base | gated_cost_aware | 13 | 0.8801 | 0.8993 | -1.92 pp | -4.08 pp | +0.24 pp | 16.72% | 0.09625 |
| BGE-base | gated_cost_aware | 17 | 0.8705 | 0.8993 | -2.88 pp | -5.04 pp | -0.72 pp | 16.67% | 0.0169 |
| BGE-base | gated_cost_aware | 19 | 0.8729 | 0.8993 | -2.64 pp | -4.56 pp | -0.72 pp | 15.24% | 0.01273 |
| E5-base | full_multi_route | 13 | 0.8681 | 0.8753 | -0.72 pp | -2.40 pp | +0.48 pp | 12.77% | 0.5078 |
| E5-base | full_multi_route | 17 | 0.8681 | 0.8753 | -0.72 pp | -2.16 pp | +0.48 pp | 12.25% | 0.5078 |
| E5-base | full_multi_route | 19 | 0.8705 | 0.8753 | -0.48 pp | -2.16 pp | +0.96 pp | 11.58% | 0.7744 |
| E5-base | gated_cost_aware | 13 | 0.8369 | 0.8753 | -3.84 pp | -6.47 pp | -1.44 pp | 5.27% | 0.005223 |
| E5-base | gated_cost_aware | 17 | 0.8345 | 0.8753 | -4.08 pp | -6.47 pp | -1.92 pp | 8.11% | 0.0009105 |
| E5-base | gated_cost_aware | 19 | 0.8513 | 0.8753 | -2.40 pp | -4.56 pp | -0.24 pp | 7.12% | 0.04139 |

## Interpretation

- Matched-backbone comparison is essential: each IntentWeight row is compared against the dense baseline produced by the same embedding model.
- BGE and E5 full multi-route variants preserve or nearly preserve dense Hit@10 on average while reducing final context tokens by about 12%.
- The gated-cost variants save retrieval-stage dense calls, but they lower Hit@10 under BGE and E5; use them as cost-aggressive boundary points rather than the main quality-preserving result.
- Strict 1pp CI non-inferiority is not established for these 100k single-scale seed rows, so paper wording should say quality-cost trade off rather than universal non-inferiority.
