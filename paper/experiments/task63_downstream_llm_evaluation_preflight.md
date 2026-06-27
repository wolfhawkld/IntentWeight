# Task63 Downstream LLM Evaluation Preflight

This file records the Task63 preflight. The formal answer-level experiment is
now complete; use `task63_downstream_llm_evaluation_summary.md` and the formal
result directory for claims and statistics.

Result directory:

- `paper/experiments/results/task63_downstream_llm_evaluation/`

Prepared scope:

- dataset: LoTTE technology search 100k;
- split: Task38 frozen test split;
- sample size: 300 queries from 417 frozen-test queries;
- methods:
  - MiniLM dense top-10;
  - BGE-base dense top-10;
  - BGE-base positive IntentWeight, seed 19;
  - E5-base dense top-10;
  - E5-base full multi-route IntentWeight, seed 19;
  - MiniLM dense top-10 + SentMMR, ratio 0.85, lambda 0.70;
  - MiniLM IntentWeight seed 19 + SentMMR, ratio 0.85, lambda 0.70.

Preflight retrieval/token check:

| method | Hit@10 | evidence recall@10 | avg context tokens | token saving vs MiniLM dense |
| --- | ---: | ---: | ---: | ---: |
| MiniLM dense top-10 | 0.8700 | 0.7097 | 1461 | 0.00% |
| BGE-base dense top-10 | 0.9000 | 0.7447 | 1698 | -16.16% |
| BGE-base positive IntentWeight seed 19 | 0.9133 | 0.7504 | 1596 | -9.19% |
| E5-base dense top-10 | 0.8733 | 0.7161 | 1525 | -4.32% |
| E5-base full multi-route IntentWeight seed 19 | 0.8700 | 0.7084 | 1341 | 8.23% |
| MiniLM dense + SentMMR | 0.8700 | 0.7097 | 1240 | 15.16% |
| MiniLM IntentWeight seed 19 + SentMMR | 0.8767 | 0.6925 | 1157 | 20.80% |

Status:

- preflight superseded by the completed 2,100-answer / 2,100-judgment run;
- this file remains as an execution-readiness record and is not the formal
  result summary.

Execution readiness:

- `.env` is ignored by git and contains local DeepSeek settings for this
  machine;
- the preflight script detected DeepSeek credentials in the local environment.

Formal Task63 completion is documented in
`paper/experiments/task63_downstream_llm_evaluation_summary.md`.
