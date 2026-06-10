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
- Completed gated cost-aware LinUCB formal run for
  `lotte_science_search_20k_q200` with the same multi-seed / multi-epoch
  protocol used by the main LoTTE technology results.
- Completed the calibrated context-budget protocol on
  `lotte_science_search_20k_q200`.

The 20k/q200 dense baseline result is:

| Dataset | Corpus chunks | Queries | GT refs | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `lotte_science_search_20k_q200` | 20,490 | 200 | 626 | 0.8950 | 0.7384 | 0.7504 | 0.6569 |

The 20k/q200 gated cost-aware LinUCB result is:

| Dataset | Seeds | Epochs | Hit@10 | EvidenceRecall@10 | MRR@10 | nDCG@10 | Avg source candidate cost | Dense query rate | LinUCB primary rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `lotte_science_search_20k_q200` | 3 | 8 | 0.9267 | 0.7406 | 0.7433 | 0.6444 | 207.67 | 0.6327 | 0.3673 |

This improves query-level sufficient-evidence Hit@10 over the dense baseline
from `0.8950` to `0.9267`, while preserving the same no-leakage prequential
simulated-feedback protocol. As in the main LoTTE technology experiments, this
should be interpreted as adaptive test-time feedback simulation rather than an
offline IID train/test claim.

The calibrated context-budget result selects `token_budget_r0.85_m4` using only
60 calibration queries, then freezes that policy on 140 test queries:

| Method | Seed | Frozen test Hit@10 | Hit delta vs dense | Final context token saving | Strict NI by CI |
|---|---:|---:|---:|---:|---:|
| dense adaptive truncation | - | 0.8857 | -0.71 pp | 22.69% | False |
| dense fixed top-8 | - | 0.8786 | -1.43 pp | 20.01% | False |
| dense fixed top-9 | - | 0.8786 | -1.43 pp | 9.52% | False |
| Task39 budgeted LinUCB | 13 | 0.9214 | +2.86 pp | 13.18% | True |
| Task39 budgeted LinUCB | 17 | 0.9071 | +1.43 pp | 14.31% | False |
| Task39 budgeted LinUCB | 19 | 0.9000 | +0.71 pp | 13.91% | False |

The science/search checkpoint therefore supports the main Task38 finding on a
second LoTTE domain: dense-only truncation saves more context tokens but loses
Hit@10, while the budgeted IntentWeight ranking keeps above-dense mean Hit@10
with roughly 13-14% final LLM evidence-context input token saving. The strict
seed-level non-inferiority CI remains conservative because the frozen test
split has only 140 queries; this should be reported transparently.

Artifacts:

- `paper/experiments/data/scale_store/lotte_science_search/`
- `paper/experiments/results/task39_lotte_science_20k_q200_dense/`
- `paper/experiments/results/task39_lotte_science_20k_q200_linucb/`
- `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.*`

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

The current 20k/q200 cross-domain validation slice is complete. A stronger
optional extension is to append the remaining `lotte_science_search_100k`
corpus rows into the same scale store, then repeat:

1. dense baseline through the scale-store path;
2. gated cost-aware LinUCB formal run;
3. calibrated context-budget validation.

That extension is useful if the paper needs a larger second-domain validation,
but it is not required to interpret the current Task39 checkpoint.
