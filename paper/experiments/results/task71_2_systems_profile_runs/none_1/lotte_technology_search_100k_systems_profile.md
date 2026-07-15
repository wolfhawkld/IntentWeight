# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 3546.12 |
| load_queries_json | 2.59 |
| load_corpus_embeddings | 386.84 |
| load_query_embeddings | 2.04 |
| load_dense_rankings | 399.38 |
| load_bm25_rankings | 259.74 |
| load_context_clusters | 252.48 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 20149.85 ms; throughput: 29.58 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0088 | 0.0432 | 12.6863 |
| cluster_route | 596 | 21.3346 | 39.4198 | 13347.7259 |
| dense_route | 596 | 0.0114 | 0.0222 | 16.3182 |
| feedback_memory_append | 596 | 0.0004 | 0.0006 | 0.3356 |
| feedback_observation_and_trust | 1788 | 0.0153 | 0.0902 | 96.5755 |
| feedback_state_update | 1788 | 0.0013 | 0.0067 | 5.0930 |
| final_context_budget | 596 | 0.0079 | 0.0117 | 5.7933 |
| fusion_and_dense_floor | 596 | 0.2603 | 0.4626 | 210.4693 |
| routing_and_gating | 596 | 8.6392 | 18.9250 | 6176.3575 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
