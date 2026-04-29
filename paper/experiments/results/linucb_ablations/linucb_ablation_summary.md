# Global LinUCB Ablation Summary

PubMedQA sample ablation: `max_queries=200`, `max_corpus=1000`, `seeds=13,17,19`, `n_clusters=16`, `context_dim=32`.

| variant | description | recall@1_mean | recall@10_mean | mrr@10_mean | ndcg@10_mean |
| --- | --- | --- | --- | --- | --- |
| main_sample | default: alpha_decay=0.01, candidate_arms=3 | 0.4033 | 0.5450 | 0.4690 | 0.3845 |
| no_decay | alpha_decay=0.0, candidate_arms=3 | 0.4767 | 0.6550 | 0.5615 | 0.4674 |
| candidate_arms_1 | alpha_decay=0.01, candidate_arms=1 | 0.1733 | 0.2433 | 0.2060 | 0.1586 |
| candidate_arms_5 | alpha_decay=0.01, candidate_arms=5 | 0.5950 | 0.8150 | 0.6984 | 0.6021 |

## Notes

- This is a sample-scale ablation for Task 11 design, not the final paper-wide ablation matrix.
- `candidate_arms=1` is too narrow for this setting.
- `candidate_arms=5` performs best in this sample, suggesting that cluster prefilter breadth is a critical hyperparameter.
- `alpha_decay=0.0` outperforms the default decay in this sample, suggesting the current decay schedule may exploit too early.
