# Task78 Cross-Machine Reproduction And GPU Revalidation Plan

Status: in progress; GPU revalidation and final-result handoff audit complete,
all-fresh-route checkpoint completion pending

Date: 2026-07-18

## Objective

Create a hardware-independent checkpoint package from which a colleague can
recompute every paper-facing retrieval, routing, calibration, statistical, and
document result without requiring the local AMD GPU. Before freezing that
package, rerun the experiments whose canonical embeddings were generated on
the local RX 9070 XT and compare both code paths and outputs with the existing
evidence.

This task is a reproducibility gate. It must not tune policies, replace frozen
splits, search for favorable seeds, or alter a scientific claim because a new
backend produces harmless floating-point differences.

## Three Reproduction Levels

### Level 1: Paper And Result Regeneration

Required payload:

- the exact Git commit;
- tracked result JSON/CSV files, fixed answer and judge outputs, and figure
  data;
- the CPU environment lock and TeX environment.

This level regenerates tables, figures, statistics derived from tracked result
files, and submission PDFs. It does not rerun retrieval or routing and does not
need a GPU or raw datasets.

### Level 2: Fixed-Checkpoint Scientific Rerun

Required payload in addition to Level 1:

- exact processed corpus/query JSON files and their SHA-256 digests;
- normalized corpus/query embedding arrays in record order;
- LoTTE canonical scale stores and per-scale row-index manifests;
- Dense and BM25 candidate rankings;
- PCA/KMeans context-cluster arrays for seeds 13/17/19;
- exact query-by-corpus score arrays where the cached-exact route engine is
  used;
- tokenizer cache/encoding identity;
- frozen external answer and judge outputs.

This is the recommended colleague handoff. The colleague starts after the
hardware-sensitive encoder boundary and can freshly rerun routing, simulated
feedback, budget calibration, paired statistics, and manuscript generation.
The GPU vendor is then not an experimental variable.

### Level 3: End-To-End Encoder Rerun

Required payload in addition to Level 2 or equivalent download instructions:

- exact model snapshots or immutable model revisions;
- exact dataset revisions and preprocessing inputs;
- CPU/ROCm software locks and system manifests.

This level verifies semantic equivalence but is not expected to produce
byte-identical embeddings across CPU, CUDA, and ROCm. Small floating-point
differences are acceptable only when ranking and metric equivalence gates pass.

## Frozen Evidence Scope

The Level 2 package covers the settings used by the current manuscript:

- LoTTE technology/search 100k, 200k, 400k, and 638k;
- LoTTE science/search 20k/q200, 100k, 200k, and 400k;
- LoTTE recreation/search and writing/search 100k;
- PubMedQA native full, CovidQA-RAG native full, and eManual deduplicated;
- Banking77 mechanism-only and CUAD sparse-GT boundary artifacts;
- MiniLM, BGE-base, and E5-base matched-backbone results on LoTTE
  technology/search 100k;
- Task47 reranker inputs and outputs;
- Task63/65 answer and multi-judge outputs.

FinQA, TechQA, LegalBench-RAG, science/search native full, and other deferred
datasets are excluded unless they later enter a submitted table or claim.

## Pinned Model And Dataset Identities

| Asset | Revision | Encoding contract |
|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` | no prefix |
| `BAAI/bge-base-en-v1.5` | `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` | BGE query instruction; no corpus prefix |
| `intfloat/e5-base-v2` | `f52bf8ec8c7124536f0efb74aca902b2995e5bcd` | `query: ` and `passage: ` |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | `c5ee24cb16019beea0893ab7796b1df96625c6b8` | query-passage pairs |
| `mteb/LoTTE` | `a9006514d20ec3353082b4272bf46a20dd96a195` | processed by the checked-in LoTTE script |
| `qiaojin/PubMedQA` | `9001f2853fb87cab8d220904e0de81ac6973b318` | checked-in preprocessing contract |

The BGE query prefix is exactly
`Represent this sentence for searching relevant passages: `, including the
trailing space.

## Local ROCm Contract

Every GPU command must run outside the restricted sandbox and begin with:

```bash
source .venv-rocm/bin/activate-rocm
```

That activation sets:

- `ROCM_PATH=$HOME/.local/rocm-7.2.3-root/opt/rocm-7.2.3`;
- `HSA_ENABLE_DXG_DETECTION=1`;
- `LD_LIBRARY_PATH` entries for `$HOME/.local/rocdxg/lib` and
  `/usr/lib/wsl/lib`.

The validated external adapter is
`$HOME/.local/rocdxg/lib/librocdxg.so.1.2.0`; `/dev/dxg` must be visible.
PyTorch must report ROCm 7.2.3 and `AMD Radeon RX 9070 XT` before encoding.

## GPU Revalidation Matrix

Formal isolated reruns cover every canonical GPU-generated embedding family:

| Case | Dataset | Model | Reference depth |
|---|---|---|---:|
| Task47 candidates | technology/search 100k | MiniLM | 50 |
| Task52 strong dense | technology/search 100k | BGE-base | 50 |
| Task53 third backbone | technology/search 100k | E5-base | 50 |
| Task73 domain expansion | recreation/search 100k | MiniLM | 10 |
| Task73 domain expansion | writing/search 100k | MiniLM | 10 |

Technology/search 638k MiniLM is additionally rebuilt as the complete
canonical scale-store handoff boundary. Small external MiniLM embeddings and
missing per-scale manifests are completed after the five equivalence cases.

## Validation Gates

Each case is written to an isolated ignored directory and must satisfy:

1. exact dataset record count, ID order, text fingerprint, model revision, and
   prefix contract;
2. two-dimensional float32 arrays, expected dimension, finite values, and
   normalized rows;
3. minimum corresponding-row cosine similarity at least 0.99999 against the
   canonical array;
4. exact top-10 member equality for every query; ordered equality and top-50
   equality are reported separately. A near-tied order change is acceptable
   only when the member set and metrics are unchanged and the affected texts,
   scores, and ground truth are explicitly audited. A cross-hardware member
   change is reported as a numerical boundary, rather than strict equivalence,
   only when the changed candidates are within `1e-6`, no changed candidate is
   ground truth, and every published metric is unchanged;
5. identical retrieval metrics at all published cutoffs;
6. no writes to canonical result, embedding, scale-store, or artifact paths;
7. downstream route/checkpoint audits pass against the fixed transferred
   fingerprints.

Byte equality is reported but is not a cross-hardware acceptance criterion.
Any top-10 disagreement is investigated at score margins before acceptance; it
is never silently rounded away.

## Provenance Hardening

Before formal execution:

- embedding caches bind an explicit model revision when supplied and store an
  exact numeric-content fingerprint;
- corrupt embedding content is rejected and recomputed;
- canonical scale stores record and validate model revision and embedding
  content identity;
- all model, data, array, ranking, and fixed API artifacts receive portable
  SHA-256 entries in the handoff manifest;
- CPU and ROCm package locks, Python/library versions, BLAS/thread settings,
  GPU/ROCm identity, Git commit, and dirty state are recorded.

These additions change cache eligibility and audit metadata only. Dense
scoring, candidate selection, route fusion, feedback, budgeting, and metrics
remain unchanged.

## Missing Local Inputs To Reconstruct

The initial audit found that the current machine is not yet a complete Level 2
source. At minimum it must reconstruct:

- LoTTE science/search 200k processed corpus/query files;
- CovidQA-RAG processed corpus/query files from the pinned local/downloaded
  parquet inputs;
- eManual deduplicated processed corpus/query files;
- the technology/search canonical MiniLM scale store through 638k;
- missing external-dataset and query embedding checkpoints required by the
  frozen evidence set.

Historical cache filenames referenced by obsolete experiments are not copied
merely to satisfy old absolute paths. The handoff uses one verified canonical
artifact per current input identity and maps it through a portable manifest.

## Handoff Layout

```text
intentroute-task78-handoff/
  MANIFEST.json
  SHA256SUMS
  README.md
  code/
  environments/
  data/processed/
  checkpoints/embeddings/
  checkpoints/scale_store/
  checkpoints/retrieval_artifacts/
  fixed_external_outputs/
  reference_results/
```

Paths in the manifest are relative to the handoff root. The package excludes
`.venv`, `.venv-rocm`, `.env`, API keys, machine-local ROCm installations,
stale smoke caches, and resumable checkpoints that could bypass a requested
fresh run. Dataset/model licenses are audited before any raw data or weights
are redistributed.

## Completion Definition

Task78 is complete only when:

- all five GPU equivalence cases pass or have a documented investigated
  boundary;
- the 638k technology scale store and current paper-evidence checkpoint set are
  complete;
- the portable manifest reports no missing required Level 2 artifact;
- a clean-room verification command validates every checksum and regenerates
  a representative route, calibration, statistics, and paper build;
- the final report distinguishes exact, numerical, ranking, metric, and
  scientific equivalence.

Only after this gate should the payload be transferred to the colleague and
Task79 LLMLingua-2 work begin.

## Progress On 2026-07-18

- The external DXG adapter path was recovered and verified. The formal ROCm
  environment sees `/dev/dxg`, PyTorch/HIP 7.2.3, and the RX 9070 XT.
- All five formal GPU cases passed. BGE and E5 reproduced exactly; MiniLM
  reproduced with cosine similarity above the gate, exact published metrics,
  and only one duplicate-text order tie in writing/search.
- The technology/search 638k canonical scale store was rebuilt. All published
  Dense metrics are exact; one non-ground-truth rank-10 membership boundary is
  separated by approximately float32 precision and is recorded rather than
  called strict equality.
- Missing science/search 200k, CovidQA, and deduplicated eManual processed
  records were reconstructed and matched the tracked data identities. The
  science 200k row manifest was added without rewriting its canonical store.
- PubMedQA and deduplicated eManual fixed MiniLM checkpoints reproduce the
  tracked Task69 top-10 rankings and metrics exactly. The provisional CPU-only
  CovidQA audit was superseded by a complete pinned-revision ROCm canonical
  rerun. Versus history, all 584 Dense member-set changes replace identical
  normalized text within `4.77e-7` score spans, paired Hit changes are not
  significant, and the cross-fitted Hit delta remains exactly `-0.212437` pp.
  The paper now uses one coherent canonical generation with `9.00%` token
  saving; historical Task69 artifacts remain comparison evidence only.
- CPU, ROCm, and TinyTeX locks are captured with portable paths. The current
  file count and byte size are recorded by the generated handoff manifest
  rather than duplicated here.
- Level 1 and exact final-result regeneration are ready. A cold fresh replay
  of every historical route run remains partial because several untracked
  historical BM25/cluster/score caches are absent. These must either be
  recovered from the machine that produced them or rebuilt and explicitly
  treated as a new numerical rerun.
