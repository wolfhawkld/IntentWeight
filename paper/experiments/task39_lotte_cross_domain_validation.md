# Task39 LoTTE Cross-domain Validation

## Goal

Task39 starts the cross-domain replication work requested after Task38. The goal
is to test whether the context-budget / minimum-sufficient-context finding is
limited to `LoTTE technology/search` or also appears in other LoTTE domains.

The first target domain is `science/search`.

## Current Checkpoint

Completed:

- Downloaded and cached LoTTE `science/search` locally.
- Built processed datasets:
  - `lotte_science_search_100k`
  - `lotte_science_search_20k_q200`
- Built a reusable `lotte_science_search` scale store for
  `lotte_science_search_20k_q200`.
- Completed dense baseline for `lotte_science_search_20k_q200`.

The 20k/q200 dense baseline result is:

| Dataset | Corpus chunks | Queries | GT refs | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `lotte_science_search_20k_q200` | 20,490 | 200 | 626 | 0.8950 | 0.7384 | 0.7504 | 0.6569 |

Artifacts:

- `paper/experiments/data/scale_store/lotte_science_search/`
- `paper/experiments/results/task39_lotte_science_20k_q200_dense/`

## Incremental Embedding Note

Directly running dense baseline on a new LoTTE domain caused a long monolithic
corpus-embedding job. That path is risky because the default embedding cache is
written only after the full corpus has been encoded.

Task39 therefore switches cross-domain scale-up to the LoTTE scale-store path.
`lotte_scale_store.py` now supports initializing an empty store with
`--streaming-append`, so new domains can be encoded in bounded chunks and later
extended to larger slices by appending only missing corpus rows.

The first science store was built with:

```bash
.venv/bin/python paper/experiments/scripts/lotte_scale_store.py \
  --datasets lotte_science_search_20k_q200 \
  --canonical-name lotte_science_search \
  --store-dir paper/experiments/data/scale_store/lotte_science_search \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --compute-missing --streaming-append \
  --local-files-only --device cpu \
  --batch-size 64 --encode-chunk-size 500
```

Resulting store:

| Store | Rows | Dim | Encode elapsed |
|---|---:|---:|---:|
| `lotte_science_search` | 20,490 | 384 | 750.405 sec |

## Next Step

Resume Task39 by running cost-aware LinUCB on
`lotte_science_search_20k_q200`, preferably with `--use-scale-store` and:

```text
--scale-store-dir paper/experiments/data/scale_store/lotte_science_search
--scale-store-canonical-name lotte_science_search
```

After LinUCB ranking is available, run the same Task38 calibrated context-budget
protocol on science/search and compare against dense adaptive truncation.
