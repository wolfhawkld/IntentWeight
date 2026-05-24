# Task28.1 Historical Context Token Backfill

| dataset | task | source_label | method | runs | hit@10_mean | avg_context_tokens@10_mean | context_token_ratio_vs_baseline@10_mean | context_token_saving_pct@10 | hit_delta_vs_baseline@10_mean | avg_source_candidate_cost_mean_mean | dense_query_rate_mean_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | baseline | banking77:dense | banking77:dense | 1 | 0.9805 | 121.0880 | 1.0000 | 0.0000 | 0.0000 |  |  |
| banking77 | task16 | linucb_cost_banking77_heldout-test_test_corpus-full_q3080 | full_multi_route | 3 | 0.9844 | 121.4937 | 1.0034 | -0.3351 | 0.0039 | 300.0000 | 1.0000 |
| banking77 | task16 | linucb_cost_banking77_heldout-test_test_corpus-full_q3080 | gated_cost_aware | 3 | 0.9813 | 120.8180 | 0.9978 | 0.2230 | 0.0008 | 142.5108 | 1.0000 |
| cuad | baseline | cuad:dense | cuad:dense | 1 | 0.0029 | 14.9669 | 1.0000 | 0.0000 | 0.0000 |  |  |
| cuad | task16 | linucb_cost_cuad_smoke-only_test_corpus-gt-anchored-10000_q100 | full_multi_route | 3 | 0.0034 | 17.0242 | 1.1375 | -13.7452 | 0.0005 | 300.0000 | 1.0000 |
| cuad | task16 | linucb_cost_cuad_smoke-only_test_corpus-gt-anchored-10000_q100 | gated_cost_aware | 3 | 0.0024 | 18.0175 | 1.2038 | -20.3822 | -0.0005 | 203.4667 | 1.0000 |
| emanual | baseline | emanual:dense | emanual:dense | 1 | 0.0324 | 18.2357 | 1.0000 | 0.0000 | 0.0000 |  |  |
| emanual | task16 | linucb_cost_emanual_heldout-test_test_corpus-full_q132 | full_multi_route | 3 | 0.0149 | 18.7378 | 1.0275 | -2.7531 | -0.0175 | 300.0000 | 1.0000 |
| emanual | task16 | linucb_cost_emanual_heldout-test_test_corpus-full_q132 | gated_cost_aware | 3 | 0.0116 | 17.9237 | 0.9829 | 1.7110 | -0.0208 | 214.0741 | 1.0000 |
| lotte_technology_search | baseline | lotte_technology_search:dense | lotte_technology_search:dense | 1 | 0.9000 | 1115.2000 | 1.0000 | 0.0000 | 0.0000 |  |  |
| lotte_technology_search | task18 | linucb_cost_lotte-technology-search_heldout-test_test_corpus-full_q20 | full_multi_route | 1 | 1.0000 | 1235.6500 | 1.1080 | -10.8008 | 0.1000 | 150.0000 | 1.0000 |
| lotte_technology_search | task18 | linucb_cost_lotte-technology-search_heldout-test_test_corpus-full_q20 | gated_cost_aware | 1 | 0.9500 | 1207.1000 | 1.0824 | -8.2407 | 0.0500 | 129.5000 | 0.9500 |
| lotte_technology_search_100k | baseline | lotte_technology_search_100k:dense | lotte_technology_search_100k:dense | 1 | 0.8674 | 1472.3876 | 1.0000 | 0.0000 | 0.0000 |  |  |
| lotte_technology_search_100k | task18 | linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596 | full_multi_route | 3 | 0.8826 | 1558.0872 | 1.0582 | -5.8205 | 0.0151 | 300.0000 | 1.0000 |
| lotte_technology_search_100k | task18 | linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596 | gated_cost_aware | 3 | 0.8440 | 1473.7209 | 1.0009 | -0.0906 | -0.0235 | 191.6816 | 0.8220 |
| lotte_technology_search_100k | task19_ablation_A | task19_ablation_A | gated_cost_aware | 3 | 0.8378 | 1474.5721 | 1.0015 | -0.1484 | -0.0296 | 199.5582 | 0.8249 |
| lotte_technology_search_100k | task19_ablation_B | task19_ablation_B | gated_cost_aware | 3 | 0.8479 | 1502.0117 | 1.0201 | -2.0120 | -0.0196 | 205.9601 | 0.8138 |
| lotte_technology_search_100k | task19_ablation_C | task19_ablation_C | gated_cost_aware | 3 | 0.8496 | 1482.9161 | 1.0072 | -0.7151 | -0.0179 | 198.7696 | 0.8276 |
| lotte_technology_search_100k | task19_ablation_D | task19_ablation_D | gated_cost_aware | 3 | 0.8770 | 1518.4396 | 1.0313 | -3.1277 | 0.0095 | 229.9720 | 0.9029 |
| lotte_technology_search_100k | task19_ablation_E | task19_ablation_E | gated_cost_aware | 3 | 0.8865 | 1549.8345 | 1.0526 | -5.2600 | 0.0190 | 258.8386 | 0.9489 |
| lotte_technology_search_100k | task20_conditional_H | task20_conditional_H | gated_cost_aware | 3 | 0.8669 | 1514.8445 | 1.0288 | -2.8835 | -0.0006 | 237.5391 | 0.9053 |
| lotte_technology_search_100k | task20_conditional_L | task20_conditional_L | gated_cost_aware | 3 | 0.7383 | 1455.9810 | 0.9889 | 1.1143 | -0.1292 | 143.2159 | 0.5405 |
| lotte_technology_search_100k | task20_conditional_M | task20_conditional_M | gated_cost_aware | 3 | 0.8624 | 1508.3758 | 1.0244 | -2.4442 | -0.0050 | 225.4866 | 0.8689 |
| lotte_technology_search_100k | task20_conditional_S | task20_conditional_S | gated_cost_aware | 3 | 0.8747 | 1516.2444 | 1.0298 | -2.9786 | 0.0073 | 227.2875 | 0.8945 |
| lotte_technology_search_100k | task25_100k_cluster_credit_formal | task25_100k_cluster_credit_formal | gated_cost_aware | 3 | 0.8764 | 1550.6516 | 1.0532 | -5.3154 | 0.0089 | 181.4723 | 0.6708 |
| lotte_technology_search_100k | task25_100k_cluster_credit_value_conf | task25_100k_cluster_credit_value_conf | gated_cost_aware | 1 | 0.8758 | 1550.4849 | 1.0530 | -5.3041 | 0.0084 | 176.2940 | 0.6422 |
| lotte_technology_search_100k | task25_100k_old_credit | task25_100k_old_credit | gated_cost_aware | 1 | 0.8809 | 1509.8104 | 1.0254 | -2.5416 | 0.0134 | 189.4631 | 0.7267 |
| lotte_technology_search_100k | task25_100k_old_credit_formal | task25_100k_old_credit_formal | gated_cost_aware | 3 | 0.8826 | 1529.6963 | 1.0389 | -3.8922 | 0.0151 | 193.9178 | 0.7466 |
| lotte_technology_search_100k | task25_100k_route_credit | task25_100k_route_credit | gated_cost_aware | 1 | 0.8792 | 1555.7836 | 1.0566 | -5.6640 | 0.0117 | 299.2764 | 1.0000 |
| lotte_technology_search_200k | baseline | lotte_technology_search_200k:dense | lotte_technology_search_200k:dense | 1 | 0.7970 | 1444.1242 | 1.0000 | 0.0000 | 0.0000 |  |  |
| lotte_technology_search_200k | task22_200k_formal | task22_200k_formal | full_multi_route | 3 | 0.8300 | 1558.1801 | 1.0790 | -7.8979 | 0.0330 | 300.0000 | 1.0000 |
| lotte_technology_search_200k | task22_200k_formal | task22_200k_formal | gated_cost_aware | 3 | 0.8154 | 1549.3881 | 1.0729 | -7.2891 | 0.0185 | 232.0078 | 0.9027 |
| lotte_technology_search_200k | task22_200k_smoke | task22_200k_smoke | full_multi_route | 1 | 0.8289 | 1579.7332 | 1.0939 | -9.3904 | 0.0319 | 300.0000 | 1.0000 |
| lotte_technology_search_200k | task22_200k_smoke | task22_200k_smoke | gated_cost_aware | 1 | 0.8104 | 1554.1510 | 1.0762 | -7.6189 | 0.0134 | 251.8792 | 0.9480 |
| lotte_technology_search_400k | baseline | lotte_technology_search_400k:dense | lotte_technology_search_400k:dense | 1 | 0.7718 | 1482.2987 | 1.0000 | 0.0000 | 0.0000 |  |  |
| lotte_technology_search_400k | task22_4_lotte_400k_linucb_smoke | task22_4_lotte_400k_linucb_smoke | full_multi_route | 1 | 0.8087 | 1569.2265 | 1.0586 | -5.8644 | 0.0369 | 300.0000 | 1.0000 |
| lotte_technology_search_400k | task22_4_lotte_400k_linucb_smoke | task22_4_lotte_400k_linucb_smoke | gated_cost_aware | 1 | 0.7768 | 1532.6426 | 1.0340 | -3.3963 | 0.0050 | 247.7013 | 0.9094 |
| lotte_technology_search_400k | task22_5_lotte_400k_linucb_formal | task22_5_lotte_400k_linucb_formal | full_multi_route | 3 | 0.8003 | 1571.0134 | 1.0598 | -5.9849 | 0.0285 | 300.0000 | 1.0000 |
| lotte_technology_search_400k | task22_5_lotte_400k_linucb_formal | task22_5_lotte_400k_linucb_formal | gated_cost_aware | 3 | 0.7836 | 1547.6577 | 1.0441 | -4.4093 | 0.0117 | 233.2159 | 0.9141 |
| lotte_technology_search_638k | baseline | lotte_technology_search_638k:dense | lotte_technology_search_638k:dense | 1 | 0.7282 | 1525.6191 | 1.0000 | 0.0000 | 0.0000 |  |  |
| lotte_technology_search_638k | task22_9_lotte_638k_linucb_formal | task22_9_lotte_638k_linucb_formal | full_multi_route | 3 | 0.7612 | 1613.2768 | 1.0575 | -5.7457 | 0.0330 | 300.0000 | 1.0000 |
| lotte_technology_search_638k | task22_9_lotte_638k_linucb_formal | task22_9_lotte_638k_linucb_formal | gated_cost_aware | 3 | 0.7343 | 1599.9452 | 1.0487 | -4.8719 | 0.0062 | 236.2248 | 0.9146 |
| lotte_technology_search_638k | task22_9_lotte_638k_linucb_smoke | task22_9_lotte_638k_linucb_smoke | full_multi_route | 1 | 0.7584 | 1633.5369 | 1.0707 | -7.0737 | 0.0302 | 300.0000 | 1.0000 |
| lotte_technology_search_638k | task22_9_lotte_638k_linucb_smoke | task22_9_lotte_638k_linucb_smoke | gated_cost_aware | 1 | 0.7399 | 1618.4396 | 1.0608 | -6.0841 | 0.0117 | 247.1980 | 0.9346 |
| lotte_technology_search_638k | task24_online_baselines_638k | task24_online_baselines_638k | epsilon_greedy_ensemble | 3 | 0.7578 | 1625.1247 | 1.0652 | -6.5223 | 0.0296 | 300.0000 | 1.0000 |
| lotte_technology_search_638k | task24_online_baselines_638k | task24_online_baselines_638k | uniform_random_ensemble | 3 | 0.7634 | 1638.0515 | 1.0737 | -7.3696 | 0.0352 | 300.0000 | 1.0000 |
| lotte_technology_search_638k | task24_static_ensemble_638k | task24_static_ensemble_638k | static_nearest_ensemble | 3 | 0.7612 | 1627.4418 | 1.0667 | -6.6742 | 0.0330 | 300.0000 | 1.0000 |
| lotte_technology_search_638k | task24_static_gated_638k | task24_static_gated_638k | static_nearest_gated | 3 | 0.7500 | 1613.6823 | 1.0577 | -5.7723 | 0.0218 | 223.4899 | 0.9972 |

## Notes

- `avg_source_candidate_cost*` columns are retrieval-stage candidate-count proxies.
- `avg_context_tokens@k` columns are final retrieved context token measurements.
- Token metrics count retrieved chunk text only, not prompts, generated output, or reranker internals.
- Dense-only rankings are included as the baseline for each dataset/scale.
