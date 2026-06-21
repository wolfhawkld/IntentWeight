# Task47 Cross-Encoder Reranker Same-Budget Baseline

Date: 2026-06-21

## Goal

Task47 adds the heavier reviewer-facing retrieval baseline requested in the
review plan:

> Can a standard cross-encoder reranker over dense candidates select an equally
> small context more simply than IntentWeight?

This is a diagnostic baseline. It tests whether reranking dense top-50
candidates with a cross-encoder, followed by the same final-context token
budget used by Task38 IntentWeight, dominates the current route-and-budget
controller.

## Implementation

Script:

- `paper/experiments/scripts/task47_cross_encoder_reranker.py`

Artifacts:

- `paper/experiments/results/task47_dense_top50_candidates/dense_lotte_technology_search_100k_rankings.json`
- `paper/experiments/results/task47_dense_top50_candidates/dense_lotte_technology_search_100k_metrics.json`
- `paper/experiments/results/task47_dense_top50_candidates/dense_baseline_summary.csv`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.md`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.csv`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.paired.csv`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.json`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.rankings.json`
- `paper/experiments/results/task47_100k_cross_encoder_reranker.scores.json`

Dense top-50 candidate generation used the local ROCm environment and the AMD
RX 9070 XT:

```bash
source .venv-rocm/bin/activate-rocm
python paper/experiments/scripts/dense_baseline.py \
  --dataset lotte_technology_search_100k \
  --data-dir paper/experiments/data/processed \
  --output-dir paper/experiments/results/task47_dense_top50_candidates \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --device cuda \
  --local-files-only \
  --batch-size 512 \
  --top-k 50 \
  --ks 1,5,10,50 \
  --query-split test
```

The dense candidate run covered all 596 LoTTE technology/search 100k test
queries and produced `Hit@50=0.9513` and `EvidenceRecall@50=0.8552`.

The cross-encoder reranker was run from the standard project `.venv`:

```bash
.venv/bin/python paper/experiments/scripts/task47_cross_encoder_reranker.py \
  --scale 100k \
  --corpus paper/experiments/data/processed/lotte_technology_search_100k_corpus.json \
  --queries paper/experiments/data/processed/lotte_technology_search_100k_queries.json \
  --dense-candidates dense50=paper/experiments/results/task47_dense_top50_candidates/dense_lotte_technology_search_100k_rankings.json \
  --target-ranking task38=paper/experiments/results/task38_100k_calibrated_context_budget.rankings.json \
  --target-include task37_source:gated_cost_aware \
  --model cross-encoder/ms-marco-MiniLM-L-6-v2 \
  --device cpu \
  --local-files-only \
  --batch-size 32 \
  --candidate-depth 50 \
  --top-k 10 \
  --eval-split test \
  --bootstrap 2000 \
  --output-prefix paper/experiments/results/task47_100k_cross_encoder_reranker
```

The reranker used the same Task38 deterministic split:

- 179 calibration queries;
- 417 frozen test queries;
- LoTTE technology/search 100k;
- dense top-50 candidate pool;
- Task38 `token_budget_r0.95_m4` target budgets for seeds 13, 17, and 19.

It scored 20,850 query-chunk pairs with
`cross-encoder/ms-marco-MiniLM-L-6-v2`.

## Results

| Method | Hit@10 | EvidenceRecall@10 | Avg context tokens | Token saving vs dense | Notes |
|---|---:|---:|---:|---:|---|
| Dense top-10 | 0.8705 | 0.7081 | 1470 | 0.00% | Baseline context. |
| Cross-encoder top-10 | 0.8777 | 0.7332 | 1792 | -21.91% | Better support metrics, but longer context. |
| IntentWeight target, seeds 13/17/19 | 0.8657-0.8777 | 0.6766-0.6871 | 1365-1397 | 4.98-7.14% | Frozen Task38 target policies. |
| Cross-encoder same budget, seeds 13/17/19 | 0.8633-0.8729 | 0.6975-0.7044 | 1360-1390 | 5.43-7.49% | Reranked chunks greedily kept under each IntentWeight budget. |

The top-10 cross-encoder reranker improves chunk-support `Hit@10` by about
`+0.72pp` and `EvidenceRecall@10` by about `+2.51pp`, but it selects longer
chunks and increases final context tokens by about `21.9%` relative to dense
top-10.

When constrained to the same per-query token budgets as Task38 IntentWeight,
the reranker does not consistently dominate the current method. Its
same-budget `Hit@10` ranges from `0.8633` to `0.8729`, while the corresponding
IntentWeight target policies range from `0.8657` to `0.8777`.

## Interpretation

Task47 strengthens the baseline coverage but does not overturn the current
paper framing.

- A cross-encoder is a strong ranking baseline and can improve support metrics
  when allowed to keep a full reranked top-10.
- The full reranked top-10 is not a token-saving baseline on this split; it
  increases selected context tokens because the highest-scoring reranked chunks
  are longer on average.
- Under the same final-context token budgets, cross-encoder reranking does not
  provide a simpler baseline that uniformly beats IntentWeight.
- Cross-encoder compute is also heavier than the lightweight route-and-budget
  controller, and the token metrics above do not charge that compute cost.

The safe claim is that IntentWeight remains competitive as a lightweight
route-and-budget controller under a strong reranker baseline. It should not be
framed as replacing rerankers; rerankers, SentMMR, and IntentWeight can be
stacked as separate retrieval-ranking, context-compression, and budget-control
layers.

## Limitations

- The experiment reranks dense candidates only; it does not retrieve over the
  full corpus with a cross-encoder.
- The result is currently limited to LoTTE technology/search 100k.
- Metrics are chunk-support proxies, not downstream answer-level correctness.
- Same-budget selection keeps full chunks, not compressed sentences, so it is
  complementary to Task46/Task48 SentMMR rather than a replacement for them.

## Paper-Facing Recommendation

Use Task47 as a strong reranker baseline in the appendix or baseline discussion:

> A cross-encoder reranker over dense top-50 candidates improves chunk-support
> when allowed to keep a full reranked top-10, but that setting increases final
> context tokens. Under the same calibrated per-query token budgets used by
> IntentWeight, reranking does not uniformly dominate the lightweight
> route-and-budget controller.

This supports a conservative systems framing: IntentWeight is a low-compute
route-and-budget controller that is complementary to heavier reranking and
sentence-level context compression.
