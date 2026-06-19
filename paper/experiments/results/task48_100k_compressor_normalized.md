# Task48 Compressor-Normalized Comparison

- Scale: `100k`
- Evaluation split: `test`
- Dense candidate depth: `10`
- Budget ratios: `0.95,0.90,0.85`
- MMR lambda: `0.70`
- Sentence unit cap: `128` tokens

## Main Table

| source_group | compressor | budget_ratio | hit@10 | hit_delta_vs_dense@10 | hit_delta_vs_source@10 | evidence_recall@10 | avg_context_tokens@10 | context_token_saving_percent_vs_dense@10 | context_token_saving_percent_vs_source@10 | avg_selected_sentences@10 | avg_supported_chunks@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | none |  | 0.8705 | 0 | 0 | 0.7081 | 1470 | 0 | 0 | 0 | 10 |
| dense | sent_mmr | 0.85 | 0.8705 | 0 | 0 | 0.7081 | 1247 | 15.16 | 15.16 | 49.36 | 10 |
| dense | sent_mmr | 0.9 | 0.8705 | 0 | 0 | 0.7081 | 1320 | 10.22 | 10.22 | 53.04 | 10 |
| dense | sent_mmr | 0.95 | 0.8705 | 0 | 0 | 0.7081 | 1392 | 5.325 | 5.325 | 56.75 | 10 |
| intentweight | none |  | 0.8681 | -0.002398 | 0 | 0.6824 | 1376 | 6.426 | 0 | 0 | 8.909 |
| intentweight | sent_mmr | 0.85 | 0.8681 | -0.002398 | 0 | 0.6824 | 1167 | 20.65 | 15.2 | 45.65 | 8.906 |
| intentweight | sent_mmr | 0.9 | 0.8681 | -0.002398 | 0 | 0.6824 | 1234 | 16.04 | 10.28 | 49.05 | 8.906 |
| intentweight | sent_mmr | 0.95 | 0.8681 | -0.002398 | 0 | 0.6824 | 1302 | 11.46 | 5.375 | 52.36 | 8.909 |
| intentweight | none |  | 0.8657 | -0.004796 | 0 | 0.6766 | 1365 | 7.137 | 0 | 0 | 8.89 |
| intentweight | sent_mmr | 0.85 | 0.8657 | -0.004796 | 0 | 0.6766 | 1158 | 21.24 | 15.18 | 45.52 | 8.887 |
| intentweight | sent_mmr | 0.9 | 0.8657 | -0.004796 | 0 | 0.6766 | 1225 | 16.68 | 10.28 | 48.83 | 8.89 |
| intentweight | sent_mmr | 0.95 | 0.8657 | -0.004796 | 0 | 0.6766 | 1292 | 12.14 | 5.389 | 52.24 | 8.89 |
| intentweight | none |  | 0.8777 | 0.007194 | 0 | 0.6871 | 1397 | 4.98 | 0 | 0 | 8.902 |
| intentweight | sent_mmr | 0.85 | 0.8777 | 0.007194 | 0 | 0.6871 | 1185 | 19.41 | 15.18 | 46.51 | 8.899 |
| intentweight | sent_mmr | 0.9 | 0.8777 | 0.007194 | 0 | 0.6871 | 1254 | 14.72 | 10.25 | 49.84 | 8.902 |
| intentweight | sent_mmr | 0.95 | 0.8777 | 0.007194 | 0 | 0.6871 | 1322 | 10.07 | 5.359 | 53.41 | 8.902 |

## Paired Comparisons

| comparison | method_label | source_group | budget_ratio | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vs_dense | dense_top10_sent_mmr | dense | 0.85 | 0.8705 | 0 | 0 | 0 | True | 0.8484 | 15.16 | 1 |
| vs_dense | dense_top10_sent_mmr | dense | 0.9 | 0.8705 | 0 | 0 | 0 | True | 0.8978 | 10.22 | 1 |
| vs_dense | dense_top10_sent_mmr | dense | 0.95 | 0.8705 | 0 | 0 | 0 | True | 0.9467 | 5.325 | 1 |
| vs_dense | intentweight | intentweight |  | 0.8681 | -0.002398 | -0.02398 | 0.01679 | False | 0.9357 | 6.426 | 1 |
| vs_dense | intentweight | intentweight |  | 0.8657 | -0.004796 | -0.02398 | 0.01199 | False | 0.9286 | 7.137 | 0.8036 |
| vs_dense | intentweight | intentweight |  | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.9502 | 4.98 | 0.69 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.85 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.7935 | 20.65 | 1 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.85 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.7876 | 21.24 | 0.8036 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.85 | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.8059 | 19.41 | 0.69 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.9 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.8396 | 16.04 | 1 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.9 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.8332 | 16.68 | 0.8036 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.9 | 0.8777 | 0.007194 | -0.01679 | 0.02878 | False | 0.8528 | 14.72 | 0.69 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.95 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.8854 | 11.46 | 1 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.95 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.8786 | 12.14 | 0.8036 |
| vs_dense | intentweight_sent_mmr | intentweight | 0.95 | 0.8777 | 0.007194 | -0.01445 | 0.03118 | False | 0.8993 | 10.07 | 0.69 |
| vs_source | dense_top10_sent_mmr | dense | 0.85 | 0.8705 | 0 | 0 | 0 | True | 0.8484 | 15.16 | 1 |
| vs_source | dense_top10_sent_mmr | dense | 0.9 | 0.8705 | 0 | 0 | 0 | True | 0.8978 | 10.22 | 1 |
| vs_source | dense_top10_sent_mmr | dense | 0.95 | 0.8705 | 0 | 0 | 0 | True | 0.9467 | 5.325 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.85 | 0.8681 | 0 | 0 | 0 | True | 0.848 | 15.2 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.85 | 0.8657 | 0 | 0 | 0 | True | 0.8482 | 15.18 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.85 | 0.8777 | 0 | 0 | 0 | True | 0.8482 | 15.18 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.9 | 0.8681 | 0 | 0 | 0 | True | 0.8972 | 10.28 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.9 | 0.8657 | 0 | 0 | 0 | True | 0.8972 | 10.28 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.9 | 0.8777 | 0 | 0 | 0 | True | 0.8975 | 10.25 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.95 | 0.8681 | 0 | 0 | 0 | True | 0.9462 | 5.375 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.95 | 0.8657 | 0 | 0 | 0 | True | 0.9461 | 5.389 | 1 |
| vs_source | intentweight_sent_mmr | intentweight | 0.95 | 0.8777 | 0 | 0 | 0 | True | 0.9464 | 5.359 | 1 |

## Notes

- The same sentence-level MMR compressor is applied after each evidence pool is produced.
- `vs_source` compares a compressed row against its own uncompressed evidence pool.
- `vs_dense` compares every row against uncompressed dense top-10.
- Hit and evidence-recall metrics remain chunk-support proxies; they do not prove sentence-level answer sufficiency.
