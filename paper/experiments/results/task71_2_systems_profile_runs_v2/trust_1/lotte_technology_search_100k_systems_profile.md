# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1263.32 |
| load_queries_json | 1.56 |
| load_corpus_embeddings | 151.69 |
| load_query_embeddings | 1.06 |
| load_dense_rankings | 133.20 |
| load_bm25_rankings | 133.93 |
| load_context_clusters | 133.95 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 6174.15 ms; throughput: 96.53 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0072 | 0.0081 | 4.3726 |
| cluster_route | 596 | 4.7191 | 8.2153 | 3054.3053 |
| dense_route | 596 | 0.0090 | 0.0104 | 5.4233 |
| feedback_memory_append | 596 | 0.0013 | 0.0017 | 0.7918 |
| feedback_observation | 1788 | 0.0073 | 0.0225 | 20.1749 |
| feedback_reward_measurement | 1788 | 0.0193 | 0.0520 | 51.3939 |
| feedback_state_update | 1788 | 0.1311 | 0.2046 | 257.0234 |
| feedback_trust_weighting | 1788 | 0.0018 | 0.0041 | 4.3654 |
| final_context_budget | 596 | 0.0070 | 0.0079 | 4.1169 |
| fusion_and_dense_floor | 596 | 0.2353 | 0.2881 | 150.0730 |
| linucb_update | 7152 | 0.0225 | 0.0404 | 167.3102 |
| routing_and_gating | 596 | 4.1088 | 4.9161 | 2535.2761 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
