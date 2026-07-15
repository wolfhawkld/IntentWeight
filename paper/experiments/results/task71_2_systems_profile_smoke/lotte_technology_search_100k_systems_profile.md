# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1561.79 |
| load_queries_json | 3.24 |
| load_corpus_embeddings | 224.08 |
| load_query_embeddings | 7.79 |
| load_dense_rankings | 141.03 |
| load_bm25_rankings | 144.16 |
| load_context_clusters | 156.74 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 6189.70 ms; throughput: 96.29 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0073 | 0.0083 | 4.4810 |
| cluster_route | 596 | 4.8255 | 7.5381 | 3078.8508 |
| dense_route | 596 | 0.0092 | 0.0112 | 5.8967 |
| feedback_memory_append | 596 | 0.0013 | 0.0018 | 0.8499 |
| feedback_observation_and_trust | 1788 | 0.0320 | 0.0752 | 73.8345 |
| feedback_state_update | 1788 | 0.1300 | 0.1930 | 250.8319 |
| final_context_budget | 596 | 0.0066 | 0.0082 | 4.0335 |
| fusion_and_dense_floor | 596 | 0.2566 | 0.3056 | 157.6324 |
| linucb_update | 7152 | 0.0219 | 0.0366 | 162.5740 |
| routing_and_gating | 596 | 4.0565 | 4.9876 | 2522.4785 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

### Feedback mode: `none`

Stream wall time: 6060.72 ms; throughput: 98.34 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0074 | 0.0094 | 4.7372 |
| cluster_route | 596 | 4.5673 | 9.9477 | 3165.4534 |
| dense_route | 596 | 0.0094 | 0.0121 | 6.2151 |
| feedback_memory_append | 596 | 0.0004 | 0.0007 | 0.2882 |
| feedback_observation_and_trust | 1788 | 0.0142 | 0.0729 | 68.4288 |
| feedback_state_update | 1788 | 0.0012 | 0.0050 | 4.2326 |
| final_context_budget | 596 | 0.0067 | 0.0083 | 4.1146 |
| fusion_and_dense_floor | 596 | 0.2658 | 0.3591 | 180.5580 |
| routing_and_gating | 596 | 3.8425 | 6.6704 | 2523.4967 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
