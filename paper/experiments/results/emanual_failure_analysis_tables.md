# Task 14.5 eManual Failure Analysis

| num_corpus_chunks | num_unique_texts | duplicate_text_groups | gt_refs_with_duplicate_text | gt_ref_duplicate_count_mean | random_record_neighbor_purity | random_record_neighbor_hit@10 |
| --- | --- | --- | --- | --- | --- | --- |
| 18812 | 1729 | 1571 | 861 | 22.2636 | 0.0021 | 0.0205 |

## Existing Rankings

| method | evaluation_mode | num_seeds | recall@10_mean | mrr@10_mean | ndcg@10_mean |
| --- | --- | --- | --- | --- | --- |
| bm25 | strict_chunk_id | 1 | 0.1154 | 0.0244 | 0.0256 |
| bm25 | text_equivalent | 1 | 0.3846 | 0.3059 | 0.1620 |
| dense | strict_chunk_id | 1 | 0.3231 | 0.0551 | 0.0526 |
| dense | text_equivalent | 1 | 0.5615 | 0.4716 | 0.2030 |
| hybrid_rrf | strict_chunk_id | 1 | 0.1692 | 0.0366 | 0.0287 |
| hybrid_rrf | text_equivalent | 1 | 0.5846 | 0.4895 | 0.2263 |
| linucb_soft | strict_chunk_id | 3 | 0.1436 | 0.0337 | 0.0248 |
| linucb_soft | text_equivalent | 3 | 0.5795 | 0.4761 | 0.2139 |

## Deduplicated Corpus Baselines

| method | evaluation_mode | num_corpus_chunks | recall@10 | mrr@10 | ndcg@10 |
| --- | --- | --- | --- | --- | --- |
| dedup_bm25 | deduplicated_text_corpus | 1729 | 0.7308 | 0.4218 | 0.3000 |
| dedup_dense | deduplicated_text_corpus | 1729 | 0.8615 | 0.5736 | 0.3807 |
| dedup_hybrid_rrf | deduplicated_text_corpus | 1729 | 0.8615 | 0.5903 | 0.3956 |

## Centroid Routing

| method | evaluation_mode | recall@10 | mrr@10 | ndcg@10 |
| --- | --- | --- | --- | --- |
| nearest_centroid_1_clusters | strict_chunk_id | 0.2769 | 0.0463 | 0.0351 |
| nearest_centroid_1_clusters | text_equivalent | 0.4846 | 0.4228 | 0.1724 |
| nearest_centroid_3_clusters | strict_chunk_id | 0.3308 | 0.0539 | 0.0519 |
| nearest_centroid_3_clusters | text_equivalent | 0.5462 | 0.4647 | 0.1990 |
| nearest_centroid_5_clusters | strict_chunk_id | 0.3385 | 0.0552 | 0.0493 |
| nearest_centroid_5_clusters | text_equivalent | 0.5462 | 0.4578 | 0.1953 |
| gt_cluster_oracle | strict_chunk_id | 0.3308 | 0.0568 | 0.0535 |
| gt_cluster_oracle | text_equivalent | 0.6615 | 0.5713 | 0.2737 |

## LinUCB Soft Diagnostics

| bm25_fallback_hit_rate_mean | cluster_local_hit_rate_mean | dense_fallback_hit_rate_mean | mrr@10_mean | num_queries_mean | num_seeds | recall@10_mean | selected_cluster_hit_rate_mean | selected_cluster_miss_rate_mean | soft_fused_hit_rate_mean | soft_rescue_on_cluster_miss_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1154 | 0.0487 | 0.1692 | 0.0337 | 130.0000 | 3 | 0.1436 | 0.2641 | 0.7359 | 0.1436 | 0.1173 |

## Interpretation

- Low record-id purity cannot exclude usable geometry because `record_id` is an instance-level label, not a semantic topic label.
- Strict chunk-id recall is heavily affected by duplicate manual sentences across records.
- Text-equivalent and deduplicated-corpus metrics should be reported as diagnostics, not replacements for the strict main table.
- If nearest-centroid routing is strong while LinUCB-selected-cluster diagnostics are weak, the failure is likely policy/fusion/credit assignment rather than absence of geometry.
