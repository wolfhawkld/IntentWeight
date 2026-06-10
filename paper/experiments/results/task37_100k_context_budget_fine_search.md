# Task37 Context Budget Search

| run_id | policy | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_chunks@10 | avg_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense:token_budget_r0.95_m5 | token_budget_r0.95_m5 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1264.9765 | 0.8591 | -0.0134 |
| dense:token_budget_r0.95_m6 | token_budget_r0.95_m6 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8893 | 1264.9966 | 0.8591 | -0.0134 |
| dense:token_budget_r0.95_m7 | token_budget_r0.95_m7 |  | 0.8540 | 0.6863 | 0.7067 | 0.6406 | 8.8876 | 1266.6309 | 0.8603 | -0.0134 |
| dense:token_budget_r0.95_m8 | token_budget_r0.95_m8 |  | 0.8557 | 0.6871 | 0.7069 | 0.6410 | 8.8725 | 1281.4631 | 0.8703 | -0.0117 |
| dense:token_budget_r0.96_m5 | token_budget_r0.96_m5 |  | 0.8574 | 0.6895 | 0.7071 | 0.6420 | 8.9346 | 1287.6644 | 0.8745 | -0.0101 |
| dense:token_budget_r0.96_m6 | token_budget_r0.96_m6 |  | 0.8574 | 0.6895 | 0.7071 | 0.6420 | 8.9362 | 1287.6846 | 0.8746 | -0.0101 |
| dense:token_budget_r0.96_m7 | token_budget_r0.96_m7 |  | 0.8574 | 0.6895 | 0.7071 | 0.6420 | 8.9346 | 1289.2852 | 0.8756 | -0.0101 |
| dense:token_budget_r0.96_m8 | token_budget_r0.96_m8 |  | 0.8574 | 0.6895 | 0.7071 | 0.6420 | 8.9262 | 1298.6728 | 0.8820 | -0.0101 |
| dense:token_budget_r0.97_m5 | token_budget_r0.97_m5 |  | 0.8574 | 0.6897 | 0.7071 | 0.6423 | 8.9648 | 1309.1930 | 0.8892 | -0.0101 |
| dense:token_budget_r0.97_m6 | token_budget_r0.97_m6 |  | 0.8574 | 0.6897 | 0.7071 | 0.6423 | 8.9648 | 1309.1930 | 0.8892 | -0.0101 |
| dense:token_budget_r0.97_m7 | token_budget_r0.97_m7 |  | 0.8574 | 0.6897 | 0.7071 | 0.6423 | 8.9614 | 1310.7685 | 0.8902 | -0.0101 |
| dense:token_budget_r0.97_m8 | token_budget_r0.97_m8 |  | 0.8574 | 0.6897 | 0.7071 | 0.6423 | 8.9614 | 1312.6309 | 0.8915 | -0.0101 |
| dense:token_budget_r0.98_m5 | token_budget_r0.98_m5 |  | 0.8574 | 0.6895 | 0.7071 | 0.6422 | 8.9933 | 1320.1997 | 0.8966 | -0.0101 |
| dense:token_budget_r0.98_m6 | token_budget_r0.98_m6 |  | 0.8574 | 0.6895 | 0.7071 | 0.6422 | 8.9933 | 1320.1997 | 0.8966 | -0.0101 |
| dense:token_budget_r0.98_m7 | token_budget_r0.98_m7 |  | 0.8574 | 0.6895 | 0.7071 | 0.6422 | 8.9899 | 1321.7752 | 0.8977 | -0.0101 |
| dense:token_budget_r0.98_m8 | token_budget_r0.98_m8 |  | 0.8574 | 0.6895 | 0.7071 | 0.6422 | 8.9899 | 1322.0621 | 0.8979 | -0.0101 |
| dense:token_budget_r0.99_m5 | token_budget_r0.99_m5 |  | 0.8574 | 0.6904 | 0.7071 | 0.6426 | 8.9983 | 1329.5151 | 0.9030 | -0.0101 |
| dense:token_budget_r0.99_m6 | token_budget_r0.99_m6 |  | 0.8574 | 0.6904 | 0.7071 | 0.6426 | 8.9983 | 1329.5151 | 0.9030 | -0.0101 |
| dense:token_budget_r0.99_m7 | token_budget_r0.99_m7 |  | 0.8574 | 0.6904 | 0.7071 | 0.6426 | 8.9983 | 1329.5151 | 0.9030 | -0.0101 |
| dense:token_budget_r0.99_m8 | token_budget_r0.99_m8 |  | 0.8574 | 0.6904 | 0.7071 | 0.6426 | 8.9983 | 1329.5906 | 0.9030 | -0.0101 |
| dense |  |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 10.0000 | 1472.3876 | 1.0000 | 0.0000 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m5 | token_budget_r0.95_m5 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m6 | token_budget_r0.95_m6 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m7 | token_budget_r0.95_m7 | 13 | 0.8658 | 0.6710 | 0.7006 | 0.6189 | 8.9161 | 1355.8188 | 0.9208 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.95_m8 | token_budget_r0.95_m8 | 13 | 0.8658 | 0.6711 | 0.7006 | 0.6190 | 8.8993 | 1359.8020 | 0.9235 | -0.0017 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.96_m5 | token_budget_r0.96_m5 | 13 | 0.8641 | 0.6709 | 0.7004 | 0.6189 | 8.9513 | 1368.5621 | 0.9295 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.96_m6 | token_budget_r0.96_m6 | 13 | 0.8641 | 0.6709 | 0.7004 | 0.6189 | 8.9513 | 1368.5621 | 0.9295 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.96_m7 | token_budget_r0.96_m7 | 13 | 0.8641 | 0.6709 | 0.7004 | 0.6189 | 8.9513 | 1368.5621 | 0.9295 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.96_m8 | token_budget_r0.96_m8 | 13 | 0.8641 | 0.6711 | 0.7004 | 0.6190 | 8.9413 | 1371.1829 | 0.9313 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.97_m5 | token_budget_r0.97_m5 | 13 | 0.8641 | 0.6714 | 0.7004 | 0.6192 | 8.9899 | 1380.5168 | 0.9376 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.97_m6 | token_budget_r0.97_m6 | 13 | 0.8641 | 0.6714 | 0.7004 | 0.6192 | 8.9899 | 1380.5168 | 0.9376 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.97_m7 | token_budget_r0.97_m7 | 13 | 0.8641 | 0.6714 | 0.7004 | 0.6192 | 8.9899 | 1380.5168 | 0.9376 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.97_m8 | token_budget_r0.97_m8 | 13 | 0.8641 | 0.6716 | 0.7004 | 0.6193 | 8.9815 | 1383.0570 | 0.9393 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.98_m5 | token_budget_r0.98_m5 | 13 | 0.8641 | 0.6715 | 0.7004 | 0.6193 | 8.9966 | 1389.0906 | 0.9434 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.98_m6 | token_budget_r0.98_m6 | 13 | 0.8641 | 0.6715 | 0.7004 | 0.6193 | 8.9966 | 1389.0906 | 0.9434 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.98_m7 | token_budget_r0.98_m7 | 13 | 0.8641 | 0.6715 | 0.7004 | 0.6193 | 8.9966 | 1389.0906 | 0.9434 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.98_m8 | token_budget_r0.98_m8 | 13 | 0.8641 | 0.6715 | 0.7004 | 0.6193 | 8.9933 | 1390.8876 | 0.9446 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.99_m5 | token_budget_r0.99_m5 | 13 | 0.8641 | 0.6722 | 0.7004 | 0.6196 | 9.0000 | 1408.0000 | 0.9563 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.99_m6 | token_budget_r0.99_m6 | 13 | 0.8641 | 0.6722 | 0.7004 | 0.6196 | 9.0000 | 1408.0000 | 0.9563 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.99_m7 | token_budget_r0.99_m7 | 13 | 0.8641 | 0.6722 | 0.7004 | 0.6196 | 9.0000 | 1408.0000 | 0.9563 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13:token_budget_r0.99_m8 | token_budget_r0.99_m8 | 13 | 0.8641 | 0.6722 | 0.7004 | 0.6196 | 8.9983 | 1409.6091 | 0.9574 | -0.0034 |
| gated_fixed:gated_cost_aware:seed13 |  | 13 | 0.8775 | 0.6892 | 0.7017 | 0.6265 | 10.0000 | 1548.3742 | 1.0516 | 0.0101 |

## Notes

- Policies keep a safe prefix and then prune tail chunks by per-query token budget.
- Policy decisions use only ranking order and chunk token lengths, not ground-truth labels.
- This is a final-context policy search; it does not claim lower dense embedding compute.
