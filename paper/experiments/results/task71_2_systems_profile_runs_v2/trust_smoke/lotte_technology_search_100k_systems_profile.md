# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1214.08 |
| load_queries_json | 1.63 |
| load_corpus_embeddings | 151.31 |
| load_query_embeddings | 1.00 |
| load_dense_rankings | 129.92 |
| load_bm25_rankings | 131.74 |
| load_context_clusters | 134.04 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 6217.75 ms; throughput: 95.85 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0070 | 0.0083 | 4.4386 |
| cluster_route | 596 | 4.4047 | 8.3303 | 2971.1734 |
| dense_route | 596 | 0.0095 | 0.0114 | 5.8786 |
| feedback_memory_append | 596 | 0.0012 | 0.0018 | 0.7903 |
| feedback_observation | 1788 | 0.0076 | 0.0217 | 19.3966 |
| feedback_reward_measurement | 1788 | 0.0216 | 0.0506 | 49.0083 |
| feedback_state_update | 1788 | 0.1318 | 0.2076 | 269.2853 |
| feedback_trust_weighting | 1788 | 0.0018 | 0.0038 | 4.1034 |
| final_context_budget | 596 | 0.0061 | 0.0083 | 3.9888 |
| fusion_and_dense_floor | 596 | 0.2326 | 0.2839 | 144.0147 |
| linucb_update | 7152 | 0.0224 | 0.0393 | 178.2287 |
| routing_and_gating | 596 | 4.1340 | 5.9059 | 2618.4319 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
