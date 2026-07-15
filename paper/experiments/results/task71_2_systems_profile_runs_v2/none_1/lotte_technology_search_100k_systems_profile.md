# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1243.26 |
| load_queries_json | 1.51 |
| load_corpus_embeddings | 147.62 |
| load_query_embeddings | 1.12 |
| load_dense_rankings | 139.41 |
| load_bm25_rankings | 147.40 |
| load_context_clusters | 151.48 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 6798.97 ms; throughput: 87.66 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0075 | 0.0092 | 4.6884 |
| cluster_route | 596 | 5.3145 | 12.2176 | 3689.7997 |
| dense_route | 596 | 0.0097 | 0.0122 | 6.1569 |
| feedback_memory_append | 596 | 0.0004 | 0.0005 | 0.2512 |
| feedback_observation | 1788 | 0.0018 | 0.0075 | 6.4987 |
| feedback_reward_measurement | 1788 | 0.0119 | 0.0524 | 42.8438 |
| feedback_state_update | 1788 | 0.0013 | 0.0062 | 4.8194 |
| feedback_trust_weighting | 1788 | 0.0010 | 0.0031 | 2.8335 |
| final_context_budget | 596 | 0.0080 | 0.0099 | 6.2749 |
| fusion_and_dense_floor | 596 | 0.2482 | 0.3845 | 170.3112 |
| routing_and_gating | 596 | 4.0642 | 7.8031 | 2763.1197 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
