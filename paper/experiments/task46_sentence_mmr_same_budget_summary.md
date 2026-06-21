# Task46 Sentence-MMR Same-Budget Baseline

Date: 2026-06-20

## Goal

Task46 adds the lowest-cost reviewer-facing compression baseline requested by
the review notes:

> Why not simply compress dense top-10 context?

The baseline starts from dense top-10 retrieved chunks, splits those chunks into
sentence-like evidence units, selects sentence units with query-sentence MMR,
and caps the selected sentence context by the per-query final-context token
budget used by the frozen Task38 IntentWeight policy.

This is a diagnostic baseline, not a replacement method.

## Implementation

Script:

- `paper/experiments/scripts/task46_sentence_mmr_baseline.py`

Main artifact:

- `paper/experiments/results/task46_100k_sent_mmr_same_budget.md`
- `paper/experiments/results/task46_100k_sent_mmr_same_budget.csv`
- `paper/experiments/results/task46_100k_sent_mmr_same_budget.paired.csv`
- `paper/experiments/results/task46_100k_sent_mmr_same_budget.json`
- `paper/experiments/results/task46_100k_sent_mmr_same_budget.rankings.json`

Run command:

```bash
.venv/bin/python paper/experiments/scripts/task46_sentence_mmr_baseline.py \
  --scale 100k \
  --corpus paper/experiments/data/processed/lotte_technology_search_100k_corpus.json \
  --queries paper/experiments/data/processed/lotte_technology_search_100k_queries.json \
  --dense-ranking dense=paper/experiments/results/dense_lotte_technology_search_100k_rankings.json \
  --target-ranking task38=paper/experiments/results/task38_100k_calibrated_context_budget.rankings.json \
  --target-include task37_source:gated_cost_aware \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --device cpu \
  --local-files-only \
  --batch-size 64 \
  --top-k 10 \
  --eval-split test \
  --bootstrap 2000 \
  --output-prefix paper/experiments/results/task46_100k_sent_mmr_same_budget
```

The evaluation uses the same Task38 deterministic split:

- 179 calibration queries;
- 417 frozen test queries;
- LoTTE technology/search 100k;
- dense top-10 as the candidate pool;
- Task38 `token_budget_r0.95_m4` target budgets from seeds 13, 17, and 19.

## Results

On the 417-query frozen test split, Dense+Sentence-MMR preserves the dense
chunk-support `Hit@10` proxy while reducing final selected sentence tokens.

| Budget target | Hit@10 | Hit delta vs dense | EvidenceRecall@10 | Avg context tokens | Token saving vs dense | Avg selected sentences | Avg supported chunks |
|---|---:|---:|---:|---:|---:|---:|---:|
| SentMMR, seed13 budget | 0.8705 | 0.0000 | 0.7081 | 1287.8 | 12.40% | 52.0 | 9.995 |
| SentMMR, seed17 budget | 0.8705 | 0.0000 | 0.7075 | 1278.0 | 13.07% | 51.7 | 9.981 |
| SentMMR, seed19 budget | 0.8705 | 0.0000 | 0.7081 | 1302.1 | 11.43% | 52.7 | 9.993 |
| Dense top-10 | 0.8705 | 0.0000 | 0.7081 | 1470.1 | 0.00% | - | 10.000 |

The paired dense comparison reports no `Hit@10` losses:

| Budget target | Hit delta mean | Hit CI low | Token ratio | Token saving | Noninferior by CI |
|---|---:|---:|---:|---:|---:|
| seed13 budget | 0.0000 | 0.0000 | 0.8760 | 12.40% | True |
| seed17 budget | 0.0000 | 0.0000 | 0.8693 | 13.07% | True |
| seed19 budget | 0.0000 | 0.0000 | 0.8857 | 11.43% | True |

## Interpretation

This result strengthens the reviewer-facing baseline coverage, but it also
constrains the paper claim.

The safe reading is:

- simple sentence-level compression over dense top-10 is a strong final-context
  token baseline on LoTTE technology/search 100k under chunk-support metrics;
- IntentWeight should not be framed as the only way to reduce final context
  tokens;
- the paper should frame IntentWeight as a route-and-budget controller that is
  complementary to sentence compression and reranking;
- if this baseline is added to the paper, the limitation should state that
  Task46 evaluates chunk-support proxies, not sentence-level answer evidence.

The result does not prove that Dense+Sentence-MMR selects the exact answer
sentence. It only shows that the selected sentence set continues to represent
the same relevant source chunks under the available chunk-level labels.

## Paper-Facing Recommendation

Use Task46 as a diagnostic compression baseline in the discussion or appendix.
Do not use it to claim IntentWeight dominates compression. A safer paper-facing
sentence is:

> A lightweight Dense+Sentence-MMR compression baseline can preserve dense-level
> chunk-support on LoTTE technology/search 100k at comparable final-context
> budgets, indicating that IntentWeight is best viewed as a route-and-budget
> controller complementary to sentence-level compression rather than a
> replacement for context compressors.

## Next Step

Task47 has now added the heavier cross-encoder reranker same-budget baseline.
The next paper task is to revise novelty and claim framing around the completed
compression and reranker baselines.
