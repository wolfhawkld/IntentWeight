# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311; queries: 596.

This profile measures an artifact-backed MiniLM implementation. It separates cache materialization and online routing; it does not claim end-to-end provider cost, latency, or real-user RLHF efficacy.

## Cache Materialization

| Stage | ms |
|---|---:|
| load_corpus_json | 1311.47 |
| load_queries_json | 1.62 |
| load_corpus_embeddings | 154.28 |
| load_query_embeddings | 1.11 |
| load_dense_rankings | 143.38 |
| load_bm25_rankings | 141.67 |
| load_context_clusters | 146.87 |

## Warm Online Stages

### Feedback mode: `none`

Stream wall time: 6347.63 ms; throughput: 93.89 interactions/s.

| Stage | Calls | p50 ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0073 | 0.0087 | 4.5015 |
| cluster_route | 596 | 4.6442 | 11.2849 | 3395.8689 |
| dense_route | 596 | 0.0092 | 0.0124 | 8.8704 |
| feedback_memory_append | 596 | 0.0004 | 0.0005 | 0.2214 |
| feedback_observation | 1788 | 0.0018 | 0.0075 | 8.4746 |
| feedback_reward_measurement | 1788 | 0.0118 | 0.0530 | 45.5127 |
| feedback_state_update | 1788 | 0.0013 | 0.0057 | 5.6292 |
| feedback_trust_weighting | 1788 | 0.0010 | 0.0037 | 3.1057 |
| final_context_budget | 596 | 0.0071 | 0.0084 | 4.2144 |
| fusion_and_dense_floor | 596 | 0.2400 | 0.3093 | 158.6007 |
| routing_and_gating | 596 | 3.8734 | 7.5794 | 2612.9556 |

Feedback state: 0 contexts; 532,480 numeric bytes; snapshot 540,801 bytes.

## Interpretation Boundary

- Trust-weighted feedback timing establishes the local update overhead of the tested simulated-feedback controller.
- It does not establish real-user RLHF effectiveness; the recurrent/non-stationary effectiveness question remains Task72.
- Cached rankings and embeddings are explicitly separated from model encoding and offline artifact construction.
