# Task69 Runtime Optimization Plan

Updated: 2026-07-11

## Scope

This document records the runtime optimizations identified after the formal
Task69.3 LoTTE science/search 400k trust-weighted experiment was stopped
following its first completed legacy seed. The partial legacy run remains
provenance only and is not mixed with optimized artifacts.
They are implementation optimizations only. They must not change the frozen
Task69 common protocol, retrieval candidate definition, routing policy,
feedback simulation, seeds, epochs, or reported metrics.

Do not mix artifacts from the legacy and optimized retrieval engines in a
single result table. The pending 400k run will start afresh with the optimized
engine after the validation gate is complete.

## Observed Bottlenecks

The current route runner executes:

`routing mode x seed x epoch x query`.

For the formal 400k run, this is:

`2 modes x 3 seeds x 8 epochs x 596 queries = 28,608 interactions`.

The dominant repeated work is cluster-local retrieval in
`linucb_online_baseline.retrieve_from_arms`:

- scan all corpus arm labels with `np.isin`;
- gather the selected-arm embedding rows;
- score the gathered rows against the query;
- select and sort the local top-k candidates.

At 400k chunks, selecting three of 32 arms evaluates roughly 37.5k embedding
rows per interaction, in addition to scanning all 400k arm labels. The active
experiment also repeats LinUCB scoring across all arms and rebuilds/sorts the
growing feedback-neighbor history at every interaction.

## Optimization Order

### 1. Exact Query-Corpus Score Cache

Precompute and memory-map the full static query-corpus score row for every
query. At online routing time, select the current arms, gather their cached
scores, and execute the existing candidate-union, `argpartition`, and
tie-break logic unchanged.

Caching only the per-arm top `cluster_depth` candidates would be compact, but
cannot guarantee exact behavior when scores tie at a local top-k boundary. The
full score cache preserves the legacy candidate set and tie behavior.

Implementation requirements:

- cache memory-mapped `float32` score rows and precomputed arm-row indices;
- preserve the existing tie-break order: descending score, then ascending
  corpus index, by keeping the legacy candidate union and ranking operation;
- version the score artifact with corpus/query embedding fingerprints and the
  model identifier;
- store the cache under the ignored retrieval-artifact directory;
- retain the legacy on-demand retrieval path behind an explicit switch for
  regression testing.

Expected impact: largest safe improvement to repeated cluster-local retrieval.
The local 400k score cache is approximately 1 GiB and remains Git ignored.

### 2. Precompute Arm Row Indices

Build `arm -> sorted corpus row indices` once for each seed. This replaces the
per-interaction `np.isin(arm_labels, selected_arms)` scan. When a legacy
on-demand retrieval path is used, concatenate and sort the selected arm index
arrays so its candidate order matches `np.flatnonzero(np.isin(...))` exactly.

Expected impact: removes repeated full-corpus label scans and allocation.

### 3. Remove Duplicate LinUCB Factorizations

`GlobalLinUCBPolicy.scores` currently solves each arm's linear system twice:
once for the point estimate and once for the uncertainty term. Replace these
with one solve using two right-hand sides, containing `b` and the current
context. This preserves the existing linear-system formulation while avoiding
the duplicate factorization.

Do not introduce inverse-matrix or Sherman-Morrison updates in the first
optimization pass. Those may be faster but require a separate numerical
stability evaluation because small score changes can alter thresholded routes.

Expected impact: approximately halves the solve work within policy scoring.

### 4. Compact Exact Feedback-Neighborhood Selection

Replace repeated list-to-array conversion and complete sorting in
`local_feedback_boosts` with preallocated history arrays and `np.argpartition`
for exact top-`feedback_k` selection. Preserve the subsequent distance and
reward weighting calculation and deterministic tie behavior.

Expected impact: secondary reduction in Python allocation and sort overhead.

### 5. Progress And Recovery Improvements

Add epoch-level progress records and, if practical, resumable epoch checkpoints
containing policy state, RNG state, feedback history, and metric accumulators.
This does not materially reduce runtime, but prevents long 400k runs from
appearing stalled and limits lost work if an external interruption occurs.

## GPU Follow-Up

The current AMD ROCm GPU accelerates embedding construction. The long-running
route phase remains CPU-bound. After the CPU exact-cache implementation passes
regression tests, evaluate optional GPU batching for the static query-arm
candidate precomputation only.

GPU precomputation must be treated as a separate execution backend and may not
replace the CPU exact path until ranking and metric equivalence have been
demonstrated. It must not change online LinUCB, feedback, fusion, or budget
semantics.

## Validation Gate

Before an optimized implementation is used for a new paper-facing result:

1. Run legacy and optimized paths on LoTTE technology/search 100k for seeds
   `13,17,19`, both `full_multi_route` and `gated_cost_aware`, and both
   `trust_weighted` and `none` feedback modes.
2. Compare final per-query rankings, route decisions, confidence values, route
   counts, source costs, and all reported retrieval metrics.
3. Require exact equality where deterministic ordering is preserved. If a
   numerically equivalent optimization changes floating-point traces, report
   the difference explicitly and rerun all paired comparisons under one
   versioned backend; do not mix implementations within a table.
4. Record wall-clock time, peak RSS, corpus size, query count, seeds, epochs,
   and hardware for legacy versus optimized runs.
5. Only then use the optimized backend for pending Task69 datasets or any
   necessary rerun. Existing completed artifacts remain valid provenance for
   their original implementation version.

## Expected Runtime Target

Without a benchmark, no speedup is guaranteed. The conservative target for the
combined CPU-exact first pass is a 2-3x end-to-end improvement on the 400k
formal route run. The exact candidate cache is expected to contribute most;
more aggressive gains require separate numerical validation.

## 2026-07-11 Validation Status

The exact-cache backend passed the full LoTTE technology/search 100k
trust-weighted validation for seeds `13`, `17`, and `19`, both
`full_multi_route` and `gated_cost_aware`, over eight epochs and 596 test
queries. Final rankings and all non-runtime metrics matched the legacy
on-demand backend exactly. End-to-end elapsed time decreased from `461.806 s`
to `133.777 s` (`3.452x`). The detailed protocol and comparison are recorded
in `task69_runtime_optimization_validation.md`.

The matching no-feedback comparison also passed on 2026-07-12: final rankings
and all non-runtime metrics were exactly equal, while elapsed time decreased
from `1022.613 s` to `95.128 s` (`10.750x`). The full 100k validation gate is
therefore complete for both Task69.3 feedback conditions. No optimized 400k
route execution has been started yet.
