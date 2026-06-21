# Task48 Compressor-Normalized Comparison

Date: 2026-06-20

## Goal

Task48 follows the conclusion from Task46: if sentence-level MMR is a useful
final-context compressor, it should be applied uniformly to both the dense
baseline and IntentWeight evidence pools.

The experiment compares:

- Dense top-10;
- Dense top-10 + SentMMR;
- IntentWeight frozen Task38 evidence pools;
- IntentWeight frozen Task38 evidence pools + SentMMR.

This tests whether IntentWeight remains useful as an upstream route-and-budget
controller when a shared context-compression layer is available.

## Implementation

Script:

- `paper/experiments/scripts/task48_compressor_normalized_comparison.py`

Artifacts:

- `paper/experiments/results/task48_100k_compressor_normalized.md`
- `paper/experiments/results/task48_100k_compressor_normalized.csv`
- `paper/experiments/results/task48_100k_compressor_normalized.paired.csv`
- `paper/experiments/results/task48_100k_compressor_normalized.json`
- `paper/experiments/results/task48_100k_compressor_normalized.rankings.json`

Run command:

```bash
.venv/bin/python paper/experiments/scripts/task48_compressor_normalized_comparison.py \
  --scale 100k \
  --corpus paper/experiments/data/processed/lotte_technology_search_100k_corpus.json \
  --queries paper/experiments/data/processed/lotte_technology_search_100k_queries.json \
  --dense-ranking dense=paper/experiments/results/dense_lotte_technology_search_100k_rankings.json \
  --intent-ranking task38=paper/experiments/results/task38_100k_calibrated_context_budget.rankings.json \
  --intent-include task37_source:gated_cost_aware \
  --budget-ratios 0.95,0.90,0.85 \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --device cpu \
  --local-files-only \
  --batch-size 64 \
  --top-k 10 \
  --eval-split test \
  --bootstrap 2000 \
  --output-prefix paper/experiments/results/task48_100k_compressor_normalized
```

The run uses the Task38 frozen test split:

- LoTTE technology/search 100k;
- 417 frozen test queries;
- dense top-10 as the dense evidence pool;
- Task38 frozen `token_budget_r0.95_m4` IntentWeight evidence pools for seeds
  13, 17, and 19;
- SentMMR ratios `0.95`, `0.90`, and `0.85` over each method's own source
  evidence-pool token count.

## Main Results

Dense+SentMMR preserves dense chunk-support `Hit@10` at all tested ratios:

| Method | Ratio | Hit@10 | Token saving vs dense |
|---|---:|---:|---:|
| Dense top-10 | - | 0.8705 | 0.00% |
| Dense+SentMMR | 0.95 | 0.8705 | 5.33% |
| Dense+SentMMR | 0.90 | 0.8705 | 10.22% |
| Dense+SentMMR | 0.85 | 0.8705 | 15.16% |

IntentWeight+SentMMR preserves each IntentWeight source policy's chunk-support
`Hit@10`, while adding another 5-15% compression relative to that source policy.

| Method | Ratio | Hit@10 range | Token saving vs dense range | Extra saving vs source |
|---|---:|---:|---:|---:|
| IntentWeight | - | 0.8657-0.8777 | 4.98-7.14% | - |
| IntentWeight+SentMMR | 0.95 | 0.8657-0.8777 | 10.07-12.14% | 5.36-5.39% |
| IntentWeight+SentMMR | 0.90 | 0.8657-0.8777 | 14.72-16.68% | 10.25-10.28% |
| IntentWeight+SentMMR | 0.85 | 0.8657-0.8777 | 19.41-21.24% | 15.18-15.20% |

All `vs_source` paired comparisons report zero chunk-support `Hit@10` loss for
the tested ratios. The `vs_dense` comparisons inherit the same seed-level
IntentWeight behavior as Task38: seed 19 is above dense, while seeds 13 and 17
are slightly below dense and do not pass strict 1pp bootstrap non-inferiority.

## Interpretation

Task48 supports a cleaner engineering decomposition:

- SentMMR is a shared final-context compression layer.
- IntentWeight is an upstream route-and-budget controller.
- The fair engineering comparison is no longer "IntentWeight vs compression";
  it is "which evidence pool is better after applying the same compressor?"

Under this view, IntentWeight+SentMMR can reach larger token savings than
Dense+SentMMR at the same compressor ratio because IntentWeight already starts
from a smaller evidence pool. However, retrieval quality remains seed-dependent
under the available chunk-support metric. The paper should therefore avoid a
dominance claim and instead state that IntentWeight is compatible with, and can
be stacked with, sentence-level compression.

## Limitations

The metrics are still chunk-support proxies. They show that selected sentence
contexts continue to represent the same relevant chunks, but they do not prove
that the exact answer-bearing sentence is preserved. A downstream answer-level
check is still needed before making answer-quality claims.

## Paper-Facing Recommendation

Use Task48 to justify this framing:

> We apply the same sentence-level MMR compressor to dense and IntentWeight
> evidence pools. The compressor preserves chunk-support Hit@10 for both sources
> at tested ratios and provides additional final-context token savings. This
> positions IntentWeight as a route-and-budget controller that is complementary
> to final-context compression rather than a replacement for it.

Task47 cross-encoder reranker is now completed. The next highest-value paper
task is claim and novelty reframing around the completed strong-baseline
evidence.
