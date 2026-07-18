# Task78 Handoff Source Manifest

- Git commit: `c382c06b88ce307c1e25672df4064c8db33fd683`
- Manifested files: 1,833
- Manifested bytes: 9.41 GiB
- Level 1 paper/result regeneration: **PASS**
- Level 2 exact final-result regeneration: **PASS_WITH_DOCUMENTED_NUMERICAL_BOUNDARIES**
- Level 2 fresh execution of every historical route run: **PARTIAL**
- Level 3 cross-backend encoder verification: **PASS_WITH_CROSS_BACKEND_NUMERICAL_EQUIVALENCE**

## Transfer Rule

For hardware-independent reproduction, transfer the processed records, fixed
embeddings/scale stores, selected retrieval checkpoints, tracked per-query
rankings/results, fixed answer/judge outputs, tokenizer cache, and environment
locks listed by this manifest. Do not transfer `.venv`, `.venv-rocm`, `.env`,
API keys, resumable checkpoints, or the machine-local ROCm installation.

The tracked result files are authoritative when an original historical cache is
unavailable. Re-encoding on CUDA, ROCm, or CPU is a Level 3 numerical check, not
a byte-identical substitute for the fixed Level 2 boundary.

## Remaining Fresh-Route Gaps

- technology/search 200k, 400k, and 638k do not all have a current hardened BM25 plus seeds-13/17/19 context-cluster cache set; tracked historical route outputs remain authoritative.
- science/search 20k/q200 and 200k do not have a complete current hardened embedding/ranking/cluster/score cache set; processed records and tracked outputs are present.
- PubMedQA, eManual, Banking77, and CUAD do not all have complete current hardened BM25/cluster/score caches for a fresh route-engine replay.
- The original historical CovidQA embedding cache remains absent, but the replacement canonical branch is complete: pinned ROCm embeddings, Dense/BM25/Hybrid, seeds-13/17/19 trust/no-feedback routes, exact score and cluster caches, cross-fitted budgets, and feedback recovery. Exact reproduction uses this fixed canonical generation; historical artifacts are retained only for comparison.

## Model Snapshots

- `sentence-transformers/all-MiniLM-L6-v2` @ `c9745ed1d9f207416be6d2e6f8de32d1f16199bf`: available locally
- `BAAI/bge-base-en-v1.5` @ `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`: available locally
- `intfloat/e5-base-v2` @ `f52bf8ec8c7124536f0efb74aca902b2995e5bcd`: available locally
- `cross-encoder/ms-marco-MiniLM-L-6-v2` @ `c5ee24cb16019beea0893ab7796b1df96625c6b8`: available locally

Before redistribution, dataset/model licenses and blinded-review constraints
must be checked. The manifest records source files; it does not grant a license
to redistribute model weights or raw restricted datasets.
