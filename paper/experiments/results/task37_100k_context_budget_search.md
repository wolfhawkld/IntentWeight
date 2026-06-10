# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.75_m5 | token_budget_r0.75_m5 |  | 0.8356 | 0.6538 | 0.7043 | 0.6236 | 7.5034 | 1025.6879 | 0.6966 | -0.0319 |
| dense:token_budget_r0.75_m6 | token_budget_r0.75_m6 |  | 0.8372 | 0.6558 | 0.7045 | 0.6247 | 7.4715 | 1050.9329 | 0.7138 | -0.0302 |
| dense:token_budget_r0.80_m5 | token_budget_r0.80_m5 |  | 0.8406 | 0.6616 | 0.7050 | 0.6281 | 7.9027 | 1079.8809 | 0.7334 | -0.0268 |
| dense:token_budget_r0.80_m6 | token_budget_r0.80_m6 |  | 0.8406 | 0.6623 | 0.7050 | 0.6284 | 7.8490 | 1095.2047 | 0.7438 | -0.0268 |
| dense:token_budget_r0.75_m7 | token_budget_r0.75_m7 |  | 0.8456 | 0.6657 | 0.7057 | 0.6293 | 7.5772 | 1106.1544 | 0.7513 | -0.0218 |
| dense:token_budget_r0.80_m7 | token_budget_r0.80_m7 |  | 0.8456 | 0.6700 | 0.7057 | 0.6315 | 7.8440 | 1133.4782 | 0.7698 | -0.0218 |
| dense:token_budget_r0.85_m5 | token_budget_r0.85_m5 |  | 0.8507 | 0.6722 | 0.7062 | 0.6331 | 8.2768 | 1137.1762 | 0.7723 | -0.0168 |
| dense:token_budget_r0.85_m6 | token_budget_r0.85_m6 |  | 0.8507 | 0.6721 | 0.7062 | 0.6331 | 8.2332 | 1146.9044 | 0.7789 | -0.0168 |
| dense:token_budget_r0.85_m7 | token_budget_r0.85_m7 |  | 0.8540 | 0.6758 | 0.7067 | 0.6344 | 8.1695 | 1169.0268 | 0.7940 | -0.0134 |
| dense:token_budget_r0.75_m8 | token_budget_r0.75_m8 |  | 0.8490 | 0.6758 | 0.7062 | 0.6349 | 8.0940 | 1201.9211 | 0.8163 | -0.0185 |
| dense:token_budget_r0.90_m5 | token_budget_r0.90_m5 |  | 0.8540 | 0.6811 | 0.7067 | 0.6378 | 8.5906 | 1211.0302 | 0.8225 | -0.0134 |
| dense:token_budget_r0.90_m6 | token_budget_r0.90_m6 |  | 0.8540 | 0.6811 | 0.7067 | 0.6378 | 8.5856 | 1211.6997 | 0.8229 | -0.0134 |
| dense:token_budget_r0.80_m8 | token_budget_r0.80_m8 |  | 0.8490 | 0.6765 | 0.7062 | 0.6354 | 8.1812 | 1211.8725 | 0.8231 | -0.0185 |
| dense:token_budget_r0.90_m7 | token_budget_r0.90_m7 |  | 0.8540 | 0.6811 | 0.7067 | 0.6378 | 8.5604 | 1216.8423 | 0.8264 | -0.0134 |
| dense:token_budget_r0.85_m8 | token_budget_r0.85_m8 |  | 0.8540 | 0.6793 | 0.7067 | 0.6367 | 8.3272 | 1226.8121 | 0.8332 | -0.0134 |
| dense:token_budget_r0.90_m8 | token_budget_r0.90_m8 |  | 0.8557 | 0.6819 | 0.7069 | 0.6382 | 8.5822 | 1250.6443 | 0.8494 | -0.0117 |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1264.9765 | 0.8591 | -0.0134 |
| dense:token_budget_r0.95_m6 | token_budget_r0.95_m6 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8893 | 1264.9966 | 0.8591 | -0.0134 |
| dense:token_budget_r0.95_m7 | token_budget_r0.95_m7 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1266.6309 | 0.8603 | -0.0134 |
| dense:token_budget_r0.95_m8 | token_budget_r0.95_m8 |  | 0.8557 | 0.6871 | 0.7069 | 0.6410 | 8.8725 | 1281.4631 | 0.8703 | -0.0117 |
| dense |  |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 10.0000 | 1472.3876 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.75_m5 | token_budget_r0.75_m5 | 13 | 0.8456 | 0.6397 | 0.6982 | 0.6034 | 7.4849 | 1091.3909 | 0.7412 | -0.0218 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.75_m6 | token_budget_r0.75_m6 | 13 | 0.8440 | 0.6391 | 0.6979 | 0.6034 | 7.4211 | 1115.1812 | 0.7574 | -0.0235 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.80_m5 | token_budget_r0.80_m5 | 13 | 0.8507 | 0.6449 | 0.6988 | 0.6063 | 7.8591 | 1151.7685 | 0.7822 | -0.0168 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.80_m6 | token_budget_r0.80_m6 | 13 | 0.8507 | 0.6431 | 0.6988 | 0.6054 | 7.7953 | 1163.8389 | 0.7904 | -0.0168 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.75_m7 | token_budget_r0.75_m7 | 13 | 0.8490 | 0.6464 | 0.6986 | 0.6068 | 7.5436 | 1172.1711 | 0.7961 | -0.0185 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.80_m7 | token_budget_r0.80_m7 | 13 | 0.8540 | 0.6501 | 0.6993 | 0.6086 | 7.8020 | 1201.0302 | 0.8157 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.85_m5 | token_budget_r0.85_m5 | 13 | 0.8540 | 0.6554 | 0.6992 | 0.6110 | 8.2265 | 1219.9497 | 0.8286 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.85_m6 | token_budget_r0.85_m6 | 13 | 0.8540 | 0.6549 | 0.6992 | 0.6108 | 8.2047 | 1222.2030 | 0.8301 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.85_m7 | token_budget_r0.85_m7 | 13 | 0.8540 | 0.6560 | 0.6992 | 0.6114 | 8.1711 | 1240.7617 | 0.8427 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.75_m8 | token_budget_r0.75_m8 | 13 | 0.8540 | 0.6609 | 0.6993 | 0.6142 | 8.1007 | 1272.0822 | 0.8640 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.80_m8 | token_budget_r0.80_m8 | 13 | 0.8540 | 0.6611 | 0.6993 | 0.6143 | 8.1560 | 1278.1225 | 0.8681 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.90_m5 | token_budget_r0.90_m5 | 13 | 0.8540 | 0.6606 | 0.6992 | 0.6141 | 8.6007 | 1284.5017 | 0.8724 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.90_m6 | token_budget_r0.90_m6 | 13 | 0.8540 | 0.6606 | 0.6992 | 0.6141 | 8.6023 | 1284.6242 | 0.8725 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.90_m7 | token_budget_r0.90_m7 | 13 | 0.8540 | 0.6612 | 0.6992 | 0.6145 | 8.5940 | 1291.7919 | 0.8773 | -0.0134 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.85_m8 | token_budget_r0.85_m8 | 13 | 0.8557 | 0.6630 | 0.6995 | 0.6150 | 8.3171 | 1292.9161 | 0.8781 | -0.0117 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.90_m8 | token_budget_r0.90_m8 | 13 | 0.8557 | 0.6635 | 0.6995 | 0.6159 | 8.5570 | 1318.0034 | 0.8951 | -0.0117 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m6 | token_budget_r0.95_m6 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m7 | token_budget_r0.95_m7 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m8 | token_budget_r0.95_m8 | 13 | 0.8658 | 0.6711 | 0.7006 | 0.6190 | 8.8993 | 1359.8020 | 0.9235 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.8775 | 0.6892 | 0.7017 | 0.6265 | 10.0000 | 1548.3742 | 1.0516 | 0.0101 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
