# Task62 Prompt-Compression Baseline

- Scale: `100k`
- Evaluation split: `test`
- Dense candidate depth: `10`
- Budget ratios: `0.95,0.90,0.85,0.75`
- Prompt compressor: `selective_context_lite`
- Sentence unit cap: `128` tokens

## Main Table

| source_group | compressor | budget_ratio | hit@10 | hit_delta_vs_dense@10 | hit_delta_vs_source@10 | evidence_recall@10 | avg_context_tokens@10 | context_token_saving_percent_vs_dense@10 | context_token_saving_percent_vs_source@10 | avg_selected_sentences@10 | avg_supported_chunks@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dense | none |  | 0.8705 | 0 | 0 | 0.7081 | 1470 | 0 | 0 | 0 | 10 |
| dense | selective_context_lite | 0.75 | 0.8705 | 0 | 0 | 0.7081 | 1100 | 25.19 | 25.19 | 44.6 | 9.998 |
| dense | selective_context_lite | 0.85 | 0.8705 | 0 | 0 | 0.7081 | 1245 | 15.31 | 15.31 | 51.61 | 10 |
| dense | selective_context_lite | 0.9 | 0.8705 | 0 | 0 | 0.7081 | 1317 | 10.42 | 10.42 | 54.99 | 10 |
| dense | selective_context_lite | 0.95 | 0.8705 | 0 | 0 | 0.7081 | 1387 | 5.662 | 5.662 | 58.1 | 10 |
| intentweight | none |  | 0.8681 | -0.002398 | 0 | 0.6824 | 1376 | 6.426 | 0 | 0 | 8.909 |
| intentweight | selective_context_lite | 0.75 | 0.8681 | -0.002398 | 0 | 0.6824 | 1029 | 30.01 | 25.2 | 40.64 | 8.904 |
| intentweight | selective_context_lite | 0.85 | 0.8681 | -0.002398 | 0 | 0.6824 | 1165 | 20.78 | 15.33 | 47.27 | 8.904 |
| intentweight | selective_context_lite | 0.9 | 0.8681 | -0.002398 | 0 | 0.6824 | 1231 | 16.23 | 10.48 | 50.47 | 8.906 |
| intentweight | selective_context_lite | 0.95 | 0.8681 | -0.002398 | 0 | 0.6824 | 1298 | 11.69 | 5.62 | 53.46 | 8.909 |
| intentweight | none |  | 0.8657 | -0.004796 | 0 | 0.6766 | 1365 | 7.137 | 0 | 0 | 8.89 |
| intentweight | selective_context_lite | 0.75 | 0.8657 | -0.004796 | 0 | 0.6766 | 1021 | 30.57 | 25.23 | 40.82 | 8.89 |
| intentweight | selective_context_lite | 0.85 | 0.8657 | -0.004796 | 0 | 0.6766 | 1156 | 21.4 | 15.35 | 47.53 | 8.89 |
| intentweight | selective_context_lite | 0.9 | 0.8657 | -0.004796 | 0 | 0.6766 | 1222 | 16.87 | 10.48 | 50.49 | 8.89 |
| intentweight | selective_context_lite | 0.95 | 0.8657 | -0.004796 | 0 | 0.6766 | 1288 | 12.42 | 5.689 | 53.36 | 8.89 |
| intentweight | none |  | 0.8777 | 0.007194 | 0 | 0.6871 | 1397 | 4.98 | 0 | 0 | 8.902 |
| intentweight | selective_context_lite | 0.75 | 0.8777 | 0.007194 | 0 | 0.6871 | 1045 | 28.95 | 25.23 | 41.79 | 8.899 |
| intentweight | selective_context_lite | 0.85 | 0.8777 | 0.007194 | 0 | 0.6871 | 1183 | 19.53 | 15.31 | 48.52 | 8.902 |
| intentweight | selective_context_lite | 0.9 | 0.8777 | 0.007194 | 0 | 0.6871 | 1251 | 14.92 | 10.46 | 51.64 | 8.902 |
| intentweight | selective_context_lite | 0.95 | 0.8777 | 0.007194 | 0 | 0.6871 | 1317 | 10.38 | 5.686 | 54.61 | 8.902 |

## Paired Comparisons

| comparison | method_label | source_group | compressor | budget_ratio | method_hit@10 | hit_delta_mean | hit_delta_ci_low | hit_delta_ci_high | noninferior_by_ci | token_ratio | token_saving_percent | mcnemar_p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vs_dense | dense_top10_selective_context | dense | selective_context_lite | 0.75 | 0.8705 | 0 | 0 | 0 | True | 0.7481 | 25.19 | 1 |
| vs_dense | dense_top10_selective_context | dense | selective_context_lite | 0.85 | 0.8705 | 0 | 0 | 0 | True | 0.8469 | 15.31 | 1 |
| vs_dense | dense_top10_selective_context | dense | selective_context_lite | 0.9 | 0.8705 | 0 | 0 | 0 | True | 0.8958 | 10.42 | 1 |
| vs_dense | dense_top10_selective_context | dense | selective_context_lite | 0.95 | 0.8705 | 0 | 0 | 0 | True | 0.9434 | 5.662 | 1 |
| vs_dense | intentweight | intentweight | none |  | 0.8681 | -0.002398 | -0.02398 | 0.01679 | False | 0.9357 | 6.426 | 1 |
| vs_dense | intentweight | intentweight | none |  | 0.8657 | -0.004796 | -0.02398 | 0.01199 | False | 0.9286 | 7.137 | 0.8036 |
| vs_dense | intentweight | intentweight | none |  | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.9502 | 4.98 | 0.69 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.6999 | 30.01 | 1 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.6943 | 30.57 | 0.8036 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.7105 | 28.95 | 0.69 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8681 | -0.002398 | -0.02398 | 0.02158 | False | 0.7922 | 20.78 | 1 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.786 | 21.4 | 0.8036 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.8047 | 19.53 | 0.69 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.8377 | 16.23 | 1 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.8313 | 16.87 | 0.8036 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8777 | 0.007194 | -0.01679 | 0.03118 | False | 0.8508 | 14.92 | 0.69 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8681 | -0.002398 | -0.02398 | 0.01918 | False | 0.8831 | 11.69 | 1 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8657 | -0.004796 | -0.02398 | 0.01439 | False | 0.8758 | 12.42 | 0.8036 |
| vs_dense | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8777 | 0.007194 | -0.01445 | 0.03118 | False | 0.8962 | 10.38 | 0.69 |
| vs_source | dense_top10_selective_context | dense | selective_context_lite | 0.75 | 0.8705 | 0 | 0 | 0 | True | 0.7481 | 25.19 | 1 |
| vs_source | dense_top10_selective_context | dense | selective_context_lite | 0.85 | 0.8705 | 0 | 0 | 0 | True | 0.8469 | 15.31 | 1 |
| vs_source | dense_top10_selective_context | dense | selective_context_lite | 0.9 | 0.8705 | 0 | 0 | 0 | True | 0.8958 | 10.42 | 1 |
| vs_source | dense_top10_selective_context | dense | selective_context_lite | 0.95 | 0.8705 | 0 | 0 | 0 | True | 0.9434 | 5.662 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8681 | 0 | 0 | 0 | True | 0.748 | 25.2 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8657 | 0 | 0 | 0 | True | 0.7477 | 25.23 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.75 | 0.8777 | 0 | 0 | 0 | True | 0.7477 | 25.23 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8681 | 0 | 0 | 0 | True | 0.8467 | 15.33 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8657 | 0 | 0 | 0 | True | 0.8465 | 15.35 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.85 | 0.8777 | 0 | 0 | 0 | True | 0.8469 | 15.31 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8681 | 0 | 0 | 0 | True | 0.8952 | 10.48 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8657 | 0 | 0 | 0 | True | 0.8952 | 10.48 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.9 | 0.8777 | 0 | 0 | 0 | True | 0.8954 | 10.46 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8681 | 0 | 0 | 0 | True | 0.9438 | 5.62 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8657 | 0 | 0 | 0 | True | 0.9431 | 5.689 | 1 |
| vs_source | intentweight_selective_context | intentweight | selective_context_lite | 0.95 | 0.8777 | 0 | 0 | 0 | True | 0.9431 | 5.686 | 1 |

## SentMMR Reference From Task48

| Compressor | Ratio | Hit@10 | Token saving vs dense |
| --- | ---: | ---: | ---: |
| SentMMR | 0.85 | 0.8705 | 15.16% |
| SentMMR | 0.9 | 0.8705 | 10.22% |
| SentMMR | 0.95 | 0.8705 | 5.33% |
| SelectiveContext-lite | 0.75 | 0.8705 | 25.19% |
| SelectiveContext-lite | 0.85 | 0.8705 | 15.31% |
| SelectiveContext-lite | 0.9 | 0.8705 | 10.42% |
| SelectiveContext-lite | 0.95 | 0.8705 | 5.66% |

## Notes

- This is a local Selective Context-style prompt-pruning baseline, not LLMLingua.
- The compressor is applied after each evidence pool is produced, so it is downstream of retrieval.
- `vs_source` compares a compressed row against its own uncompressed evidence pool.
- `vs_dense` compares every row against uncompressed dense top-10.
- Hit and evidence-recall metrics remain chunk-support proxies; answer-level sufficiency still requires downstream generation evaluation.
