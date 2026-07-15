# Task71.2 Systems and Feedback Operational Profile

Dataset: `lotte_technology_search_100k`. Corpus: 101,311 chunks; queries: 596.

## Measurement Protocol

- Three independent CPU processes per feedback mode; one prequential epoch per process.
- MiniLM artifacts were pre-existing and loaded from local cache. Dense and BM25 routes are cached ranking lookups; cluster-local retrieval uses the declared `on_demand` exact scorer.
- The common full multi-route policy is held fixed. This is an operational profile, not a retrieval-quality comparison or a real-user RLHF evaluation.
- Per-stage p50/p95 values are first computed within each run, then summarized across the three runs; they are not pooled into a synthetic request-level distribution.

## Warm Online Workload

| Feedback mode | Median stream wall ms (range) | Median interactions/s (range) | Median peak RSS GiB (range) |
|---|---:|---:|---:|
| `none` | 6347.63 (5743.37-6798.97) | 93.89 (87.66-103.77) | 0.939 (0.939-0.940) |
| `trust_weighted` | 6429.92 (6174.15-6570.04) | 92.69 (90.71-96.53) | 0.939 (0.939-0.940) |

## Stage Timing

Values are medians of run-level timing summaries. Stage p95 is a within-run p95, then the median across runs.

### `none`

| Stage | Calls/run | p50 ms | p95 ms | Total ms/run |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0074 | 0.0087 | 4.6884 |
| cluster_route | 596 | 4.6442 | 11.2849 | 3395.8689 |
| dense_route | 596 | 0.0092 | 0.0122 | 6.1569 |
| feedback_memory_append | 596 | 0.0004 | 0.0005 | 0.2412 |
| feedback_observation | 1788 | 0.0018 | 0.0075 | 6.4987 |
| feedback_reward_measurement | 1788 | 0.0118 | 0.0530 | 42.9501 |
| feedback_state_update | 1788 | 0.0013 | 0.0057 | 4.8194 |
| feedback_trust_weighting | 1788 | 0.0010 | 0.0031 | 2.8335 |
| final_context_budget | 596 | 0.0071 | 0.0084 | 4.2144 |
| fusion_and_dense_floor | 596 | 0.2400 | 0.3093 | 158.6007 |
| routing_and_gating | 596 | 3.8734 | 7.5794 | 2612.9556 |

Feedback-state median: 0 contexts; 532480 numeric bytes; 540801-byte snapshot.

### `trust_weighted`

| Stage | Calls/run | p50 ms | p95 ms | Total ms/run |
|---|---:|---:|---:|---:|
| bm25_route | 596 | 0.0072 | 0.0081 | 4.3953 |
| cluster_route | 596 | 4.7890 | 8.6815 | 3190.3266 |
| dense_route | 596 | 0.0090 | 0.0109 | 5.4824 |
| feedback_memory_append | 596 | 0.0013 | 0.0018 | 0.8394 |
| feedback_observation | 1788 | 0.0073 | 0.0225 | 21.3374 |
| feedback_reward_measurement | 1788 | 0.0193 | 0.0509 | 50.5920 |
| feedback_state_update | 1788 | 0.1325 | 0.2107 | 266.6400 |
| feedback_trust_weighting | 1788 | 0.0018 | 0.0041 | 4.3071 |
| final_context_budget | 596 | 0.0070 | 0.0080 | 4.1169 |
| fusion_and_dense_floor | 596 | 0.2387 | 0.2992 | 152.3694 |
| linucb_update | 7152 | 0.0226 | 0.0411 | 171.2528 |
| routing_and_gating | 596 | 4.2167 | 5.6812 | 2639.9535 |

Feedback-state median: 596 contexts; 685056 numeric bytes; 730371-byte snapshot.

## Query-Encoding Microbenchmark

MiniLM CPU load: 4591.78 ms; 64 single-query samples, p50 7.1559 ms, p95 8.6183 ms.

## Interpretation Boundary

- Cluster-local retrieval dominates the measured warm route. The trust-weighting and individual LinUCB-update stages are reported separately rather than attributed to retrieval quality.
- The `none` control still constructs controlled synthetic observations for a comparable diagnostic path, but assigns zero update weight: it performs no LinUCB update and retains no feedback-memory records.
- Trust-weighted versus `none` wall-time runs are independent process launches, not a paired latency significance test; changing system load can affect their absolute difference.
- The feedback snapshot uses pickle only as a state-size microbenchmark. It is not a production persistence protocol.
- This operational profile does not establish real-user RLHF efficacy. Task72 remains the controlled recurrent-feedback effectiveness evaluation.
- Final-context token savings and conditional LLM input-cost calculations remain traceable to the calibrated Task69 evidence, not to this fixed-top-k operational workload.
