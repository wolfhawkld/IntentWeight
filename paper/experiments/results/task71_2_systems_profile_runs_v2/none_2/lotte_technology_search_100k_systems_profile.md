# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1277.16 |
| load_queries_json | 1.65 |
| load_corpus_embeddings | 160.38 |
| load_query_embeddings | 1.26 |
| load_dense_rankings | 173.09 |
| load_bm25_rankings | 150.13 |
| load_context_clusters | 152.87 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 5743.37 ms; throughput: 103.77 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0074 | 0.0083 | 4.7660 |
| cluster_route | 596 | 4.4710 | 7.8719 | 2981.2262 |
| dense_route | 596 | 0.0092 | 0.0111 | 5.7394 |
| feedback_memory_append | 596 | 0.0004 | 0.0005 | 0.2412 |
| feedback_observation | 1788 | 0.0017 | 0.0073 | 6.0686 |
| feedback_reward_measurement | 1788 | 0.0116 | 0.0532 | 42.9501 |
| feedback_state_update | 1788 | 0.0012 | 0.0052 | 4.1457 |
| feedback_trust_weighting | 1788 | 0.0010 | 0.0027 | 2.5493 |
| final_context_budget | 596 | 0.0061 | 0.0078 | 3.8211 |
| fusion_and_dense_floor | 596 | 0.2354 | 0.2966 | 151.3218 |
| routing_and_gating | 596 | 3.8187 | 5.2336 | 2408.9279 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
