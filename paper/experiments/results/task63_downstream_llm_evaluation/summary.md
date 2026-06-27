# Task63 Downstream LLM Evaluation Summary

Status: formal LLM execution artifact.

| method_label | answer_count | judgment_count | correct_rate | faithful_rate | strict_citation_support_rate | insufficient_context_rate | avg_context_tokens | context_tokens_per_correct | estimated_context_cost_per_correct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bge_dense_top10 | 300 | 300 | 0.9167 | 0.9433 | 0.3567 | 0.07667 | 1698 | 1852 | 0 |
| bge_intentweight_positive_seed19 | 300 | 300 | 0.9167 | 0.92 | 0.37 | 0.07667 | 1596 | 1741 | 0 |
| dense_sent_mmr_r0.85_l0.70 | 300 | 300 | 0.89 | 0.91 | 0.07333 | 0.08 | 1240 | 1393 | 0 |
| e5_dense_top10 | 300 | 300 | 0.9167 | 0.93 | 0.41 | 0.07 | 1525 | 1663 | 0 |
| e5_intentweight_full_seed19 | 300 | 300 | 0.92 | 0.9333 | 0.3633 | 0.05667 | 1341 | 1458 | 0 |
| intentweight_sent_mmr_r0.85_l0.70_seed19 | 300 | 300 | 0.9133 | 0.9267 | 0.08333 | 0.09 | 1157 | 1267 | 0 |
| minilm_dense_top10 | 300 | 300 | 0.92 | 0.9533 | 0.3533 | 0.09667 | 1461 | 1588 | 0 |
