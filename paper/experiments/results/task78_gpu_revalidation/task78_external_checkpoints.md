# Task78 External Checkpoint Audit

The tracked Task69 rankings remain the authoritative paper evidence. Rebuilt
embeddings are accepted as exact checkpoints only when both rankings and all
published metrics are identical.

| Dataset | Status | Top-10 members | Top-10 order | Metrics exact |
|---|---|---:|---:|---:|
| pubmedqa | EXACT | 1000/1000 | 1000/1000 | yes |
| emanual_deduplicated | EXACT | 132/132 | 132/132 | yes |
| covidqa | HISTORICAL_RANKINGS_REQUIRED | 1734/1765 | 1652/1765 | no |

A `HISTORICAL_RANKINGS_REQUIRED` row is not substituted into the manuscript.
Its rebuilt embeddings are useful for numerical reruns, while the tracked
historical rankings and downstream route outputs must be transferred for exact
paper-result regeneration.

For `covidqa`, 31 query top-10 member sets
change; the largest changed-candidate score span under the rebuilt
embeddings is 1.19e-07, and 1 query
changes Hit@10. This is a numerical tie boundary, but it is not exact
paper-result equivalence.
