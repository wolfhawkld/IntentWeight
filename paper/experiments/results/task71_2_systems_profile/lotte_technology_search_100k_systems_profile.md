# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1433.68 |
| load_queries_json | 1.88 |
| load_corpus_embeddings | 158.26 |
| load_query_embeddings | 1.41 |
| load_dense_rankings | 134.78 |
| load_bm25_rankings | 137.75 |
| load_context_clusters | 143.26 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 344661.15 ms; throughput: 41.50 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 14304 | 0.0076 | 0.0094 | 174.4022 |
| cluster_route | 14304 | 13.4393 | 30.6875 | 198170.3537 |
| dense_route | 14304 | 0.0100 | 0.0128 | 214.7165 |
| feedback_memory_append | 14304 | 0.0016 | 0.0021 | 30.2401 |
| feedback_observation_and_trust | 42912 | 0.0316 | 0.0757 | 1790.5230 |
| feedback_state_update | 42912 | 0.1228 | 0.1939 | 5884.6520 |
| final_context_budget | 14304 | 0.0072 | 0.0095 | 108.6153 |
| fusion_and_dense_floor | 14304 | 0.2623 | 0.3433 | 3975.9803 |
| linucb_update | 171648 | 0.0165 | 0.0352 | 3536.4493 |
| routing_and_gating | 14304 | 9.0440 | 17.7258 | 132879.4736 |

Feedback state: 4768 contexts; 1,753,088 numeric bytes; snapshot 2,094,838 bytes.

### Feedback mode: `none`

Stream wall time: 231534.56 ms; throughput: 61.78 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 14304 | 0.0078 | 0.0098 | 158.6862 |
| cluster_route | 14304 | 6.2783 | 23.5802 | 138916.6600 |
| dense_route | 14304 | 0.0101 | 0.0136 | 177.8441 |
| feedback_memory_append | 14304 | 0.0005 | 0.0007 | 7.5913 |
| feedback_observation_and_trust | 42912 | 0.0147 | 0.0625 | 1358.2984 |
| feedback_state_update | 42912 | 0.0013 | 0.0060 | 128.5324 |
| final_context_budget | 14304 | 0.0076 | 0.0103 | 134.1124 |
| fusion_and_dense_floor | 14304 | 0.2911 | 0.4338 | 4845.2322 |
| routing_and_gating | 14304 | 4.2422 | 12.1313 | 84295.6570 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 578,357 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
