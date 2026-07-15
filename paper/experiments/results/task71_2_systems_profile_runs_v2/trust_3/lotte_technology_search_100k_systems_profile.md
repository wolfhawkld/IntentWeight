# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1232.53 |
| load_queries_json | 1.50 |
| load_corpus_embeddings | 148.25 |
| load_query_embeddings | 1.09 |
| load_dense_rankings | 135.52 |
| load_bm25_rankings | 135.63 |
| load_context_clusters | 147.69 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 6570.04 ms; throughput: 90.71 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0072 | 0.0083 | 4.5116 |
| cluster_route | 596 | 4.8789 | 8.8749 | 3255.3199 |
| dense_route | 596 | 0.0096 | 0.0115 | 6.0453 |
| feedback_memory_append | 596 | 0.0013 | 0.0019 | 0.8394 |
| feedback_observation | 1788 | 0.0082 | 0.0233 | 21.4007 |
| feedback_reward_measurement | 1788 | 0.0238 | 0.0509 | 50.5920 |
| feedback_state_update | 1788 | 0.1384 | 0.2107 | 270.5918 |
| feedback_trust_weighting | 1788 | 0.0020 | 0.0037 | 4.2250 |
| final_context_budget | 596 | 0.0066 | 0.0080 | 3.9550 |
| fusion_and_dense_floor | 596 | 0.2399 | 0.3048 | 160.5155 |
| linucb_update | 7152 | 0.0229 | 0.0411 | 179.7499 |
| routing_and_gating | 596 | 4.2416 | 6.2819 | 2699.1028 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
