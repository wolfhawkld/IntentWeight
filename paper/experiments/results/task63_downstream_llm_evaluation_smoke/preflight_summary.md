# Task63 Downstream LLM Evaluation Preflight

Status: preflight only. No answer generation or LLM judging has been executed in this artifact.

This file is not paper-facing answer-level evidence. It only verifies the frozen-test sample, method contexts, retrieval support, and context-token cost before the LLM run.

## Sample

- Frozen test queries: `417`
- Eligible common frozen-test queries: `417`
- Selected queries: `1`
- Credential status: `{'provider': 'deepseek', 'has_key': True, 'has_base_url': True}`

## Preflight Retrieval/Token Checks

| method_label | num_queries | hit@10 | hit_delta_vs_baseline@10 | evidence_recall@10 | avg_context_tokens@10 | context_token_saving_percent_vs_baseline@10 | avg_selected_sentences@10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bge_dense_top10 | 1 | 1 | 1 | 0.5 | 1394 | -31.88 | 0 |
| bge_intentweight_positive_seed19 | 1 | 1 | 1 | 0.5 | 1310 | -23.94 | 0 |
| dense_sent_mmr_r0.85_l0.70 | 1 | 0 | 0 | 0 | 896 | 15.23 | 41 |
| e5_dense_top10 | 1 | 0 | 0 | 0 | 556 | 47.4 | 0 |
| e5_intentweight_full_seed19 | 1 | 0 | 0 | 0 | 445 | 57.9 | 0 |
| intentweight_sent_mmr_r0.85_l0.70_seed19 | 1 | 0 | 0 | 0 | 561 | 46.93 | 26 |
| minilm_dense_top10 | 1 | 0 | 0 | 0 | 1057 | 0 | 0 |

## Execution Requirement

To complete Task63, run the same script with `--execute` after configuring a valid LLM provider API key. The formal summary is generated only after `answers.jsonl` and `judgments.jsonl` exist.
