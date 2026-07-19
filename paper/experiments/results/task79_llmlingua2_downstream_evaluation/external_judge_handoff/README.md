# Task79 External Judge Handoff

Run every `requests.jsonl` prompt independently with `glm-5.2` and `minimax-m3`.
Do not alter the system prompt, user prompt, answer, context, or schema.
Return one response row per request/model using the embedded response contract.
Provider rejections must be returned as explicit error rows and are not imputed.
