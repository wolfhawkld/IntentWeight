# Task78 Cross-Machine Reproduction And GPU Revalidation Summary

Status: GPU gate passed; final-result handoff source set ready; all-fresh-route
cache set remains partial

Date: 2026-07-18

## Verdict

The local AMD path is valid and reproducible. GPU execution requires the
project-specific activation script and external DXG adapter, not a stock WSL
ROCm installation:

```bash
source .venv-rocm/bin/activate-rocm
```

The activation exposes `$HOME/.local/rocdxg/lib`, sets
`HSA_ENABLE_DXG_DETECTION=1`, and uses `/dev/dxg`. The captured environment
reports PyTorch `2.9.1+rocm7.2.3.gitebc02d69`, HIP
`7.2.53211-c2d9476115`, and `AMD Radeon RX 9070 XT`.

The paper-facing final outputs can be reproduced on the colleague's machine
without an AMD, CUDA, or other GPU. Exact final-result reproduction must start
from the fixed records, embeddings/rankings, route outputs, and external API
outputs in the handoff manifest. Re-encoding is a separate end-to-end
numerical validation level and must not replace a historical fixed checkpoint
silently.

## GPU Code And Result Validation

The embedding cache now binds an optional immutable model revision and exact
array-content fingerprint. Corrupt arrays are rejected. LoTTE scale stores
record and validate model revision and embedding content, and adding a
fully-reused scale manifest does not rewrite the canonical array.

Five isolated formal reruns passed:

| Case | Embedding result | Top-10 result | Published metrics |
|---|---|---|---|
| MiniLM, technology/search 100k | numerical equivalent | members/order exact | exact |
| BGE-base, technology/search 100k | byte exact | exact | exact |
| E5-base, technology/search 100k | byte exact | exact | exact |
| MiniLM, recreation/search 100k | numerical equivalent | exact | exact |
| MiniLM, writing/search 100k | numerical equivalent | one duplicate-text order tie | exact |

The rebuilt technology/search 638k scale store contains 638,509 normalized
MiniLM rows. Its full Dense result preserves every published metric. One query
changes the non-ground-truth candidate at rank 10 within a `1.19e-7` score
boundary, so the result is classified as numerical/scientific equivalence,
not strict ranking identity.

## Reconstructed Data And External Checkpoints

- LoTTE science/search 200k: 201,098 corpus records and 596 queries, matched to
  tracked Task69 identities.
- CovidQA-RAG: 32,392 corpus records and 1,765 queries, including 1,726 queries
  with usable ground truth, matched to tracked identities.
- Deduplicated eManual: 1,729 corpus records and 132 queries, matched exactly.
- PubMedQA and deduplicated eManual rebuilt CPU checkpoints reproduce their
  historical top-10 rankings and all displayed metrics exactly.
- CovidQA's original Task69 embedding cache is not present locally. A complete
  replacement canonical branch now pins the model revision and regenerates
  Dense/BM25/Hybrid, trust/no-feedback routes, cross-fitted budgets, and
  feedback recovery. Its paired conclusions are stable, and a second ROCm run
  is byte-identical. All 584 Dense member-set changes versus history substitute
  identical normalized text within `4.77e-7` score spans. Exact reproduction
  therefore uses the fixed canonical rankings and score cache; historical
  outputs remain comparison evidence only.

After full paired validation, the manuscript's CovidQA point estimates were
switched coherently to the new canonical generation. Historical Task69
artifacts remain archived as comparison evidence and are not mixed with the
canonical values.

## What Must Be Given To The Colleague

For exact final-result and document regeneration:

1. The exact Git commit and all tracked experiment result JSON/CSV/ranking
   files.
2. The processed corpus/query files listed in the Task78 manifest.
3. Frozen corpus/query embeddings, LoTTE canonical scale stores, and row-index
   manifests.
4. Available Dense/BM25 rankings, PCA/KMeans cluster arrays, and exact score
   caches used by the current optimized route path.
5. The fixed Task63 answers/judgments and Task65.7 multi-judge outputs. API
   calls must not be repeated merely to reproduce existing tables.
6. The `cl100k_base` tokenizer cache and identity.
7. CPU package lock, TeX Live package lock, and the optional ROCm lock for
   end-to-end encoder checks.
8. `SHA256SUMS` and the JSON source manifest; verify these before execution.

The source manifest records its current file count and byte size in
`handoff-source-manifest.md`. It excludes
`.venv`, `.venv-rocm`, `.env`, API keys, local ROCm binaries, resumable
checkpoints, and stale Task69/70 smoke caches.

## Reproduction Levels

| Level | Current status | Hardware implication |
|---|---|---|
| Paper, tables, statistics, PDF | PASS | CPU only |
| Exact final-result regeneration from fixed per-query evidence | PASS with documented float boundaries | CPU only |
| Fresh execution of every historical route run | PARTIAL | GPU not needed, but several original untracked caches are absent |
| End-to-end encoder rerun | PASS with numerical-equivalence gates | GPU optional; backend changes may alter float ties |

The remaining fresh-route gaps cover some technology 200k/400k/638k,
science 20k/200k, and non-Covid external-dataset hardened BM25/cluster/score
cache sets.
Recovering the original caches from the machine that produced them is the only
way to claim exact historical route replay. Rebuilding them is valid as a new
numerical rerun, after which the downstream conclusions must be compared and
reported rather than assumed.

## Files

- `results/task78_gpu_revalidation/task78_gpu_formal.{json,md}`
- `results/task78_gpu_revalidation/task78_technology_scale_store.{json,md}`
- `results/task78_gpu_revalidation/task78_external_checkpoints.{json,md}`
- `results/task78_covidqa_canonical/comparison.{json,csv,md}`
- `data/task78_covidqa_canonical/`
- `reproducibility/task78/environment-{cpu,rocm,tex}.json`
- `reproducibility/task78/requirements-{cpu,rocm}-lock.txt`
- `reproducibility/task78/texlive-installed-lock.txt`
- `reproducibility/task78/handoff-source-manifest.{json,md}`
- `reproducibility/task78/SHA256SUMS`

Before actual transfer, dataset/model redistribution licenses and blinded
review constraints still require an explicit release audit. Model snapshots
should normally be fetched by pinned revision rather than copied blindly.
