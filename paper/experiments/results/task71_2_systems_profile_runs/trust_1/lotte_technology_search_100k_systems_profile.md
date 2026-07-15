# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 4168.77 |
| load_queries_json | 2.22 |
| load_corpus_embeddings | 620.25 |
| load_query_embeddings | 2.08 |
| load_dense_rankings | 465.51 |
| load_bm25_rankings | 574.94 |
| load_context_clusters | 865.23 |

## Warm Online Stages

### Feedback mode: `trust_weighted`

Stream wall time: 23783.90 ms; throughput: 25.06 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0080 | 0.0099 | 13.3754 |
| cluster_route | 596 | 22.8004 | 36.3359 | 15013.6979 |
| dense_route | 596 | 0.0106 | 0.0141 | 19.5900 |
| feedback_memory_append | 596 | 0.0015 | 0.0022 | 1.0041 |
| feedback_observation_and_trust | 1788 | 0.0431 | 0.1006 | 104.2651 |
| feedback_state_update | 1788 | 0.1512 | 0.2297 | 313.4358 |
| final_context_budget | 596 | 0.0071 | 0.0098 | 4.5405 |
| fusion_and_dense_floor | 596 | 0.2498 | 0.3436 | 159.6196 |
| linucb_update | 7152 | 0.0242 | 0.0433 | 201.7994 |
| routing_and_gating | 596 | 12.5145 | 16.7469 | 7906.8014 |

Feedback state: 596 contexts; 685,056 numeric bytes; snapshot 730,371 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
