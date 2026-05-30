# Task36.1 Geometry Formula Definitions

Updated: 2026-05-30

## Status

Complete. This task is a paper-writing clarification, not a new experiment.

## Purpose

The full draft already used LoTTE geometry diagnostics as evidence for the
piecewise relevance-manifold framing, but the diagnostic metrics were only
described in prose and result tables. Task36.1 adds paper-facing mathematical
definitions for:

- $\mathrm{PCAvar@m}$;
- $\mathrm{PCAdim90}$;
- $\mathrm{NearestClusterHit@K}$;
- $\mathrm{ContextHit@K}$;
- $\mathrm{ContextRetention@K}$.

## Files Updated

- `paper/full_draft/05_experimental_setup.md`

## Claim Boundary

These formulas define diagnostic metrics. They do not turn the manifold
framing into a theorem-level proof. The paper should continue to state that
geometry diagnostics support the relevance-manifold assumption empirically, and
that dense retrieval remains necessary as a recall floor.

## Implementation Consistency

The definitions follow the existing Task30 implementation:

- PCA spectrum metrics are computed from mean-centered sampled corpus
  embeddings.
- nearest-cluster hit checks whether any ground-truth evidence cluster appears
  among the top-$K$ nearest KMeans centroids for a query context vector.
- context retention is the context-space top-$K$ hit rate divided by dense
  $\mathrm{Hit@K}$, matching the reported
  $\mathrm{ContextRetention@10}$ values.
