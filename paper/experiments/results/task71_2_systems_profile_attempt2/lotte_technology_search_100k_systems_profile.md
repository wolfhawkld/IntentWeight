# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 2469.39 |
| load_queries_json | 7.21 |
| load_corpus_embeddings | 696.28 |
| load_query_embeddings | 1.34 |
| load_dense_rankings | 612.10 |
| load_bm25_rankings | 556.16 |
| load_context_clusters | 563.56 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 48662.78 ms; throughput: 24.50 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 1192 | 0.0079 | 0.0100 | 25.9357 |
| cluster_route | 1192 | 22.7946 | 34.8915 | 30740.7313 |
| dense_route | 1192 | 0.0105 | 0.0137 | 13.0334 |
| feedback_memory_append | 1192 | 0.0013 | 0.0018 | 1.6270 |
| feedback_observation_and_trust | 3576 | 0.0358 | 0.0887 | 160.4351 |
| feedback_state_update | 3576 | 0.1448 | 0.2211 | 580.5268 |
| final_context_budget | 1192 | 0.0075 | 0.0100 | 9.5591 |
| fusion_and_dense_floor | 1192 | 0.2411 | 0.3105 | 301.5083 |
| linucb_update | 14304 | 0.0240 | 0.0422 | 373.4721 |
| routing_and_gating | 1192 | 12.8800 | 17.6248 | 16577.6941 |

Feedback state: 1192 contexts; 837,632 numeric bytes; snapshot 925,304 bytes.

### Feedback mode: `none`

Stream wall time: 46836.69 ms; throughput: 25.45 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 1192 | 0.0080 | 0.0102 | 9.9673 |
| cluster_route | 1192 | 23.6205 | 35.4377 | 30814.9193 |
| dense_route | 1192 | 0.0109 | 0.0145 | 13.7197 |
| feedback_memory_append | 1192 | 0.0006 | 0.0008 | 0.7300 |
| feedback_observation_and_trust | 3576 | 0.0140 | 0.0602 | 97.5338 |
| feedback_state_update | 3576 | 0.0013 | 0.0050 | 8.4376 |
| final_context_budget | 1192 | 0.0075 | 0.0098 | 9.2822 |
| fusion_and_dense_floor | 1192 | 0.2460 | 0.3093 | 311.2027 |
| routing_and_gating | 1192 | 12.1140 | 16.3848 | 15291.1231 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 546,167 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
