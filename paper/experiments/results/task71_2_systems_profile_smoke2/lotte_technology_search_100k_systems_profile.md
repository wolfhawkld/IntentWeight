# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 7940.42 |
| load_queries_json | 2.26 |
| load_corpus_embeddings | 715.33 |
| load_query_embeddings | 2.46 |
| load_dense_rankings | 521.12 |
| load_bm25_rankings | 505.53 |
| load_context_clusters | 570.91 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 22957.87 ms; throughput: 25.96 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0079 | 0.0095 | 4.9152 |
| cluster_route | 596 | 22.7687 | 34.6543 | 14727.6847 |
| dense_route | 596 | 0.0107 | 0.0130 | 12.8968 |
| feedback_memory_append | 596 | 0.0014 | 0.0021 | 0.9357 |
| feedback_observation_and_trust | 1788 | 0.0408 | 0.1003 | 93.4736 |
| feedback_state_update | 1788 | 0.1493 | 0.2209 | 286.6322 |
| final_context_budget | 596 | 0.0071 | 0.0096 | 4.4391 |
| fusion_and_dense_floor | 596 | 0.2505 | 0.3317 | 157.1878 |
| linucb_update | 7152 | 0.0242 | 0.0419 | 187.5972 |
| routing_and_gating | 596 | 12.3847 | 16.6595 | 7400.7066 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

### Feedback mode: `none`

Stream wall time: 21954.01 ms; throughput: 27.15 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0080 | 0.0108 | 13.1351 |
| cluster_route | 596 | 23.5308 | 35.3907 | 14479.1636 |
| dense_route | 596 | 0.0109 | 0.0149 | 6.8739 |
| feedback_memory_append | 596 | 0.0005 | 0.0008 | 0.3256 |
| feedback_observation_and_trust | 1788 | 0.0144 | 0.0635 | 58.6698 |
| feedback_state_update | 1788 | 0.0013 | 0.0055 | 4.3901 |
| final_context_budget | 596 | 0.0072 | 0.0097 | 4.5814 |
| fusion_and_dense_floor | 596 | 0.2493 | 0.3396 | 157.1293 |
| routing_and_gating | 596 | 12.0335 | 16.0656 | 7025.0500 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
