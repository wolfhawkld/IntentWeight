# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 2361.52 |
| load_queries_json | 2.63 |
| load_corpus_embeddings | 346.18 |
| load_query_embeddings | 1.82 |
| load_dense_rankings | 240.59 |
| load_bm25_rankings | 248.70 |
| load_context_clusters | 235.79 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 14958.55 ms; throughput: 39.84 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0079 | 0.0097 | 4.9795 |
| cluster_route | 596 | 15.5355 | 23.5363 | 9525.0716 |
| dense_route | 596 | 0.0104 | 0.0136 | 6.6126 |
| feedback_memory_append | 596 | 0.0004 | 0.0007 | 0.2648 |
| feedback_observation_and_trust | 1788 | 0.0143 | 0.0674 | 52.0655 |
| feedback_state_update | 1788 | 0.0013 | 0.0059 | 4.5688 |
| final_context_budget | 596 | 0.0073 | 0.0099 | 4.6500 |
| fusion_and_dense_floor | 596 | 0.2492 | 0.3448 | 159.3893 |
| routing_and_gating | 596 | 8.0371 | 12.1241 | 5070.0773 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
