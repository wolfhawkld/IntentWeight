# Task63 Downstream LLM Evaluation Preflight

Status: preflight only. No answer generation or LLM judging has been executed in this artifact.

This file is not paper-facing answer-level evidence. It only verifies the frozen-test sample, method contexts, retrieval support, and context-token cost before the LLM run.

## Sample

- Frozen test queries: `417`
- Eligible common frozen-test queries: `417`
- Selected queries: `300`
- Credential status: `{'provider': 'deepseek', 'has_key': True, 'has_base_url': True}`

## Preflight Retrieval/Token Checks

| method_label | num_queries | hit@10 | hit_delta_vs_baseline@10 | evidence_recall@10 | avg_context_tokens@10 | context_token_saving_percent_vs_baseline@10 | avg_selected_sentences@10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bge_dense_top10 | 300 | 0.9 | 0.03 | 0.7447 | 1698 | -16.16 | 0 |
| bge_intentweight_positive_seed19 | 300 | 0.9133 | 0.04333 | 0.7504 | 1596 | -9.19 | 0 |
| dense_sent_mmr_r0.85_l0.70 | 300 | 0.87 | 0 | 0.7097 | 1240 | 15.16 | 49.27 |
| e5_dense_top10 | 300 | 0.8733 | 0.003333 | 0.7161 | 1525 | -4.323 | 0 |
| e5_intentweight_full_seed19 | 300 | 0.87 | 0 | 0.7084 | 1341 | 8.234 | 0 |
| intentweight_sent_mmr_r0.85_l0.70_seed19 | 300 | 0.8767 | 0.006667 | 0.6925 | 1157 | 20.8 | 45.72 |
| minilm_dense_top10 | 300 | 0.87 | 0 | 0.7097 | 1461 | 0 | 0 |

## Execution Requirement

To complete Task63, run the same script with `--execute` after configuring a valid LLM provider API key. The formal summary is generated only after `answers.jsonl` and `judgments.jsonl` exist.
