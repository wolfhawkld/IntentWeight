# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 4523.93 |
| load_queries_json | 6.52 |
| load_corpus_embeddings | 825.56 |
| load_query_embeddings | 1.53 |
| load_dense_rankings | 536.00 |
| load_bm25_rankings | 503.21 |
| load_context_clusters | 443.80 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 23507.29 ms; throughput: 25.35 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0083 | 0.0101 | 5.2606 |
| cluster_route | 596 | 22.7413 | 34.7681 | 14910.0092 |
| dense_route | 596 | 0.0108 | 0.0139 | 18.8425 |
| feedback_memory_append | 596 | 0.0014 | 0.0021 | 0.9083 |
| feedback_observation_and_trust | 1788 | 0.0408 | 0.1043 | 104.9709 |
| feedback_state_update | 1788 | 0.1476 | 0.2292 | 290.3614 |
| final_context_budget | 596 | 0.0080 | 0.0119 | 5.2172 |
| fusion_and_dense_floor | 596 | 0.2507 | 0.3445 | 161.0211 |
| linucb_update | 7152 | 0.0239 | 0.0427 | 186.9818 |
| routing_and_gating | 596 | 12.4651 | 16.7235 | 7753.3307 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
