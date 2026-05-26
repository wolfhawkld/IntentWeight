# Final Context Token Cost

| run_id | seed | hit@10 | evidence_recall@10 | mrr@10 | ndcg@10 | avg_context_tokens@10 | median_context_tokens@10 | p95_context_tokens@10 | context_token_ratio_vs_baseline@10 | hit_delta_vs_baseline@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense |  | 0.8674 | 0.7026 | 0.7081 | 0.6487 | 1472.3876 | 1312.0000 | 2908.2500 | 1.0000 | 0.0000 |
| none:gated_cost_aware:seed13 | 13 | 0.8809 | 0.7255 | 0.7103 | 0.6567 | 1572.0151 | 1421.5000 | 3049.5000 | 1.0677 | 0.0134 |
| none:gated_cost_aware:seed17 | 17 | 0.8876 | 0.7272 | 0.7111 | 0.6573 | 1560.3893 | 1384.5000 | 3011.0000 | 1.0598 | 0.0201 |
| none:gated_cost_aware:seed19 | 19 | 0.8792 | 0.7209 | 0.7103 | 0.6557 | 1551.0537 | 1374.0000 | 3012.2500 | 1.0534 | 0.0117 |
| oracle:gated_cost_aware:seed13 | 13 | 0.8775 | 0.6790 | 0.7112 | 0.6277 | 1334.5688 | 1168.0000 | 2756.0000 | 0.9064 | 0.0101 |
| oracle:gated_cost_aware:seed17 | 17 | 0.8708 | 0.6739 | 0.7185 | 0.6287 | 1320.1074 | 1163.5000 | 2651.2500 | 0.8966 | 0.0034 |
| oracle:gated_cost_aware:seed19 | 19 | 0.8792 | 0.6774 | 0.7152 | 0.6261 | 1326.4178 | 1185.0000 | 2634.5000 | 0.9009 | 0.0117 |
| equal_default:gated_cost_aware:seed13 | 13 | 0.8658 | 0.6707 | 0.7079 | 0.6217 | 1428.8423 | 1259.5000 | 2755.7500 | 0.9704 | -0.0017 |
| equal_default:gated_cost_aware:seed17 | 17 | 0.8658 | 0.6568 | 0.7047 | 0.6141 | 1408.4480 | 1235.5000 | 2768.0000 | 0.9566 | -0.0017 |
| equal_default:gated_cost_aware:seed19 | 19 | 0.8607 | 0.6538 | 0.6980 | 0.6070 | 1434.2164 | 1292.0000 | 2738.0000 | 0.9741 | -0.0067 |
| trust_default:gated_cost_aware:seed13 | 13 | 0.8607 | 0.6646 | 0.7008 | 0.6151 | 1393.7047 | 1214.5000 | 2711.5000 | 0.9466 | -0.0067 |
| trust_default:gated_cost_aware:seed17 | 17 | 0.8641 | 0.6653 | 0.7118 | 0.6239 | 1390.3607 | 1243.0000 | 2689.2500 | 0.9443 | -0.0034 |
| trust_default:gated_cost_aware:seed19 | 19 | 0.8674 | 0.6683 | 0.7156 | 0.6244 | 1414.4664 | 1241.0000 | 2889.0000 | 0.9607 | 0.0000 |
| trust_mild:gated_cost_aware:seed13 | 13 | 0.8725 | 0.6798 | 0.7097 | 0.6303 | 1359.0436 | 1174.0000 | 2749.5000 | 0.9230 | 0.0050 |
| trust_mild:gated_cost_aware:seed17 | 17 | 0.8809 | 0.6857 | 0.7135 | 0.6315 | 1377.3121 | 1221.5000 | 2655.5000 | 0.9354 | 0.0134 |
| trust_mild:gated_cost_aware:seed19 | 19 | 0.8792 | 0.6731 | 0.7159 | 0.6250 | 1351.6762 | 1204.0000 | 2693.0000 | 0.9180 | 0.0117 |
| trust_strong:gated_cost_aware:seed13 | 13 | 0.8490 | 0.6463 | 0.6969 | 0.6082 | 1464.9312 | 1287.0000 | 2985.5000 | 0.9949 | -0.0185 |
| trust_strong:gated_cost_aware:seed17 | 17 | 0.8473 | 0.6343 | 0.6957 | 0.6003 | 1433.6376 | 1242.5000 | 2933.0000 | 0.9737 | -0.0201 |
| trust_strong:gated_cost_aware:seed19 | 19 | 0.8473 | 0.6257 | 0.6902 | 0.5890 | 1446.7299 | 1271.5000 | 2841.2500 | 0.9826 | -0.0201 |

## Notes

- Token metrics count final top-k retrieved chunk text only.
- They do not include system prompt, instructions, generated output, or reranker internals.
- Earlier `avg_source_candidate_cost` metrics are retrieval-stage candidate-count proxies, not token costs.
