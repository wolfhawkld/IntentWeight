# Task72.2 Runtime Integrity Hardening

Date: 2026-07-15

## Purpose

Close the runtime-provenance risks identified after the Task69 science/search
400k review before any Task73 domain expansion. This task changes cache and
checkpoint integrity controls only. It does not change retrieval scores,
routing policy, feedback semantics, fusion, final-context budgeting, or any
paper-facing Task69 result.

## Risks Addressed

1. Embedding-dependent artifacts were keyed by records and model name but not
   by the actual embedding values. A changed model revision, prefix, or scale
   store could therefore reuse an incompatible score, Dense, or context cache.
2. Seed checkpoints did not bind themselves to source code, input content,
   embeddings, or retrieval artifacts, and restore accepted structurally
   incomplete rankings and metrics.
3. `random_partition_*` shuffled active arm labels while cached retrieval kept
   arm-row indices from the original partition.
4. The runner exposed one cumulative elapsed value without making checkpoint
   restores and actual seed computation distinguishable.

## Implemented Controls

### Embedding-bound artifacts

`large_scale_artifacts.py` now computes a chunked SHA-256 fingerprint over an
embedding array's shape, dtype, and exact bytes. Dense rankings, context
clusters, and query-corpus score artifacts bind both corpus and query
embedding fingerprints into their payload fingerprint and metadata.

The artifact outputs also carry verified logical-content fingerprints:
canonical ranking mappings for Dense/BM25, all persisted context arrays for
PCA/KMeans artifacts, and the complete float32 score matrix for score mmap
artifacts. A content mismatch rejects the cache. Existing structurally valid
BM25 metadata can be upgraded in place because BM25 does not depend on the new
embedding key; embedding-dependent legacy artifacts cannot be upgraded by
identity alone.

The caller computes each large-array fingerprint once and reuses it across all
artifact loaders. BM25 artifacts remain keyed only by their actual lexical
inputs and are not invalidated unnecessarily.

Existing embedding-dependent v1 artifacts remain historical local caches, but
they cannot satisfy a new embedding-bound cache lookup. The first future run
under the hardened implementation will create a new artifact identity.

### Checkpoint v2

Each seed checkpoint now binds:

- a checkpoint format version;
- a SHA-256 fingerprint of the routing implementation and its direct source
  dependencies;
- Python, NumPy, SciPy, and scikit-learn versions, preventing mixed-version
  seed restoration within one result family;
- ordered corpus/query record fingerprints;
- exact corpus/query embedding fingerprints;
- Dense, BM25, context-cluster, and query-corpus-score artifact identities and
  verified logical-content checksums;
- corpus/query counts, protocol parameters, seed, routing mode, epochs,
  expected interactions, and allowed final ranking depths.

Restore rejects a checkpoint unless it has exact selected-query coverage,
valid unique ranking IDs, an allowed ranking depth, matching seed/mode/epoch
metrics, the expected interaction count, the expected epoch-metric count, and
query-trace coverage when traces were requested. Legacy checkpoints therefore
cannot silently resume a new run. They remain valid provenance for the
completed historical result that produced them.

### Random-partition consistency

When a random-partition ablation changes arm labels, the cached backend now
rebuilds arm-row indices from that active partition. Before retrieval, the
runner checks that arm-row arrays are disjoint, cover the full corpus, remain
in range, and match every active label.

The regression fixture explicitly demonstrates that stale pre-shuffle indices
would change at least one ranking, then requires the fixed cached backend to
match legacy on-demand retrieval exactly.

### Runtime audit fields

Every routing-mode result now records:

- artifact cache state;
- checkpoint hits, misses, bypasses, and miss reasons;
- preparation time;
- actual seed-computation time;
- checkpoint read and write time;
- routing-mode wall time; and
- a runtime measurement class.

The legacy cumulative `elapsed_sec` field is retained for schema compatibility,
but it is not sufficient for a performance claim.

## Timing Protocol

Future timing checks must report these cases separately:

1. **Cold construction:** new embedding/artifact location, new output
   location, and checkpoint resume disabled.
2. **Warm artifact execution:** existing validated artifacts, checkpoint
   resume disabled with `--no-resume-checkpoints` or a fresh output location.
3. **Checkpoint restoration:** same validated artifacts and output location,
   with every planned seed restored from checkpoint v2.

Checkpoint restoration time is recovery overhead, not experiment execution
time. Historical 400k values that represent cache hits or checkpoint restores
must not be used as cold-start or end-to-end speed measurements.

## Validation

- 26 focused runtime, artifact, frozen-policy, and integration tests pass,
  including score-cache corruption detection and exact repair.
- All 121 cache tests pass when discovery is run with an isolated `sys.argv`.
  The stock `python -m unittest discover ...` form passes 120 and exposes the
  pre-existing `test_download_parquet` argv-isolation issue; its direct module
  entry point also passes both download tests.
- Python compilation and `git diff --check` pass for the changed sources.
- The chunked hasher processed the real `(596, 400902)` float32 science/search
  score mmap (912 MiB) read-only in 1.156 seconds without materializing the
  matrix in RAM. Its logical-content SHA-256 is
  `16a827132a38eb9f52a7d799905163d1e6872e98d7c344b7163a4290d98e83b5`.
- No tracked Task69 result, ranking, checkpoint, table, figure, or manuscript
  file was regenerated by this hardening task.

## Effect On Existing Evidence

The completed Task69 400k quality results remain usable under their recorded
backend and provenance. Earlier audits already established complete formal
coverage and exact agreement between the current 596-query score cache and
the embeddings from which it was built. The new controls prevent future stale
reuse; they do not retroactively alter those rankings or metrics.

The random-partition fix does not affect the completed science/search 400k
`full_multi_route` or `gated_cost_aware` runs. Any future cached
`random_partition_*` ablation must use the corrected implementation.

Task73 may proceed after this change is reviewed and committed. It should use
fresh output directories so historical checkpoints remain immutable.
