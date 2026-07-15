# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 2086.05 |
| load_queries_json | 2.83 |
| load_corpus_embeddings | 283.05 |
| load_query_embeddings | 1.33 |
| load_dense_rankings | 200.88 |
| load_bm25_rankings | 215.50 |
| load_context_clusters | 214.27 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 163665.61 ms; throughput: 29.13 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 4768 | 0.0080 | 0.0100 | 72.6801 |
| cluster_route | 4768 | 21.0477 | 33.4359 | 98679.1280 |
| dense_route | 4768 | 0.0104 | 0.0138 | 125.1437 |
| feedback_memory_append | 4768 | 0.0015 | 0.0020 | 7.5296 |
| feedback_observation_and_trust | 14304 | 0.0345 | 0.0843 | 642.6864 |
| feedback_state_update | 14304 | 0.1351 | 0.2053 | 2106.5449 |
| final_context_budget | 4768 | 0.0074 | 0.0101 | 47.6443 |
| fusion_and_dense_floor | 4768 | 0.2571 | 0.3456 | 1324.0424 |
| linucb_update | 57216 | 0.0186 | 0.0379 | 1284.6014 |
| routing_and_gating | 4768 | 13.1757 | 23.0415 | 60135.0562 |

Feedback state: 4768 contexts; 1,753,088 numeric bytes; snapshot 2,094,838 bytes.

### Feedback mode: `none`

Stream wall time: 152609.84 ms; throughput: 31.24 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 4768 | 0.0084 | 0.0109 | 44.7466 |
| cluster_route | 4768 | 22.7388 | 31.7330 | 99505.7175 |
| dense_route | 4768 | 0.0107 | 0.0143 | 62.9856 |
| feedback_memory_append | 4768 | 0.0005 | 0.0008 | 2.8023 |
| feedback_observation_and_trust | 14304 | 0.0145 | 0.0669 | 469.2787 |
| feedback_state_update | 14304 | 0.0013 | 0.0054 | 57.7991 |
| final_context_budget | 4768 | 0.0077 | 0.0106 | 38.9721 |
| fusion_and_dense_floor | 4768 | 0.2772 | 0.4023 | 1525.1909 |
| routing_and_gating | 4768 | 11.8344 | 16.0736 | 50362.5002 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 578,357 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
