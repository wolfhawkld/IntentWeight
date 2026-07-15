# Task72.1 Cluster-Credit Feedback Ablation

## Scope

This ablation reuses the predeclared Task72 streams but disables Dense and BM25 retrieval, Dense floors, answer caching, and final-context caching. The simulated reward is the selected cluster-route reward (`cluster_only`). It evaluates a route-learning mechanism, not end-to-end RAG, real-user RLHF, or a replacement for the full-fusion Task72 boundary.

## Stream and Integrity

| Dataset | Region-A arm | Region-B arm | Events | Unique queries |
|---|---:|---:|---:|---:|
| lotte_science_search_100k | 21 | 3 | 212 | 152 |
| lotte_technology_search_100k | 14 | 16 | 212 | 152 |

- Event coverage: passed (6360/6360).
- Cluster-only retrieval invariant: passed.
- Feedback-update invariant: passed.

## Per-Seed Outcomes

`selected_cluster_hit`, route reward, and all retrieval metrics are measured on the same cluster-only ranked top-10. Seed rows are intentionally kept separate; paired block-bootstrap intervals are not pooled across seeds or domains.

| Dataset | Method | Seed | Condition | Phase | n | Hit@10 | Recall@10 | MRR@10 | nDCG@10 | Cluster hit |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | nearby | A_nearby | 24 | 0.083 | 0.062 | 0.083 | 0.064 | 0.083 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | nearby | B_nearby | 24 | 0.167 | 0.125 | 0.167 | 0.135 | 0.167 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_return | 20 | 0.300 | 0.092 | 0.258 | 0.118 | 0.300 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.150 | 0.087 | 0.150 | 0.101 | 0.150 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.100 | 0.037 | 0.100 | 0.050 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 0.050 | 0.025 | 0.025 | 0.019 | 0.050 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 0.100 | 0.100 | 0.100 | 0.100 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | unseen | unseen_tail | 64 | 0.078 | 0.055 | 0.070 | 0.052 | 0.078 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | nearby | A_nearby | 24 | 0.125 | 0.089 | 0.089 | 0.069 | 0.167 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | nearby | B_nearby | 24 | 0.083 | 0.062 | 0.062 | 0.054 | 0.083 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_return | 20 | 0.100 | 0.033 | 0.075 | 0.037 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.050 | 0.050 | 0.050 | 0.050 | 0.050 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 0.100 | 0.100 | 0.100 | 0.094 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 0.150 | 0.100 | 0.150 | 0.105 | 0.150 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | unseen | unseen_tail | 64 | 0.172 | 0.078 | 0.151 | 0.088 | 0.203 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | nearby | A_nearby | 24 | 0.042 | 0.010 | 0.042 | 0.016 | 0.042 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | nearby | B_nearby | 24 | 0.167 | 0.106 | 0.111 | 0.101 | 0.167 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_return | 20 | 0.100 | 0.050 | 0.100 | 0.062 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.100 | 0.042 | 0.075 | 0.047 | 0.100 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.250 | 0.150 | 0.212 | 0.157 | 0.250 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 0.200 | 0.133 | 0.200 | 0.146 | 0.200 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 0.200 | 0.108 | 0.150 | 0.104 | 0.200 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | unseen | unseen_tail | 64 | 0.109 | 0.066 | 0.088 | 0.065 | 0.141 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | nearby | A_nearby | 24 | 0.125 | 0.044 | 0.104 | 0.055 | 0.125 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | nearby | B_nearby | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_return | 20 | 0.050 | 0.010 | 0.017 | 0.008 | 0.050 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | repeated | B_recurrent_shift_1 | 20 | 0.150 | 0.085 | 0.083 | 0.060 | 0.150 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | repeated | B_recurrent_shift_2 | 20 | 0.150 | 0.098 | 0.085 | 0.072 | 0.150 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | unseen | unseen_tail | 64 | 0.141 | 0.078 | 0.106 | 0.075 | 0.156 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | nearby | A_nearby | 24 | 0.500 | 0.372 | 0.410 | 0.344 | 0.583 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | nearby | B_nearby | 24 | 0.625 | 0.543 | 0.550 | 0.496 | 0.667 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_return | 20 | 0.700 | 0.463 | 0.624 | 0.495 | 0.700 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.650 | 0.438 | 0.570 | 0.463 | 0.650 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.700 | 0.463 | 0.624 | 0.495 | 0.700 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | repeated | B_recurrent_shift_1 | 20 | 0.650 | 0.562 | 0.515 | 0.499 | 0.700 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | repeated | B_recurrent_shift_2 | 20 | 0.750 | 0.629 | 0.590 | 0.563 | 0.750 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | unseen | unseen_tail | 64 | 0.297 | 0.177 | 0.283 | 0.197 | 0.328 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | nearby | A_nearby | 24 | 0.042 | 0.042 | 0.006 | 0.014 | 0.042 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | nearby | B_nearby | 24 | 0.167 | 0.125 | 0.125 | 0.120 | 0.167 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_return | 20 | 0.550 | 0.352 | 0.512 | 0.382 | 0.550 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.050 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | repeated | B_recurrent_shift_1 | 20 | 0.100 | 0.050 | 0.060 | 0.038 | 0.100 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | repeated | B_recurrent_shift_2 | 20 | 0.150 | 0.100 | 0.108 | 0.087 | 0.150 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | unseen | unseen_tail | 64 | 0.219 | 0.090 | 0.176 | 0.099 | 0.250 |
| lotte_science_search_100k | cluster_oracle | 13 | nearby | A_nearby | 24 | 0.542 | 0.409 | 0.500 | 0.414 | 0.625 |
| lotte_science_search_100k | cluster_oracle | 13 | nearby | B_nearby | 24 | 0.833 | 0.701 | 0.714 | 0.650 | 0.833 |
| lotte_science_search_100k | cluster_oracle | 13 | repeated | A_recurrent_return | 20 | 0.750 | 0.570 | 0.707 | 0.592 | 0.750 |
| lotte_science_search_100k | cluster_oracle | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.300 | 0.215 | 0.300 | 0.234 | 0.300 |
| lotte_science_search_100k | cluster_oracle | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.700 | 0.540 | 0.657 | 0.563 | 0.750 |
| lotte_science_search_100k | cluster_oracle | 13 | repeated | B_recurrent_shift_1 | 20 | 0.800 | 0.642 | 0.699 | 0.616 | 0.800 |
| lotte_science_search_100k | cluster_oracle | 13 | repeated | B_recurrent_shift_2 | 20 | 0.800 | 0.642 | 0.698 | 0.615 | 0.800 |
| lotte_science_search_100k | cluster_oracle | 13 | unseen | unseen_tail | 64 | 0.391 | 0.223 | 0.321 | 0.224 | 0.406 |
| lotte_science_search_100k | cluster_oracle | 17 | nearby | A_nearby | 24 | 0.542 | 0.375 | 0.431 | 0.348 | 0.625 |
| lotte_science_search_100k | cluster_oracle | 17 | nearby | B_nearby | 24 | 0.625 | 0.515 | 0.550 | 0.480 | 0.667 |
| lotte_science_search_100k | cluster_oracle | 17 | repeated | A_recurrent_return | 20 | 0.800 | 0.504 | 0.645 | 0.518 | 0.800 |
| lotte_science_search_100k | cluster_oracle | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.150 | 0.069 | 0.082 | 0.064 | 0.150 |
| lotte_science_search_100k | cluster_oracle | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.750 | 0.492 | 0.632 | 0.509 | 0.750 |
| lotte_science_search_100k | cluster_oracle | 17 | repeated | B_recurrent_shift_1 | 20 | 0.650 | 0.529 | 0.490 | 0.463 | 0.650 |
| lotte_science_search_100k | cluster_oracle | 17 | repeated | B_recurrent_shift_2 | 20 | 0.650 | 0.529 | 0.490 | 0.462 | 0.650 |
| lotte_science_search_100k | cluster_oracle | 17 | unseen | unseen_tail | 64 | 0.359 | 0.205 | 0.312 | 0.220 | 0.422 |
| lotte_science_search_100k | cluster_oracle | 19 | nearby | A_nearby | 24 | 0.458 | 0.328 | 0.417 | 0.327 | 0.500 |
| lotte_science_search_100k | cluster_oracle | 19 | nearby | B_nearby | 24 | 0.500 | 0.322 | 0.411 | 0.321 | 0.500 |
| lotte_science_search_100k | cluster_oracle | 19 | repeated | A_recurrent_return | 20 | 0.650 | 0.448 | 0.588 | 0.469 | 0.700 |
| lotte_science_search_100k | cluster_oracle | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.650 | 0.435 | 0.588 | 0.456 | 0.650 |
| lotte_science_search_100k | cluster_oracle | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.650 | 0.435 | 0.588 | 0.456 | 0.650 |
| lotte_science_search_100k | cluster_oracle | 19 | repeated | B_recurrent_shift_1 | 20 | 0.350 | 0.233 | 0.252 | 0.223 | 0.350 |
| lotte_science_search_100k | cluster_oracle | 19 | repeated | B_recurrent_shift_2 | 20 | 0.350 | 0.233 | 0.260 | 0.227 | 0.350 |
| lotte_science_search_100k | cluster_oracle | 19 | unseen | unseen_tail | 64 | 0.312 | 0.148 | 0.265 | 0.159 | 0.344 |
| lotte_science_search_100k | cluster_static_nearest | 13 | nearby | A_nearby | 24 | 0.625 | 0.410 | 0.526 | 0.393 | 0.750 |
| lotte_science_search_100k | cluster_static_nearest | 13 | nearby | B_nearby | 24 | 0.875 | 0.757 | 0.777 | 0.703 | 0.875 |
| lotte_science_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.712 | 0.821 | 0.689 | 0.950 |
| lotte_science_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.712 | 0.821 | 0.689 | 0.950 |
| lotte_science_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.712 | 0.821 | 0.689 | 0.950 |
| lotte_science_search_100k | cluster_static_nearest | 13 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.822 | 0.771 | 0.724 | 1.000 |
| lotte_science_search_100k | cluster_static_nearest | 13 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.822 | 0.771 | 0.724 | 1.000 |
| lotte_science_search_100k | cluster_static_nearest | 13 | unseen | unseen_tail | 64 | 0.766 | 0.544 | 0.651 | 0.524 | 0.844 |
| lotte_science_search_100k | cluster_static_nearest | 17 | nearby | A_nearby | 24 | 0.542 | 0.415 | 0.385 | 0.350 | 0.667 |
| lotte_science_search_100k | cluster_static_nearest | 17 | nearby | B_nearby | 24 | 0.917 | 0.749 | 0.818 | 0.712 | 0.917 |
| lotte_science_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_return | 20 | 0.900 | 0.652 | 0.725 | 0.622 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.652 | 0.725 | 0.622 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.652 | 0.725 | 0.622 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 17 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.780 | 0.722 | 0.695 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 17 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.780 | 0.722 | 0.695 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 17 | unseen | unseen_tail | 64 | 0.766 | 0.561 | 0.665 | 0.546 | 0.875 |
| lotte_science_search_100k | cluster_static_nearest | 19 | nearby | A_nearby | 24 | 0.542 | 0.372 | 0.409 | 0.337 | 0.625 |
| lotte_science_search_100k | cluster_static_nearest | 19 | nearby | B_nearby | 24 | 0.708 | 0.553 | 0.646 | 0.541 | 0.708 |
| lotte_science_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_return | 20 | 0.750 | 0.547 | 0.623 | 0.525 | 0.800 |
| lotte_science_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.750 | 0.547 | 0.623 | 0.525 | 0.800 |
| lotte_science_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.750 | 0.547 | 0.623 | 0.525 | 0.800 |
| lotte_science_search_100k | cluster_static_nearest | 19 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.761 | 0.691 | 0.668 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 19 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.761 | 0.691 | 0.668 | 0.900 |
| lotte_science_search_100k | cluster_static_nearest | 19 | unseen | unseen_tail | 64 | 0.797 | 0.568 | 0.668 | 0.543 | 0.891 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | nearby | A_nearby | 24 | 0.542 | 0.409 | 0.500 | 0.414 | 0.625 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | nearby | B_nearby | 24 | 0.833 | 0.701 | 0.714 | 0.650 | 0.833 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_return | 20 | 0.700 | 0.502 | 0.657 | 0.532 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.050 | 0.013 | 0.050 | 0.020 | 0.100 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.650 | 0.477 | 0.608 | 0.502 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | repeated | B_recurrent_shift_1 | 20 | 0.800 | 0.617 | 0.699 | 0.596 | 0.800 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | repeated | B_recurrent_shift_2 | 20 | 0.800 | 0.642 | 0.698 | 0.615 | 0.800 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | unseen | unseen_tail | 64 | 0.375 | 0.212 | 0.327 | 0.222 | 0.391 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | nearby | A_nearby | 24 | 0.458 | 0.337 | 0.375 | 0.313 | 0.542 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | nearby | B_nearby | 24 | 0.667 | 0.564 | 0.589 | 0.523 | 0.708 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_return | 20 | 0.700 | 0.463 | 0.624 | 0.495 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.600 | 0.425 | 0.557 | 0.454 | 0.600 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.700 | 0.463 | 0.624 | 0.495 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | repeated | B_recurrent_shift_1 | 20 | 0.650 | 0.588 | 0.515 | 0.517 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | repeated | B_recurrent_shift_2 | 20 | 0.700 | 0.617 | 0.565 | 0.548 | 0.700 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | unseen | unseen_tail | 64 | 0.328 | 0.193 | 0.294 | 0.203 | 0.359 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | nearby | A_nearby | 24 | 0.125 | 0.031 | 0.076 | 0.033 | 0.125 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | nearby | B_nearby | 24 | 0.042 | 0.014 | 0.042 | 0.020 | 0.042 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_return | 20 | 0.250 | 0.129 | 0.133 | 0.096 | 0.250 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.050 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.150 | 0.067 | 0.108 | 0.068 | 0.250 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | repeated | B_recurrent_shift_1 | 20 | 0.150 | 0.058 | 0.079 | 0.053 | 0.150 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | repeated | B_recurrent_shift_2 | 20 | 0.100 | 0.033 | 0.042 | 0.027 | 0.100 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | unseen | unseen_tail | 64 | 0.203 | 0.117 | 0.171 | 0.119 | 0.250 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | nearby | A_nearby | 24 | 0.208 | 0.069 | 0.208 | 0.098 | 0.208 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | nearby | B_nearby | 24 | 0.125 | 0.057 | 0.125 | 0.068 | 0.125 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_return | 20 | 0.250 | 0.098 | 0.250 | 0.135 | 0.250 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.050 | 0.050 | 0.050 | 0.046 | 0.050 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.150 | 0.041 | 0.113 | 0.050 | 0.150 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 0.300 | 0.231 | 0.260 | 0.235 | 0.300 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 0.200 | 0.087 | 0.129 | 0.086 | 0.200 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | unseen | unseen_tail | 64 | 0.125 | 0.066 | 0.105 | 0.072 | 0.156 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | nearby | A_nearby | 24 | 0.083 | 0.018 | 0.083 | 0.038 | 0.083 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | nearby | B_nearby | 24 | 0.167 | 0.146 | 0.146 | 0.141 | 0.167 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_return | 20 | 0.150 | 0.069 | 0.117 | 0.075 | 0.150 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.100 | 0.058 | 0.100 | 0.066 | 0.100 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.050 | 0.028 | 0.050 | 0.035 | 0.050 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 0.100 | 0.100 | 0.100 | 0.100 | 0.100 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 0.150 | 0.072 | 0.150 | 0.086 | 0.200 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | unseen | unseen_tail | 64 | 0.062 | 0.023 | 0.062 | 0.031 | 0.094 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | nearby | A_nearby | 24 | 0.167 | 0.110 | 0.167 | 0.125 | 0.167 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | nearby | B_nearby | 24 | 0.167 | 0.104 | 0.135 | 0.108 | 0.167 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_return | 20 | 0.050 | 0.033 | 0.050 | 0.038 | 0.050 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.100 | 0.058 | 0.100 | 0.069 | 0.150 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.200 | 0.140 | 0.167 | 0.139 | 0.200 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 0.100 | 0.056 | 0.100 | 0.062 | 0.100 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 0.300 | 0.152 | 0.235 | 0.164 | 0.300 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | unseen | unseen_tail | 64 | 0.094 | 0.043 | 0.083 | 0.051 | 0.109 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | nearby | A_nearby | 24 | 0.125 | 0.076 | 0.092 | 0.071 | 0.208 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | nearby | B_nearby | 24 | 0.792 | 0.635 | 0.704 | 0.605 | 0.875 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_return | 20 | 0.100 | 0.100 | 0.075 | 0.082 | 0.100 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.050 | 0.050 | 0.025 | 0.032 | 0.100 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.712 | 0.792 | 0.698 | 0.950 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.727 | 0.800 | 0.710 | 0.950 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | unseen | unseen_tail | 64 | 0.172 | 0.084 | 0.094 | 0.071 | 0.188 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | nearby | A_nearby | 24 | 0.208 | 0.120 | 0.208 | 0.130 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | nearby | B_nearby | 24 | 0.208 | 0.118 | 0.188 | 0.130 | 0.208 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_return | 20 | 0.250 | 0.121 | 0.250 | 0.148 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.250 | 0.110 | 0.250 | 0.135 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.250 | 0.110 | 0.250 | 0.135 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | repeated | B_recurrent_shift_1 | 20 | 0.200 | 0.060 | 0.123 | 0.064 | 0.200 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | repeated | B_recurrent_shift_2 | 20 | 0.200 | 0.060 | 0.123 | 0.064 | 0.200 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | unseen | unseen_tail | 64 | 0.188 | 0.099 | 0.162 | 0.105 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | nearby | A_nearby | 24 | 0.208 | 0.082 | 0.208 | 0.108 | 0.208 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | nearby | B_nearby | 24 | 0.042 | 0.010 | 0.042 | 0.016 | 0.042 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_return | 20 | 0.300 | 0.128 | 0.263 | 0.151 | 0.300 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.250 | 0.103 | 0.212 | 0.120 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.250 | 0.103 | 0.210 | 0.119 | 0.250 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | repeated | B_recurrent_shift_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | repeated | B_recurrent_shift_2 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | unseen | unseen_tail | 64 | 0.094 | 0.052 | 0.074 | 0.049 | 0.125 |
| lotte_technology_search_100k | cluster_oracle | 13 | nearby | A_nearby | 24 | 0.625 | 0.390 | 0.597 | 0.450 | 0.625 |
| lotte_technology_search_100k | cluster_oracle | 13 | nearby | B_nearby | 24 | 0.833 | 0.677 | 0.746 | 0.647 | 0.917 |
| lotte_technology_search_100k | cluster_oracle | 13 | repeated | A_recurrent_return | 20 | 0.800 | 0.605 | 0.646 | 0.557 | 0.850 |
| lotte_technology_search_100k | cluster_oracle | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.600 | 0.410 | 0.461 | 0.372 | 0.650 |
| lotte_technology_search_100k | cluster_oracle | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.750 | 0.541 | 0.621 | 0.515 | 0.800 |
| lotte_technology_search_100k | cluster_oracle | 13 | repeated | B_recurrent_shift_1 | 20 | 0.750 | 0.598 | 0.658 | 0.583 | 0.800 |
| lotte_technology_search_100k | cluster_oracle | 13 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.712 | 0.792 | 0.697 | 0.950 |
| lotte_technology_search_100k | cluster_oracle | 13 | unseen | unseen_tail | 64 | 0.328 | 0.164 | 0.237 | 0.170 | 0.375 |
| lotte_technology_search_100k | cluster_oracle | 17 | nearby | A_nearby | 24 | 0.292 | 0.198 | 0.271 | 0.193 | 0.292 |
| lotte_technology_search_100k | cluster_oracle | 17 | nearby | B_nearby | 24 | 0.833 | 0.663 | 0.672 | 0.611 | 0.875 |
| lotte_technology_search_100k | cluster_oracle | 17 | repeated | A_recurrent_return | 20 | 0.450 | 0.258 | 0.425 | 0.279 | 0.450 |
| lotte_technology_search_100k | cluster_oracle | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.300 | 0.135 | 0.300 | 0.165 | 0.300 |
| lotte_technology_search_100k | cluster_oracle | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.350 | 0.158 | 0.350 | 0.198 | 0.350 |
| lotte_technology_search_100k | cluster_oracle | 17 | repeated | B_recurrent_shift_1 | 20 | 0.200 | 0.060 | 0.125 | 0.064 | 0.200 |
| lotte_technology_search_100k | cluster_oracle | 17 | repeated | B_recurrent_shift_2 | 20 | 0.550 | 0.375 | 0.481 | 0.386 | 0.550 |
| lotte_technology_search_100k | cluster_oracle | 17 | unseen | unseen_tail | 64 | 0.281 | 0.146 | 0.211 | 0.143 | 0.359 |
| lotte_technology_search_100k | cluster_oracle | 19 | nearby | A_nearby | 24 | 0.708 | 0.516 | 0.660 | 0.549 | 0.750 |
| lotte_technology_search_100k | cluster_oracle | 19 | nearby | B_nearby | 24 | 0.875 | 0.705 | 0.734 | 0.660 | 0.958 |
| lotte_technology_search_100k | cluster_oracle | 19 | repeated | A_recurrent_return | 20 | 0.800 | 0.679 | 0.702 | 0.624 | 0.900 |
| lotte_technology_search_100k | cluster_oracle | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.550 | 0.396 | 0.477 | 0.366 | 0.600 |
| lotte_technology_search_100k | cluster_oracle | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.700 | 0.546 | 0.627 | 0.514 | 0.750 |
| lotte_technology_search_100k | cluster_oracle | 19 | repeated | B_recurrent_shift_1 | 20 | 0.750 | 0.563 | 0.700 | 0.574 | 0.800 |
| lotte_technology_search_100k | cluster_oracle | 19 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.769 | 0.860 | 0.762 | 0.950 |
| lotte_technology_search_100k | cluster_oracle | 19 | unseen | unseen_tail | 64 | 0.469 | 0.237 | 0.342 | 0.238 | 0.562 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | nearby | A_nearby | 24 | 0.792 | 0.543 | 0.743 | 0.598 | 0.833 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | nearby | B_nearby | 24 | 0.875 | 0.733 | 0.703 | 0.666 | 0.958 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_return | 20 | 0.850 | 0.636 | 0.711 | 0.601 | 0.900 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.850 | 0.636 | 0.711 | 0.601 | 0.900 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.850 | 0.636 | 0.711 | 0.601 | 0.900 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.751 | 0.835 | 0.740 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.751 | 0.835 | 0.740 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | unseen | unseen_tail | 64 | 0.703 | 0.475 | 0.517 | 0.447 | 0.891 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | nearby | A_nearby | 24 | 0.708 | 0.526 | 0.681 | 0.559 | 0.750 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | nearby | B_nearby | 24 | 0.875 | 0.707 | 0.696 | 0.643 | 0.958 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.743 | 0.860 | 0.725 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.743 | 0.860 | 0.725 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.743 | 0.860 | 0.725 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.676 | 0.783 | 0.680 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.676 | 0.783 | 0.680 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | unseen | unseen_tail | 64 | 0.719 | 0.478 | 0.532 | 0.457 | 0.906 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | nearby | A_nearby | 24 | 0.792 | 0.629 | 0.743 | 0.658 | 0.833 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | nearby | B_nearby | 24 | 0.833 | 0.662 | 0.634 | 0.592 | 0.917 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.823 | 0.852 | 0.760 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.823 | 0.852 | 0.760 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.823 | 0.852 | 0.760 | 0.950 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.623 | 0.838 | 0.654 | 0.900 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.623 | 0.838 | 0.654 | 0.900 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | unseen | unseen_tail | 64 | 0.719 | 0.453 | 0.532 | 0.437 | 0.938 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | nearby | A_nearby | 24 | 0.250 | 0.130 | 0.250 | 0.150 | 0.292 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | nearby | B_nearby | 24 | 0.500 | 0.389 | 0.432 | 0.356 | 0.500 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_return | 20 | 0.200 | 0.145 | 0.175 | 0.140 | 0.250 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.150 | 0.095 | 0.150 | 0.108 | 0.200 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | repeated | B_recurrent_shift_1 | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | repeated | B_recurrent_shift_2 | 20 | 0.050 | 0.010 | 0.050 | 0.017 | 0.050 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | unseen | unseen_tail | 64 | 0.219 | 0.096 | 0.148 | 0.093 | 0.234 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | nearby | A_nearby | 24 | 0.125 | 0.074 | 0.125 | 0.077 | 0.125 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | nearby | B_nearby | 24 | 0.125 | 0.056 | 0.104 | 0.066 | 0.208 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_return | 20 | 0.250 | 0.101 | 0.250 | 0.125 | 0.250 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.150 | 0.056 | 0.150 | 0.072 | 0.150 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.150 | 0.064 | 0.150 | 0.079 | 0.150 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | repeated | B_recurrent_shift_1 | 20 | 0.150 | 0.053 | 0.150 | 0.066 | 0.150 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | repeated | B_recurrent_shift_2 | 20 | 0.200 | 0.065 | 0.167 | 0.075 | 0.200 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | unseen | unseen_tail | 64 | 0.219 | 0.132 | 0.153 | 0.115 | 0.266 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | nearby | A_nearby | 24 | 0.708 | 0.513 | 0.660 | 0.547 | 0.708 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | nearby | B_nearby | 24 | 0.292 | 0.164 | 0.271 | 0.184 | 0.292 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_return | 20 | 0.800 | 0.596 | 0.727 | 0.586 | 0.800 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.500 | 0.323 | 0.467 | 0.339 | 0.500 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.800 | 0.596 | 0.727 | 0.586 | 0.800 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | repeated | B_recurrent_shift_1 | 20 | 0.150 | 0.072 | 0.150 | 0.086 | 0.150 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | repeated | B_recurrent_shift_2 | 20 | 0.150 | 0.072 | 0.150 | 0.086 | 0.150 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | unseen | unseen_tail | 64 | 0.234 | 0.109 | 0.206 | 0.127 | 0.312 |

## Paired Comparisons

The 95% intervals bootstrap unique query-ID blocks while retaining all repeated occurrences for an ID. They describe the declared stream only.

| Dataset | Seed | Condition | Comparison | Metric | Blocks | Delta | 95% CI |
|---|---:|---|---|---|---:|---:|---|
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | -0.062 | [-0.188, 0.062] |
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | -0.072 | [-0.163, 0.003] |
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | -0.073 | [-0.188, 0.042] |
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | -0.072 | [-0.164, 0.009] |
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | -0.062 | [-0.188, 0.062] |
| lotte_science_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | -0.062 | [-0.188, 0.062] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.562 | [0.417, 0.708] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.461 | [0.328, 0.590] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.482 | [0.333, 0.628] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.432 | [0.305, 0.558] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.604 | [0.438, 0.750] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.604 | [0.458, 0.750] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | 0.625 | [0.479, 0.750] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | 0.533 | [0.408, 0.656] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | 0.555 | [0.426, 0.680] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | 0.504 | [0.381, 0.623] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | 0.667 | [0.521, 0.792] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | 0.667 | [0.521, 0.792] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.062 | [-0.146, 0.021] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.028 | [-0.124, 0.061] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.044 | [-0.125, 0.029] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.016 | [-0.096, 0.063] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.083 | [-0.188, 0.021] |
| lotte_science_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.083 | [-0.188, 0.000] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.562 | [0.417, 0.708] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.461 | [0.328, 0.590] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.482 | [0.333, 0.628] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.432 | [0.305, 0.558] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.604 | [0.438, 0.750] |
| lotte_science_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.604 | [0.458, 0.750] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | -0.046 | [-0.150, 0.075] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.020 | [-0.089, 0.060] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | -0.071 | [-0.152, 0.019] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | -0.040 | [-0.101, 0.024] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | -0.046 | [-0.150, 0.075] |
| lotte_science_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | -0.046 | [-0.150, 0.075] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.504 | [0.362, 0.642] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.413 | [0.290, 0.538] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.452 | [0.316, 0.588] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.404 | [0.283, 0.524] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.521 | [0.383, 0.654] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.504 | [0.362, 0.642] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | 0.550 | [0.375, 0.708] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | 0.433 | [0.290, 0.564] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | 0.524 | [0.386, 0.653] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | 0.444 | [0.316, 0.569] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | 0.567 | [0.400, 0.717] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | 0.550 | [0.375, 0.700] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.317 | [-0.433, -0.208] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.287 | [-0.393, -0.189] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.227 | [-0.327, -0.136] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.228 | [-0.309, -0.154] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.325 | [-0.442, -0.217] |
| lotte_science_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.317 | [-0.442, -0.200] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.562 | [0.417, 0.704] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.474 | [0.344, 0.602] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.511 | [0.369, 0.650] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.464 | [0.336, 0.589] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.571 | [0.425, 0.708] |
| lotte_science_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.562 | [0.417, 0.700] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.062 | [-0.047, 0.172] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.023 | [-0.043, 0.089] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.036 | [-0.053, 0.124] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.023 | [-0.039, 0.087] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.078 | [-0.031, 0.188] |
| lotte_science_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.062 | [-0.031, 0.172] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.297 | [0.172, 0.422] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.157 | [0.081, 0.236] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.257 | [0.148, 0.374] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.170 | [0.090, 0.252] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.312 | [0.188, 0.438] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.312 | [0.188, 0.438] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | 0.234 | [0.125, 0.359] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.134 | [0.053, 0.218] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | 0.221 | [0.109, 0.339] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.147 | [0.067, 0.232] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.234 | [0.109, 0.359] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | 0.250 | [0.125, 0.375] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.391 | [-0.547, -0.219] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.332 | [-0.466, -0.196] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.323 | [-0.463, -0.181] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.302 | [-0.422, -0.181] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.453 | [-0.609, -0.297] |
| lotte_science_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.438 | [-0.609, -0.266] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.312 | [0.188, 0.438] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.168 | [0.087, 0.251] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.250 | [0.146, 0.362] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.172 | [0.091, 0.256] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.328 | [0.203, 0.453] |
| lotte_science_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.328 | [0.203, 0.453] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.458 | [0.292, 0.625] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.382 | [0.239, 0.526] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.404 | [0.262, 0.549] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.358 | [0.235, 0.479] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.500 | [0.333, 0.667] |
| lotte_science_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.500 | [0.333, 0.646] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.458 | [0.292, 0.625] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.375 | [0.231, 0.521] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.407 | [0.250, 0.560] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.356 | [0.226, 0.484] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.500 | [0.333, 0.667] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.500 | [0.333, 0.667] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | 0.000 | [-0.083, 0.083] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | -0.007 | [-0.073, 0.066] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | 0.002 | [-0.083, 0.087] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | -0.002 | [-0.072, 0.070] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | 0.000 | [-0.083, 0.083] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | 0.000 | [-0.083, 0.083] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.167 | [-0.292, -0.042] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.132 | [-0.235, -0.033] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.120 | [-0.237, -0.008] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.113 | [-0.207, -0.025] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.167 | [-0.292, -0.042] |
| lotte_science_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.167 | [-0.292, -0.042] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.479 | [0.333, 0.625] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.369 | [0.234, 0.503] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.415 | [0.279, 0.552] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.352 | [0.237, 0.464] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.521 | [0.354, 0.667] |
| lotte_science_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.521 | [0.375, 0.667] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.604 | [0.450, 0.750] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.461 | [0.328, 0.590] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.496 | [0.351, 0.645] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.443 | [0.309, 0.577] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.617 | [0.467, 0.758] |
| lotte_science_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.617 | [0.471, 0.758] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.583 | [0.429, 0.725] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.462 | [0.328, 0.590] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.488 | [0.347, 0.634] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.442 | [0.307, 0.577] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.596 | [0.446, 0.738] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.596 | [0.450, 0.738] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | -0.021 | [-0.083, 0.025] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | 0.001 | [-0.037, 0.038] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | -0.008 | [-0.071, 0.040] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | -0.001 | [-0.044, 0.037] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | -0.021 | [-0.083, 0.029] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | -0.021 | [-0.083, 0.029] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.229 | [-0.371, -0.092] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.190 | [-0.311, -0.077] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.152 | [-0.275, -0.035] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.152 | [-0.264, -0.042] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.217 | [-0.358, -0.083] |
| lotte_science_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.217 | [-0.358, -0.083] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.521 | [0.375, 0.658] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.378 | [0.254, 0.503] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.388 | [0.259, 0.522] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.349 | [0.227, 0.469] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.521 | [0.379, 0.662] |
| lotte_science_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.521 | [0.379, 0.658] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.125 | [-0.016, 0.266] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.099 | [0.009, 0.192] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.132 | [-0.004, 0.268] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.109 | [0.017, 0.207] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.125 | [-0.016, 0.266] |
| lotte_science_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.125 | [-0.016, 0.266] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.156 | [0.016, 0.281] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.116 | [0.028, 0.203] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.143 | [0.015, 0.275] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.114 | [0.029, 0.203] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.156 | [0.016, 0.297] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.156 | [0.016, 0.297] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | 0.031 | [-0.078, 0.141] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.017 | [-0.061, 0.091] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | 0.011 | [-0.087, 0.109] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.005 | [-0.069, 0.077] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.031 | [-0.078, 0.141] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | 0.031 | [-0.078, 0.141] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.438 | [-0.578, -0.297] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.367 | [-0.478, -0.255] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.371 | [-0.498, -0.240] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.343 | [-0.450, -0.236] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.516 | [-0.641, -0.391] |
| lotte_science_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.500 | [-0.641, -0.359] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.188 | [0.047, 0.328] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.128 | [0.037, 0.223] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.161 | [0.017, 0.296] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.132 | [0.035, 0.230] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.219 | [0.078, 0.375] |
| lotte_science_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.219 | [0.062, 0.359] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.000 | [-0.104, 0.125] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.025 | [-0.069, 0.125] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | -0.011 | [-0.108, 0.086] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.009 | [-0.083, 0.099] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.000 | [-0.125, 0.104] |
| lotte_science_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.000 | [-0.125, 0.125] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | -0.021 | [-0.125, 0.083] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | -0.035 | [-0.104, 0.020] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | -0.017 | [-0.108, 0.073] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | -0.032 | [-0.103, 0.026] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | -0.021 | [-0.125, 0.083] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | -0.021 | [-0.125, 0.083] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | -0.021 | [-0.146, 0.104] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | -0.061 | [-0.146, 0.009] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | -0.006 | [-0.094, 0.087] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | -0.041 | [-0.118, 0.024] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | -0.021 | [-0.146, 0.104] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | -0.021 | [-0.146, 0.104] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.542 | [-0.688, -0.396] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.440 | [-0.563, -0.318] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.469 | [-0.602, -0.336] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.413 | [-0.525, -0.300] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.583 | [-0.729, -0.438] |
| lotte_science_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.583 | [-0.729, -0.458] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.375 | [0.208, 0.521] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.267 | [0.160, 0.381] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.338 | [0.200, 0.485] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.265 | [0.158, 0.375] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.396 | [0.229, 0.562] |
| lotte_science_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.375 | [0.208, 0.521] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | -0.021 | [-0.137, 0.104] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.004 | [-0.076, 0.067] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | -0.025 | [-0.127, 0.074] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | -0.012 | [-0.082, 0.057] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.004 | [-0.117, 0.125] |
| lotte_science_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | -0.004 | [-0.121, 0.117] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | -0.046 | [-0.121, 0.033] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.045 | [-0.106, 0.014] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | -0.082 | [-0.158, -0.006] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | -0.060 | [-0.118, -0.004] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | -0.021 | [-0.104, 0.067] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | -0.021 | [-0.104, 0.067] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | -0.025 | [-0.150, 0.108] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | -0.041 | [-0.110, 0.030] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | -0.057 | [-0.144, 0.030] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | -0.048 | [-0.112, 0.016] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | -0.025 | [-0.150, 0.104] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | -0.017 | [-0.146, 0.113] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.696 | [-0.833, -0.546] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.599 | [-0.724, -0.467] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.586 | [-0.724, -0.443] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.549 | [-0.676, -0.421] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.696 | [-0.829, -0.554] |
| lotte_science_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.696 | [-0.829, -0.550] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.325 | [0.167, 0.483] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.236 | [0.110, 0.365] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.270 | [0.129, 0.417] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.236 | [0.115, 0.367] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.333 | [0.183, 0.483] |
| lotte_science_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.333 | [0.175, 0.487] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.109 | [-0.031, 0.250] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.024 | [-0.050, 0.092] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.089 | [-0.025, 0.197] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.035 | [-0.040, 0.104] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.109 | [-0.031, 0.250] |
| lotte_science_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.094 | [-0.047, 0.234] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.094 | [-0.031, 0.219] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.052 | [-0.024, 0.129] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.083 | [-0.027, 0.195] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.054 | [-0.020, 0.130] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.109 | [-0.031, 0.250] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.078 | [-0.062, 0.203] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | -0.016 | [-0.141, 0.109] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.028 | [-0.036, 0.098] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | -0.005 | [-0.109, 0.104] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.020 | [-0.050, 0.094] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.000 | [-0.125, 0.125] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | -0.016 | [-0.141, 0.094] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.594 | [-0.734, -0.453] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.451 | [-0.559, -0.340] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.496 | [-0.619, -0.361] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.424 | [-0.525, -0.320] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.641 | [-0.781, -0.500] |
| lotte_science_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.656 | [-0.781, -0.516] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.203 | [0.078, 0.328] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.083 | [0.015, 0.149] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.177 | [0.073, 0.287] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.094 | [0.025, 0.164] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.203 | [0.078, 0.344] |
| lotte_science_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.188 | [0.062, 0.312] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.292 | [0.104, 0.479] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.293 | [0.155, 0.432] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.231 | [0.044, 0.413] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.255 | [0.117, 0.395] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.375 | [0.188, 0.562] |
| lotte_technology_search_100k | 13 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.333 | [0.146, 0.521] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.208 | [0.021, 0.396] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.197 | [0.071, 0.325] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.174 | [0.000, 0.346] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.170 | [0.048, 0.301] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.229 | [0.042, 0.417] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.208 | [0.021, 0.375] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | -0.083 | [-0.229, 0.062] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | -0.097 | [-0.198, 0.003] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | -0.057 | [-0.199, 0.083] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | -0.085 | [-0.188, 0.018] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | -0.146 | [-0.312, 0.021] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | -0.125 | [-0.292, 0.042] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.458 | [-0.625, -0.292] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.378 | [-0.502, -0.249] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.382 | [-0.536, -0.229] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.379 | [-0.507, -0.251] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.500 | [-0.667, -0.333] |
| lotte_technology_search_100k | 13 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.500 | [-0.646, -0.333] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.562 | [0.417, 0.708] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.471 | [0.352, 0.590] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.505 | [0.343, 0.658] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.465 | [0.347, 0.588] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.604 | [0.438, 0.750] |
| lotte_technology_search_100k | 13 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.604 | [0.458, 0.750] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.275 | [0.117, 0.433] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.274 | [0.143, 0.410] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.249 | [0.101, 0.402] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.252 | [0.126, 0.387] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.308 | [0.146, 0.467] |
| lotte_technology_search_100k | 13 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.308 | [0.142, 0.471] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | -0.129 | [-0.242, -0.017] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.068 | [-0.152, 0.009] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | -0.099 | [-0.204, 0.001] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | -0.073 | [-0.159, 0.005] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | -0.113 | [-0.233, 0.008] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | -0.113 | [-0.237, 0.004] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | -0.404 | [-0.571, -0.233] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | -0.342 | [-0.497, -0.204] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | -0.348 | [-0.504, -0.192] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | -0.325 | [-0.474, -0.189] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | -0.421 | [-0.592, -0.250] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | -0.421 | [-0.592, -0.246] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.829 | [-0.942, -0.688] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.651 | [-0.775, -0.518] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.706 | [-0.840, -0.558] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.624 | [-0.745, -0.493] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.838 | [-0.942, -0.704] |
| lotte_technology_search_100k | 13 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.812 | [-0.933, -0.683] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.571 | [0.433, 0.704] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.476 | [0.347, 0.600] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.484 | [0.351, 0.618] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.442 | [0.322, 0.561] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.621 | [0.483, 0.750] |
| lotte_technology_search_100k | 13 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.596 | [0.458, 0.729] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.047 | [-0.078, 0.172] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.018 | [-0.056, 0.093] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | -0.011 | [-0.102, 0.085] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | -0.001 | [-0.075, 0.073] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.031 | [-0.094, 0.156] |
| lotte_technology_search_100k | 13 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.031 | [-0.109, 0.156] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.094 | [-0.047, 0.234] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.030 | [-0.047, 0.106] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.043 | [-0.064, 0.152] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.022 | [-0.054, 0.101] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.078 | [-0.062, 0.219] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.078 | [-0.062, 0.219] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | 0.047 | [-0.016, 0.109] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.011 | [-0.020, 0.044] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | 0.054 | [0.009, 0.113] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.022 | [-0.003, 0.055] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.047 | [-0.016, 0.109] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | 0.047 | [-0.016, 0.109] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.484 | [-0.625, -0.344] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.380 | [-0.484, -0.272] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.370 | [-0.491, -0.248] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.353 | [-0.454, -0.255] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.656 | [-0.781, -0.531] |
| lotte_technology_search_100k | 13 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.594 | [-0.719, -0.469] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.203 | [0.078, 0.328] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.098 | [0.018, 0.182] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.132 | [0.028, 0.241] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.098 | [0.014, 0.183] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.219 | [0.078, 0.359] |
| lotte_technology_search_100k | 13 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.219 | [0.062, 0.359] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.083 | [-0.062, 0.229] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.038 | [-0.059, 0.133] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.083 | [-0.052, 0.219] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.040 | [-0.058, 0.142] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.104 | [-0.021, 0.250] |
| lotte_technology_search_100k | 17 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.104 | [-0.021, 0.250] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.000 | [-0.125, 0.125] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | -0.017 | [-0.112, 0.075] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.000 | [-0.125, 0.125] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | -0.018 | [-0.119, 0.076] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.042 | [-0.104, 0.188] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.042 | [-0.104, 0.188] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | -0.083 | [-0.188, 0.000] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | -0.054 | [-0.120, -0.001] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | -0.083 | [-0.188, 0.000] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | -0.058 | [-0.132, -0.001] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | -0.062 | [-0.167, 0.042] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | -0.062 | [-0.167, 0.042] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.667 | [-0.792, -0.521] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.551 | [-0.663, -0.437] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.574 | [-0.712, -0.427] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.529 | [-0.647, -0.408] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.688 | [-0.812, -0.542] |
| lotte_technology_search_100k | 17 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.667 | [-0.812, -0.521] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.438 | [0.271, 0.604] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.349 | [0.208, 0.487] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.357 | [0.200, 0.514] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.312 | [0.177, 0.443] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.458 | [0.292, 0.625] |
| lotte_technology_search_100k | 17 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.458 | [0.271, 0.625] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.113 | [-0.021, 0.250] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.018 | [-0.063, 0.097] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.080 | [-0.042, 0.208] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.026 | [-0.062, 0.110] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.100 | [-0.025, 0.229] |
| lotte_technology_search_100k | 17 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.100 | [-0.029, 0.229] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.067 | [-0.050, 0.183] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.003 | [-0.077, 0.063] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.064 | [-0.054, 0.185] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.006 | [-0.074, 0.079] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.054 | [-0.050, 0.163] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.054 | [-0.058, 0.167] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | -0.046 | [-0.104, 0.000] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | -0.020 | [-0.055, 0.001] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | -0.016 | [-0.075, 0.049] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | -0.020 | [-0.056, 0.008] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | -0.046 | [-0.104, 0.000] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | -0.046 | [-0.100, 0.000] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.746 | [-0.867, -0.617] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.643 | [-0.759, -0.519] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.651 | [-0.788, -0.498] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.621 | [-0.739, -0.499] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.771 | [-0.887, -0.642] |
| lotte_technology_search_100k | 17 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.771 | [-0.892, -0.642] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.258 | [0.133, 0.392] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.131 | [0.060, 0.212] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.224 | [0.108, 0.349] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.144 | [0.062, 0.225] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.246 | [0.129, 0.371] |
| lotte_technology_search_100k | 17 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.246 | [0.125, 0.371] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.125 | [0.031, 0.234] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.077 | [0.020, 0.141] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.099 | [0.006, 0.194] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.075 | [0.015, 0.141] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.156 | [0.031, 0.281] |
| lotte_technology_search_100k | 17 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.125 | [0.016, 0.250] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.156 | [0.031, 0.281] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.110 | [0.040, 0.186] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.090 | [-0.006, 0.192] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.084 | [0.016, 0.156] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.172 | [0.047, 0.297] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.141 | [0.016, 0.266] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | 0.031 | [-0.078, 0.141] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.033 | [-0.031, 0.101] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | -0.009 | [-0.099, 0.077] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.010 | [-0.053, 0.070] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.016 | [-0.078, 0.109] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | 0.016 | [-0.094, 0.125] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.500 | [-0.641, -0.359] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.346 | [-0.449, -0.235] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.379 | [-0.502, -0.254] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.342 | [-0.446, -0.240] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.641 | [-0.766, -0.516] |
| lotte_technology_search_100k | 17 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.641 | [-0.766, -0.516] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.219 | [0.094, 0.344] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.124 | [0.051, 0.201] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.148 | [0.033, 0.260] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.112 | [0.038, 0.193] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.266 | [0.125, 0.406] |
| lotte_technology_search_100k | 17 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.219 | [0.078, 0.359] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 48 | -0.042 | [-0.167, 0.083] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | -0.061 | [-0.144, 0.013] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | -0.026 | [-0.151, 0.094] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | -0.054 | [-0.143, 0.028] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | -0.042 | [-0.167, 0.083] |
| lotte_technology_search_100k | 19 | nearby | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 48 | -0.042 | [-0.167, 0.083] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.333 | [0.188, 0.479] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.232 | [0.124, 0.347] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.314 | [0.177, 0.455] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.249 | [0.138, 0.366] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.333 | [0.167, 0.500] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.333 | [0.188, 0.500] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 48 | 0.375 | [0.249, 0.521] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 48 | 0.293 | [0.189, 0.402] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 48 | 0.340 | [0.201, 0.486] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 48 | 0.303 | [0.192, 0.422] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 48 | 0.375 | [0.250, 0.521] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 48 | 0.375 | [0.229, 0.521] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 48 | -0.312 | [-0.458, -0.167] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 48 | -0.307 | [-0.431, -0.189] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 48 | -0.223 | [-0.355, -0.102] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 48 | -0.260 | [-0.375, -0.154] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 48 | -0.375 | [-0.521, -0.229] |
| lotte_technology_search_100k | 19 | nearby | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 48 | -0.354 | [-0.500, -0.208] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 48 | 0.625 | [0.479, 0.750] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 48 | 0.503 | [0.395, 0.615] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 48 | 0.546 | [0.416, 0.680] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 48 | 0.488 | [0.376, 0.597] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 48 | 0.688 | [0.562, 0.812] |
| lotte_technology_search_100k | 19 | nearby | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 48 | 0.688 | [0.562, 0.812] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 40 | -0.025 | [-0.158, 0.117] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | -0.035 | [-0.118, 0.042] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | -0.022 | [-0.154, 0.116] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | -0.032 | [-0.121, 0.056] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | -0.033 | [-0.171, 0.100] |
| lotte_technology_search_100k | 19 | repeated | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 40 | -0.033 | [-0.171, 0.108] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.267 | [0.087, 0.442] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.198 | [0.072, 0.326] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.258 | [0.089, 0.425] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.197 | [0.068, 0.323] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.258 | [0.083, 0.429] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.258 | [0.079, 0.429] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 40 | 0.292 | [0.167, 0.425] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 40 | 0.233 | [0.135, 0.337] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 40 | 0.281 | [0.151, 0.419] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 40 | 0.230 | [0.129, 0.335] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 40 | 0.292 | [0.158, 0.425] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 40 | 0.292 | [0.167, 0.433] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 40 | -0.500 | [-0.658, -0.333] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 40 | -0.434 | [-0.574, -0.292] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 40 | -0.450 | [-0.602, -0.289] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 40 | -0.412 | [-0.546, -0.272] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 40 | -0.500 | [-0.658, -0.342] |
| lotte_technology_search_100k | 19 | repeated | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 40 | -0.500 | [-0.658, -0.333] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 40 | 0.608 | [0.475, 0.742] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 40 | 0.513 | [0.380, 0.640] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 40 | 0.554 | [0.414, 0.687] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 40 | 0.487 | [0.364, 0.610] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 40 | 0.646 | [0.512, 0.767] |
| lotte_technology_search_100k | 19 | repeated | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 40 | 0.637 | [0.504, 0.762] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.000 | [-0.094, 0.094] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.008 | [-0.033, 0.054] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | -0.009 | [-0.082, 0.063] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | -0.002 | [-0.042, 0.040] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.016 | [-0.078, 0.125] |
| lotte_technology_search_100k | 19 | unseen | cluster_equal_noisy_minus_cluster_cold_no_feedback | route_true_reward | 64 | -0.016 | [-0.109, 0.078] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.141 | [0.031, 0.250] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.066 | [-0.007, 0.140] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.123 | [0.011, 0.237] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.077 | [-0.002, 0.156] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.203 | [0.078, 0.344] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.141 | [0.016, 0.266] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | hit_at_10 | 64 | 0.141 | [0.016, 0.266] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | evidence_recall_at_10 | 64 | 0.058 | [-0.013, 0.127] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | mrr_at_10 | 64 | 0.132 | [0.030, 0.237] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | ndcg_at_10 | 64 | 0.079 | [0.010, 0.150] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | selected_cluster_hit | 64 | 0.188 | [0.062, 0.312] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_equal_noisy | route_true_reward | 64 | 0.156 | [0.031, 0.281] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | hit_at_10 | 64 | -0.484 | [-0.609, -0.359] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | evidence_recall_at_10 | 64 | -0.343 | [-0.442, -0.247] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | mrr_at_10 | 64 | -0.326 | [-0.440, -0.211] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | ndcg_at_10 | 64 | -0.310 | [-0.410, -0.215] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | selected_cluster_hit | 64 | -0.625 | [-0.750, -0.500] |
| lotte_technology_search_100k | 19 | unseen | cluster_trust_weighted_minus_cluster_static_nearest | route_true_reward | 64 | -0.609 | [-0.734, -0.484] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | hit_at_10 | 64 | 0.375 | [0.250, 0.500] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | evidence_recall_at_10 | 64 | 0.194 | [0.118, 0.275] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | mrr_at_10 | 64 | 0.258 | [0.152, 0.368] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | ndcg_at_10 | 64 | 0.187 | [0.111, 0.268] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | selected_cluster_hit | 64 | 0.453 | [0.312, 0.594] |
| lotte_technology_search_100k | 19 | unseen | cluster_oracle_minus_cluster_cold_no_feedback | route_true_reward | 64 | 0.406 | [0.266, 0.547] |

## Shift and Recovery Diagnostics

| Dataset | Method | Seed | B-shift cluster-hit delta | B-shift Hit@10 delta |
|---|---|---:|---:|---:|
| lotte_science_search_100k | cluster_static_nearest | 13 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 17 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 19 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | 0.050 | 0.050 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | 0.050 | 0.050 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | 0.050 | 0.100 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | 0.050 | 0.050 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | 0.000 | 0.050 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | -0.050 | -0.050 |
| lotte_science_search_100k | cluster_oracle | 13 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_oracle | 17 | 0.000 | 0.000 |
| lotte_science_search_100k | cluster_oracle | 19 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | -0.100 | -0.100 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | 0.100 | 0.050 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | 0.200 | 0.200 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | 0.050 | 0.050 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | 0.050 | 0.050 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | 0.000 | 0.000 |
| lotte_technology_search_100k | cluster_oracle | 13 | 0.150 | 0.150 |
| lotte_technology_search_100k | cluster_oracle | 17 | 0.350 | 0.350 |
| lotte_technology_search_100k | cluster_oracle | 19 | 0.150 | 0.200 |

| Dataset | Method | Seed | Affected repeated queries | Recovery rate |
|---|---|---:|---:|---:|
| lotte_science_search_100k | cluster_static_nearest | 13 | 2 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 17 | 4 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 19 | 7 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | 36 | 0.222 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | 38 | 0.132 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | 34 | 0.294 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | 37 | 0.027 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | 14 | 0.214 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | 38 | 0.316 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | 23 | 0.565 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | 15 | 0.267 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | 37 | 0.135 |
| lotte_science_search_100k | cluster_oracle | 13 | 18 | 0.500 |
| lotte_science_search_100k | cluster_oracle | 17 | 24 | 0.542 |
| lotte_science_search_100k | cluster_oracle | 19 | 20 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 13 | 4 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | 3 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | 3 | 0.000 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | 33 | 0.212 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | 36 | 0.139 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | 36 | 0.194 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | 22 | 0.091 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | 31 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | 35 | 0.029 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | 40 | 0.125 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | 34 | 0.088 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | 27 | 0.222 |
| lotte_technology_search_100k | cluster_oracle | 13 | 13 | 0.538 |
| lotte_technology_search_100k | cluster_oracle | 17 | 30 | 0.333 |
| lotte_technology_search_100k | cluster_oracle | 19 | 14 | 0.643 |

## Controller Update Audit

| Dataset | Method | Seed | Feedback-induced policy updates | Total update weight |
|---|---|---:|---:|---:|
| lotte_technology_search_100k | cluster_static_nearest | 13 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 17 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_static_nearest | 19 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 13 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 17 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_cold_no_feedback | 19 | 0 | 0.000 |
| lotte_technology_search_100k | cluster_equal_noisy | 13 | 2544 | 747.256 |
| lotte_technology_search_100k | cluster_equal_noisy | 17 | 2544 | 747.853 |
| lotte_technology_search_100k | cluster_equal_noisy | 19 | 2544 | 752.778 |
| lotte_technology_search_100k | cluster_trust_weighted | 13 | 2544 | 582.708 |
| lotte_technology_search_100k | cluster_trust_weighted | 17 | 2544 | 588.628 |
| lotte_technology_search_100k | cluster_trust_weighted | 19 | 2544 | 560.463 |
| lotte_technology_search_100k | cluster_oracle | 13 | 2544 | 741.697 |
| lotte_technology_search_100k | cluster_oracle | 17 | 2544 | 742.010 |
| lotte_technology_search_100k | cluster_oracle | 19 | 2544 | 742.323 |
| lotte_science_search_100k | cluster_static_nearest | 13 | 0 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 17 | 0 | 0.000 |
| lotte_science_search_100k | cluster_static_nearest | 19 | 0 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 13 | 0 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 17 | 0 | 0.000 |
| lotte_science_search_100k | cluster_cold_no_feedback | 19 | 0 | 0.000 |
| lotte_science_search_100k | cluster_equal_noisy | 13 | 2544 | 748.495 |
| lotte_science_search_100k | cluster_equal_noisy | 17 | 2544 | 745.017 |
| lotte_science_search_100k | cluster_equal_noisy | 19 | 2544 | 744.950 |
| lotte_science_search_100k | cluster_trust_weighted | 13 | 2544 | 576.775 |
| lotte_science_search_100k | cluster_trust_weighted | 17 | 2544 | 586.998 |
| lotte_science_search_100k | cluster_trust_weighted | 19 | 2544 | 563.969 |
| lotte_science_search_100k | cluster_oracle | 13 | 2544 | 740.938 |
| lotte_science_search_100k | cluster_oracle | 17 | 2544 | 745.421 |
| lotte_science_search_100k | cluster_oracle | 19 | 2544 | 740.598 |

Interpretation must keep this mechanism result separate from Task72: a positive cluster-only result does not establish an end-to-end full-fusion gain, while a negative result does not revise the already reported Task72 boundary.
