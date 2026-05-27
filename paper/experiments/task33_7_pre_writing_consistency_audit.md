# Task33.7 Pre-Writing Consistency Audit

Updated: 2026-05-27

## Purpose

Task33.7 is a final evidence-consistency audit before expanding the paper
draft. It does not add new experiments. It checks whether the current claims,
metrics, result tables, and artifact references are aligned after Task33.1-33.6.

## Audit Result

No blocking evidence-chain inconsistency remains after this audit.

The paper-ready claim should stay bounded:

> IntentWeight is a feedback-driven adaptive retrieval and context-budget
> controller for vertical-domain RAG. On LoTTE technology/search 100k-638k, the
> conservative Task29-C policy reduces final retrieved context tokens by about
> 4.7-5.3% while preserving dense-level Hit@10, with above-dense mean Hit@10 on
> 200k, 400k, and 638k. Feedback, geometry, and route confidence provide useful
> control signals, but dense retrieval remains an important recall floor.

The paper should not claim universal dense replacement, theorem-level manifold
proof, real-human-feedback validation, or full end-to-end answer-quality
superiority.

## Canonical Metric Vocabulary

| Metric | Canonical meaning | Paper use |
|---|---|---|
| `Hit@K` | Query-level success: at least one GT chunk appears in top K | Primary retrieval quality headline |
| Legacy `Recall@K` | Historical field name that equals query-level `Hit@K` in older artifacts | Mention only as legacy naming |
| `evidence_recall@K` | Fraction of all GT chunks retrieved | Secondary multi-evidence coverage metric |
| `MRR@K` / `nDCG@K` | Ranking quality among retrieved chunks | Secondary quality metrics |
| `source_candidate_cost` | Number of candidates considered before final fusion | Retrieval-stage diagnostic only |
| `dense_query_rate` | Fraction of queries that invoke global dense retrieval | Dense-compute proxy / route diagnostic |
| final context tokens | Token count of retrieved chunk text in final context | Main token-efficiency metric |
| prompt context token proxy | Retrieved context token count in LLM smoke prompts | Downstream sanity metric, not full LLM cost |

Main cost claims must use final context tokens, not source candidate counts.

## Claim-to-Evidence Map

| Claim | Evidence | Safe wording | Avoid |
|---|---|---|---|
| Conservative context control reduces final retrieved context tokens while preserving retrieval quality | Task29.2, Task29.3, Task33.6 | Task29-C reduces final context tokens by about 4.7-5.3% across LoTTE scales while preserving dense-level Hit@10 | Candidate-cost reductions prove lower LLM cost |
| IntentWeight is above dense on larger LoTTE scales | Task29.2, Task29.3 | Mean Hit@10 is above dense on 200k, 400k, and 638k while using fewer final context tokens | It significantly beats dense at every scale |
| LoTTE 100k is stable but not a statistical superiority result | Task29.3, Task33.6 | Three-seed 100k is near dense; five-seed 100k is slightly above dense on mean but CI overlaps zero | 100k proves statistically significant improvement over dense |
| Trust-weighted feedback improves the adaptive policy | Task25, Task33.2, Task33.3 | Under controlled simulated feedback, trust weighting improves last true reward, selected-cluster hit, dense fallback reduction, and token efficiency | Real human feedback has already been validated |
| Geometry is useful for routing | Task30, Task33.1a geometry, Task33.3 static KMeans row | Local cluster geometry is informative and supports a piecewise relevance-manifold framing | The manifold hypothesis is mathematically proven |
| Dense remains necessary | Task24, Task29, Task33.3, eManual/CUAD analyses | Dense is a recall floor and fallback, not an obsolete baseline | IntentWeight replaces dense retrieval |
| Results are not tied to one exact encoder | Task33.1a | A QA-tuned MiniLM-family encoder preserves the bounded claim on LoTTE 100k | The claim holds for all stronger encoders, rerankers, or late-interaction models |
| Final context compaction does not obviously harm generation quality in a small smoke | Task33.5 | In a 60-query LLM smoke, Task29-C did not show obvious generated-answer degradation relative to dense top-10 | End-to-end answer quality is proven superior |
| eManual and CUAD are limitation cases | Task14.5, CUAD guardrails | Dataset structure and sparse/strict labels can reduce observed benefit | The method works uniformly on every dataset |

## Cross-Checked Key Numbers

### Main LoTTE Token-Quality Frontier

| Scale | Dense Hit@10 | Task29-C Hit@10 | Hit delta | Dense tokens@10 | Task29-C tokens@10 | Token saving |
|---|---:|---:|---:|---:|---:|---:|
| 100k | 0.8674 | 0.8652 | -0.22 pp | 1472.39 | 1401.24 | 4.83% |
| 200k | 0.7970 | 0.8249 | +2.80 pp | 1444.12 | 1376.46 | 4.69% |
| 400k | 0.7718 | 0.7819 | +1.01 pp | 1482.30 | 1403.43 | 5.32% |
| 638k | 0.7282 | 0.7466 | +1.85 pp | 1525.62 | 1451.49 | 4.86% |

Source artifacts:

- `paper/experiments/task29_2_token_quality_frontier.md`
- `paper/experiments/results/task29_token_quality_frontier.csv`
- `paper/experiments/results/task29_3_seed_variance_ci.md`

### LoTTE 100k Five-Seed Extension

| Setting | Hit@10 | Avg context tokens@10 | Token ratio vs dense |
|---|---:|---:|---:|
| Dense | 0.8674 | 1472.39 | 1.0000x |
| Task29-C 5-seed mean | 0.8708 | 1399.83 | 0.9507x |

Five-seed Hit delta CI: `[-0.82, +1.50]` percentage points. This is stability
evidence, not a statistical-superiority result.

Source artifact:

- `paper/experiments/task33_6_additional_seeds_summary.md`

### Robustness and Sanity Checks

| Check | Result | Interpretation |
|---|---|---|
| Multi-QA MiniLM robustness | Task29-C Hit@10 `0.8853` vs dense `0.8809`; token saving `3.35%` | Not tied to exact `all-MiniLM-L6-v2`, within a CPU-friendly MiniLM family |
| Feedback sensitivity | `trust_default` improves selected-cluster hit from `0.5979` to `0.7223` versus equal noisy; `trust_mild` reaches Hit@10 `0.8775` and token ratio `0.9255x` | Trust-weighted simulated feedback behaves in the expected direction |
| LLM generation smoke | winner counts: tie `32`, dense `14`, Task29-C `14`; token proxy ratio `0.9321x` | No obvious generation degradation in a 60-query smoke |

## Corrections Applied in This Audit

- Updated the evidence package so Task33.1a, Task33.5, and Task33.6 are reflected.
- Updated limitations from "no LLM generation evaluation" to "only a small LLM
  generation smoke, not full human/end-to-end validation."
- Updated encoder limitation from "only one encoder" to "main evidence chain
  uses one encoder, with one MiniLM-family robustness check."
- Updated seed limitation from "only three seeds" to "three seeds across all
  scales, with five seeds for LoTTE 100k."
- Updated draft and artifact references so Task33.7 becomes the writing-time
  consistency entry point.

## Remaining Reviewer Risks

| Risk | Current mitigation | Residual limitation |
|---|---|---|
| Simulated feedback | Task33.2 noise/trust sensitivity and no-leakage protocol | No real user-feedback deployment |
| Single main encoder | Task33.1a multi-qa MiniLM robustness | No full-scale BGE/Nomic/domain-specific reranker study |
| Statistical strength | Task29.3 three-seed CIs and Task33.6 five-seed 100k extension | Limited seed count, especially at larger scales |
| Manifold framing | Task30 diagnostics and Task33.3 geometry ablation | Diagnostic support only, not proof |
| Generation quality | Task33.5 LLM smoke | Small sample, one model, LLM-as-judge |
| Generalization | LoTTE is main positive evidence; eManual/CUAD are limitations | More vertical corpora would strengthen external validity |

## Writing Guidance

Use Task33.7 as the pre-writing source of truth alongside Task31. The clearest
paper structure is:

1. Define the adaptive retrieval-control problem.
2. Present IntentWeight as a multi-route controller with dense fallback.
3. Use Task33.3 to explain component attribution.
4. Use Task29.2/29.3 and Task33.6 as the main token-quality evidence.
5. Use Task33.2 for feedback self-evolution.
6. Use Task30 for geometry diagnostics.
7. Use Task33.1a and Task33.5 as robustness/sanity checks.
8. Keep eManual, CUAD, simulated feedback, limited encoders, and small LLM
   smoke visible as limitations.
