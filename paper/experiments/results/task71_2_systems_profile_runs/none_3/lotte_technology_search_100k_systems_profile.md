# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 2011.84 |
| load_queries_json | 2.55 |
| load_corpus_embeddings | 261.89 |
| load_query_embeddings | 1.46 |
| load_dense_rankings | 227.69 |
| load_bm25_rankings | 260.71 |
| load_context_clusters | 256.69 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 14382.08 ms; throughput: 41.44 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0079 | 0.0096 | 4.8426 |
| cluster_route | 596 | 15.4213 | 23.4063 | 9192.6311 |
| dense_route | 596 | 0.0104 | 0.0131 | 6.6921 |
| feedback_memory_append | 596 | 0.0004 | 0.0007 | 0.2790 |
| feedback_observation_and_trust | 1788 | 0.0148 | 0.0855 | 66.5294 |
| feedback_state_update | 1788 | 0.0013 | 0.0061 | 5.0968 |
| final_context_budget | 596 | 0.0074 | 0.0102 | 4.6128 |
| fusion_and_dense_floor | 596 | 0.2525 | 0.3792 | 168.0444 |
| routing_and_gating | 596 | 8.0700 | 12.1736 | 4813.1271 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
