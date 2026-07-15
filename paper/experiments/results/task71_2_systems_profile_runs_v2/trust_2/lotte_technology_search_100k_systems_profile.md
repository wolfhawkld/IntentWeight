# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1326.16 |
| load_queries_json | 1.51 |
| load_corpus_embeddings | 148.00 |
| load_query_embeddings | 1.24 |
| load_dense_rankings | 135.30 |
| load_bm25_rankings | 136.41 |
| load_context_clusters | 153.27 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 6429.92 ms; throughput: 92.69 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0071 | 0.0081 | 4.3953 |
| cluster_route | 596 | 4.7890 | 8.6815 | 3190.3266 |
| dense_route | 596 | 0.0088 | 0.0109 | 5.4824 |
| feedback_memory_append | 596 | 0.0014 | 0.0018 | 0.8551 |
| feedback_observation | 1788 | 0.0067 | 0.0225 | 21.3374 |
| feedback_reward_measurement | 1788 | 0.0157 | 0.0501 | 45.3221 |
| feedback_state_update | 1788 | 0.1325 | 0.2119 | 266.6400 |
| feedback_trust_weighting | 1788 | 0.0017 | 0.0041 | 4.3071 |
| final_context_budget | 596 | 0.0077 | 0.0086 | 4.6967 |
| fusion_and_dense_floor | 596 | 0.2387 | 0.2992 | 152.3694 |
| linucb_update | 7152 | 0.0226 | 0.0424 | 171.2528 |
| routing_and_gating | 596 | 4.2167 | 5.6812 | 2639.9535 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
