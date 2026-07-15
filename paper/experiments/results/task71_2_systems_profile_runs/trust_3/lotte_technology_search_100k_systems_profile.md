# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 2290.73 |
| load_queries_json | 2.90 |
| load_corpus_embeddings | 264.21 |
| load_query_embeddings | 1.79 |
| load_dense_rankings | 244.94 |
| load_bm25_rankings | 248.66 |
| load_context_clusters | 342.75 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 19272.48 ms; throughput: 30.92 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0081 | 0.0101 | 5.5820 |
| cluster_route | 596 | 17.5798 | 37.9088 | 12392.4494 |
| dense_route | 596 | 0.0109 | 0.0147 | 7.0186 |
| feedback_memory_append | 596 | 0.0014 | 0.0021 | 0.8940 |
| feedback_observation_and_trust | 1788 | 0.0310 | 0.1076 | 110.6177 |
| feedback_state_update | 1788 | 0.1443 | 0.2564 | 385.5671 |
| final_context_budget | 596 | 0.0077 | 0.0112 | 5.0515 |
| fusion_and_dense_floor | 596 | 0.2479 | 0.4323 | 197.1080 |
| linucb_update | 7152 | 0.0241 | 0.0443 | 248.6070 |
| routing_and_gating | 596 | 8.5582 | 16.5997 | 5882.4496 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
