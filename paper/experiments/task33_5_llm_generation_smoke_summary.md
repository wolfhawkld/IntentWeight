# Task33.5 LLM Generation Smoke Summary

Updated: 2026-05-27

Task33.5 runs a small downstream answer-generation smoke test. It compares
dense top-10 context with Task29-C compressed context on LoTTE technology/search
100k. The goal is to check whether reducing final retrieved context tokens
causes obvious LLM answer-quality degradation.

This is not the main evidence chain. The main paper claim still rests on
retrieval quality and final retrieved-context token cost. Task33.5 is a
sanity check for downstream generation.

## Configuration

- Dataset: `lotte_technology_search_100k`.
- Query sample size: `60`.
- Dense baseline: `dense_lotte_technology_search_100k_rankings.json`.
- Treatment: Task29-C `gated_cost_aware`, seed `13`.
- LLM provider: DeepSeek OpenAI-compatible endpoint.
- Model: `deepseek-v4-flash`.
- API mode: Chat Completions.
- Thinking mode: enabled.
- Reasoning effort: high.
- Max output tokens: `2048`.
- Judge retries: `2`.

Each sampled query uses three LLM calls:

1. generate answer from dense top-10 context;
2. generate answer from Task29-C context;
3. judge dense answer vs treatment answer using reference evidence.

## Results

| Metric | Dense | Task29-C |
|---|---:|---:|
| Answer score mean | 4.4000 | 4.2833 |
| Faithfulness mean | 4.6500 | 4.6333 |
| Answer relevance mean | 4.6500 | 4.4500 |
| Retrieval hit rate in sampled queries | 0.7500 | 0.7500 |
| Prompt context token proxy mean | 1224.50 | 1141.38 |
| Prompt context token proxy ratio | 1.0000 | 0.9321 |

Judge validity:

- valid judge rows: `60 / 60`;
- invalid judge rows: `0 / 60`.

Winner counts:

| Winner | Count |
|---|---:|
| tie | 32 |
| dense | 14 |
| Task29-C | 14 |

## Interpretation

The 60-query smoke test does not show catastrophic answer-quality degradation
from Task29-C context compaction. Dense and Task29-C have identical winner
counts when excluding ties (`14` vs `14`), and most comparisons are ties
(`32 / 60`). Faithfulness is nearly identical (`4.6500` vs `4.6333`).

Dense has a small edge in average answer score and answer relevance
(`4.4000` vs `4.2833`, and `4.6500` vs `4.4500`). This means the result should
not be written as Task29-C clearly outperforming dense in generated answer
quality. The safer paper-facing conclusion is:

> In a 60-query downstream LLM generation smoke test, Task29-C compressed
> context did not cause obvious answer-quality degradation relative to dense
> top-10. Dense and Task29-C tied on most examples and had equal non-tie win
> counts, while Task29-C used fewer prompt context tokens in the sampled
> contexts.

## Paper Use

Use this result as a downstream sanity check or appendix item. It strengthens
the claim that retrieval/context-token savings are not obviously harmful to
generation quality, but it should not replace the main retrieval and token-cost
experiments.

The limitation remains:

- only 60 sampled queries;
- one LLM judge/generator model;
- LLM-as-judge can be biased;
- generated-answer quality is not the primary metric of the paper.

## Artifacts

- `paper/experiments/results/task33_5_llm_generation_smoke/llm_results.jsonl`
- `paper/experiments/results/task33_5_llm_generation_smoke/sample_records.jsonl`
- `paper/experiments/results/task33_5_llm_generation_smoke/summary.json`
- `paper/experiments/results/task33_5_llm_generation_smoke/summary.md`
- `paper/experiments/scripts/task33_5_llm_generation_smoke.py`
