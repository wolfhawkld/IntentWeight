# Task62 Prompt-Compression Baseline

Updated: 2026-06-26

## Objective

Task62 addresses the review risk that LLMLingua / Selective Context style
prompt-compression baselines are missing. The goal is not to replace Task46 or
Task48. The goal is to add a second downstream prompt-pruning baseline and
clarify that prompt compression is complementary to IntentWeight's upstream
route-and-budget controller.

The experiment uses the same LoTTE technology/search 100k frozen test split as
Task38, Task46, and Task48.

## Implementation

Script:

- `paper/experiments/scripts/task62_prompt_compression_baseline.py`

Artifacts:

- `paper/experiments/results/task62_100k_prompt_compression_baseline.md`
- `paper/experiments/results/task62_100k_prompt_compression_baseline.csv`
- `paper/experiments/results/task62_100k_prompt_compression_baseline.paired.csv`
- `paper/experiments/results/task62_100k_prompt_compression_baseline.json`
- `paper/experiments/results/task62_100k_prompt_compression_baseline.rankings.json`

Run command:

```bash
.venv/bin/python paper/experiments/scripts/task62_prompt_compression_baseline.py \
  --scale 100k \
  --corpus paper/experiments/data/processed/lotte_technology_search_100k_corpus.json \
  --queries paper/experiments/data/processed/lotte_technology_search_100k_queries.json \
  --dense-ranking dense=paper/experiments/results/dense_lotte_technology_search_100k_rankings.json \
  --intent-ranking task38=paper/experiments/results/task38_100k_calibrated_context_budget.rankings.json \
  --intent-include task37_source:gated_cost_aware \
  --budget-ratios 0.95,0.90,0.85,0.75 \
  --top-k 10 \
  --eval-split test \
  --bootstrap 2000 \
  --sent-mmr-reference paper/experiments/results/task48_100k_compressor_normalized.csv \
  --output-prefix paper/experiments/results/task62_100k_prompt_compression_baseline
```

Token accounting uses `tiktoken` with `cl100k_base`, matching Task38, Task46,
and Task48. A temporary simple-tokenizer smoke run was discarded and is not used
for paper-facing results.

## Compressor Definition

`selective_context_lite` is a local Selective Context-style prompt-pruning
proxy. It:

- splits retrieved chunks into sentence-like prompt units;
- scores units with query-term overlap, IDF-weighted salience, query-bigram
  overlap, source-rank priority, and a small compactness bonus;
- keeps at least one high-salience unit per source chunk where the budget allows;
- fills the remaining budget with the most query-salient units.

This is not LLMLingua. It is a deterministic local prompt-pruning baseline that
addresses the same downstream compression category without adding model
download/runtime dependencies.

## Main Results

Dense top-10 plus SelectiveContext-lite preserves dense chunk-support Hit@10 at
all tested ratios:

| Method | Ratio | Hit@10 | Token saving vs dense |
| --- | ---: | ---: | ---: |
| Dense top-10 | - | 0.8705 | 0.00% |
| Dense+SelectiveContext-lite | 0.95 | 0.8705 | 5.66% |
| Dense+SelectiveContext-lite | 0.90 | 0.8705 | 10.42% |
| Dense+SelectiveContext-lite | 0.85 | 0.8705 | 15.31% |
| Dense+SelectiveContext-lite | 0.75 | 0.8705 | 25.19% |

When the same compressor is applied to IntentWeight evidence pools, it preserves
each source pool's chunk-support Hit@10 and adds roughly the requested
compression on top of the upstream IntentWeight token saving.

| Method | Ratio | Hit@10 range | Token saving vs dense range | Extra saving vs source |
| --- | ---: | ---: | ---: | ---: |
| IntentWeight | - | 0.8657-0.8777 | 4.98-7.14% | - |
| IntentWeight+SelectiveContext-lite | 0.95 | 0.8657-0.8777 | 10.38-12.42% | 5.62-5.69% |
| IntentWeight+SelectiveContext-lite | 0.90 | 0.8657-0.8777 | 14.92-16.87% | 10.46-10.48% |
| IntentWeight+SelectiveContext-lite | 0.85 | 0.8657-0.8777 | 19.53-21.40% | 15.31-15.35% |
| IntentWeight+SelectiveContext-lite | 0.75 | 0.8657-0.8777 | 28.95-30.57% | 25.20-25.23% |

The dense rows closely match Task48 SentMMR at shared ratios:

| Compressor | Ratio | Hit@10 | Token saving vs dense |
| --- | ---: | ---: | ---: |
| SentMMR | 0.95 | 0.8705 | 5.33% |
| SelectiveContext-lite | 0.95 | 0.8705 | 5.66% |
| SentMMR | 0.90 | 0.8705 | 10.22% |
| SelectiveContext-lite | 0.90 | 0.8705 | 10.42% |
| SentMMR | 0.85 | 0.8705 | 15.16% |
| SelectiveContext-lite | 0.85 | 0.8705 | 15.31% |

## Interpretation

Task62 strengthens the compressor-baseline defense. A downstream prompt-pruning
baseline can preserve chunk-support Hit@10 while saving substantial final
context tokens. This means the paper should not claim that IntentWeight
dominates prompt compression.

The correct decomposition is:

- Prompt compression operates after an evidence pool has been selected.
- IntentWeight operates upstream by controlling which evidence pool and budget
  are passed downstream.
- The two can be stacked: IntentWeight+prompt compression reaches larger total
  token savings than dense+prompt compression because IntentWeight starts from a
  smaller evidence pool.

## Limitations

The metric remains chunk-support Hit@10, not answer-level sufficiency. Because
the compressor keeps sentence-like units from relevant chunks, it preserves the
chunk-support proxy; it does not prove that every answer-bearing sentence is
kept. Task63 should address this with a larger downstream answer evaluation.

## Paper-Facing Recommendation

Use Task62 to write:

> Prompt compression is a downstream context layer. IntentWeight is an upstream
> retrieval-aware route-and-budget controller and can be composed with prompt
> compression.

Do not write:

> IntentWeight replaces LLMLingua, Selective Context, or prompt compression.
