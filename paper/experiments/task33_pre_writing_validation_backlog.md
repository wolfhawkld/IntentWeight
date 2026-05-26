# Task33 Pre-Writing Validation Backlog

Updated: 2026-05-25

Task33 records the remaining validation and writing-prep work before the formal
paper draft is expanded from the Task32 skeleton. These items are not evidence
yet. They are the planned risk-reduction tasks that should be completed before
the final paper-writing pass.

## Why This Backlog Exists

Task31 and Task32 show that the current evidence chain is coherent enough to
begin paper writing. The main claim is bounded and defensible:

> IntentWeight is a feedback-driven adaptive retrieval controller for
> vertical-domain RAG. It can use multi-route retrieval, trust-weighted LinUCB,
> geometry-aware routing, and confidence-based final context compaction to
> preserve near- or above-dense retrieval quality while reducing final retrieved
> context tokens on LoTTE 100k-638k.

However, several reviewer risks remain. The backlog below targets the risks most
likely to matter during review: single embedding model, simulated feedback
sensitivity, contribution attribution, protocol clarity, and downstream LLM
sanity checking.

## Execution Order

Recommended order:

1. Task33.1 Multi-embedding robustness.
2. Task33.2 Feedback simulation sensitivity.
3. Task33.3 Clean ablation table.
4. Task33.4 Protocol defense write-up.
5. Task33.5 Small end-to-end LLM generation smoke.
6. Task33.6 Optional additional seeds.

If time is limited, the minimum pre-writing completion set is Task33.1,
Task33.2, Task33.3, and Task33.4. Task33.5 is a strong paper-quality add-on.
Task33.6 is useful but optional.

## Task33.1 Multi-Embedding Robustness

Detailed selection rationale is recorded in
`paper/experiments/task33_1_embedding_model_selection.md`.

### Risk Addressed

The current main dense baseline uses only
`sentence-transformers/all-MiniLM-L6-v2`. Reviewers may argue that the result is
specific to one embedding model and that a stronger dense encoder could reduce
or eliminate IntentWeight's measured gain. This is currently the most important
remaining experimental robustness risk before final paper writing.

### Planned Test

Run a robustness check on LoTTE with one additional embedding family:

- dense-only baseline with at least one additional embedding family;
- Task29-C final context policy under the same embedding;
- geometry diagnostics under the same embedding;
- final context-token comparison.

Preferred additional models, subject to local availability:

1. `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` for CPU-friendly
   MiniLM-family robustness;
2. `nomic-ai/nomic-embed-text-v1.5` for open-source strong-model robustness;
3. `BAAI/bge-base-en-v1.5` only as a GPU or overnight optional run.

This ordering is intentional. The paper does not benchmark embedding models.
Task33.1 only needs to show that IntentWeight is not tied to one exact encoder.
Therefore, a QA-tuned MiniLM-family model is the most efficient first
robustness check, while Nomic is a useful second-stage open-source strong-model
check.

### Execution Adjustment After Initial Attempt

Do not start with the full LoTTE 100k BGE run on CPU. A first attempt to run
`BAAI/bge-base-en-v1.5` on LoTTE 100k was stopped manually after about 1 hour
and 14 minutes. The process was still active and consuming roughly 700% CPU and
about 2 GB memory, so this was a compute-cost issue rather than an experiment
logic failure. No dense results or BGE embedding cache files were produced.

BGE base is expected to be much slower than `all-MiniLM-L6-v2` because it is a
BERT-base-level model with 12 layers and 768-dimensional embeddings, while
MiniLM is a much smaller 6-layer, 384-dimensional model. Local micro-benchmark
showed BGE base at about 6-7x slower than MiniLM on the current CPU. Therefore,
Task33.1 should proceed in staged form:

1. **Task33.1a**: LoTTE 100k with `multi-qa-MiniLM-L6-cos-v1`. Complete; see
   `paper/experiments/task33_1a_multiqa_minilm_robustness_summary.md`.
2. **Task33.1b**: LoTTE 20k or 50k with `nomic-embed-text-v1.5`, after adding
   prefix / `trust_remote_code` / optional Matryoshka support.
3. **Task33.1c**: Optional LoTTE 100k BGE on GPU or overnight CPU, only if it
   adds meaningful paper value.

For Task33.1a, run the same evaluation types as the main MiniLM chain:

- dense-only;
- Task29-C single-seed first, then three seeds if the run is tractable;
- geometry diagnostics;
- final context-token comparison.

Task33.1a result:

- multi-qa dense Hit@10: `0.8809`;
- Task29-C mean Hit@10: `0.8853`;
- Hit delta vs multi-qa dense: `+0.45` percentage points;
- dense avg context tokens@10: `1514.51`;
- Task29-C mean avg context tokens@10: `1463.71`;
- final context token saving: `3.35%`;
- nearest_cluster_hit@3: `0.8826`;
- context_recall_retention@10: `0.9352`.

This supports the robustness claim that IntentWeight is not tied to the exact
`all-MiniLM-L6-v2` encoder. It should not be used as an embedding benchmark.

### Acceptance Criteria

The result does not need to beat dense under every model. It should answer:

- Does IntentWeight still reduce final retrieved context tokens?
- Does it remain near-dense in Hit@10?
- Does geometry still provide routing signal?
- If dense becomes stronger, does IntentWeight still function as a
  quality-cost controller?

### Paper Use

Use as robustness / sensitivity analysis. Do not replace the main LoTTE
scale-up table unless the extra embedding run is completed across all scales.
If BGE dense becomes stronger and IntentWeight no longer exceeds it, the result
can still support the bounded claim if IntentWeight remains near-dense while
reducing final context tokens.

## Task33.2 Feedback Simulation Sensitivity

Status: complete. Detailed results are recorded in
`paper/experiments/task33_2_feedback_sensitivity_summary.md`.

### Risk Addressed

Feedback is simulated. This is acceptable for controlled bandit validation, but
reviewers may ask whether the result depends on one tuned noise/trust setting.

### Planned Test

Run sensitivity across feedback conditions:

- no noise;
- mild noise;
- strong noise;
- equal noisy feedback;
- trust-weighted feedback;
- optional oracle feedback upper bound;
- optional lower/higher feedback budget or epoch count.

Primary metrics:

- last true reward;
- selected-cluster hit rate;
- final Hit@10;
- final context tokens where applicable.

### Acceptance Criteria

Trust-weighted feedback should be more stable than equal/noisy feedback in
reasonable noise ranges. If strong noise breaks the policy, report that as the
expected limitation and motivate trust scoring.

### Result

Task33.2 was run on LoTTE technology/search 100k with the main paper evidence
model, `sentence-transformers/all-MiniLM-L6-v2`, using three seeds and eight
prequential epochs. The result supports the expected sensitivity pattern:

- no-feedback keeps high Hit@10 only by relying on dense/full fallback and does
  not demonstrate self-evolution;
- oracle feedback gives the clean upper bound, with selected-cluster hit
  `0.8386`, dense rate `0.4345`, and source candidate cost `160.27`;
- trust-weighted default feedback improves policy internals over equal noisy
  feedback: last true reward rises from `0.7517` to `0.8328`, selected-cluster
  hit from `0.5979` to `0.7223`, and dense rate falls from `0.7480` to
  `0.6708`;
- mild trust-weighted feedback is the strongest controlled-noise result:
  Hit@10 `0.8775`, last true reward `0.8820`, selected-cluster hit `0.7908`,
  final context token ratio `0.9255x` versus dense;
- strong noise degrades the policy, which should be reported as a limitation
  and motivation for user trust scoring plus conservative fallback.

### Paper Use

Use to support:

> Simulated feedback validates the policy-learning mechanism under controlled
> noise and trust settings. It does not claim real human-feedback deployment has
> already been validated.

## Task33.3 Clean Ablation Table

### Risk Addressed

The project has many experiments. Reviewers may struggle to identify which
component contributes what.

### Planned Table

Create one clean paper-facing ablation table, preferably on LoTTE 100k and, if
practical, one larger scale:

- dense-only;
- BM25-only;
- dense + BM25 hybrid;
- cluster-only or static nearest cluster;
- full multi-route without feedback;
- full multi-route with equal feedback;
- full multi-route with trust feedback;
- Task29-C final context policy.

Columns:

- Hit@10;
- MRR@10;
- nDCG@10;
- final context tokens;
- dense invocation rate if applicable;
- selected-cluster hit or route reward for LinUCB variants.

### Acceptance Criteria

The table should make component attribution clear:

- dense is the recall floor;
- BM25 and cluster routes contribute coverage and routing alternatives;
- feedback improves route policy metrics;
- final context policy is the actual token-saving mechanism.

## Task33.4 Protocol Defense Write-Up

### Risk Addressed

The prequential protocol can be misunderstood as leakage if it is not described
precisely.

### Required Text

Add a dedicated protocol subsection to the paper draft:

- each query is evaluated before its feedback is used;
- no future query feedback is used to rank the current query;
- the setup is simulated test-time adaptation, not offline IID generalization;
- feedback is GT-derived and controlled;
- results should be interpreted as policy adaptation under deployment-like
  interaction.

### Acceptance Criteria

The paper should make it difficult for a reviewer to claim hidden future-label
leakage. The limitation should remain explicit: real human feedback is future
work.

## Task33.5 Small End-to-End LLM Generation Smoke

### Risk Addressed

Current experiments stop at retrieval and retrieved context tokens. Reviewers
may ask whether smaller context hurts actual answer generation.

### Planned Test

Run a small downstream sanity check on about 50-100 LoTTE queries:

- dense top-10 context;
- Task29-C compressed context.

Possible evaluation signals:

- answer correctness;
- groundedness / citation support;
- prompt token count;
- obvious answer degradation cases.

### Acceptance Criteria

This is not intended to become the main experiment. It should be a sanity check:

- if answer quality is comparable, it strengthens the context-compaction claim;
- if answer quality drops, the paper can keep the claim at retrieval/context
  level and report generation as future work.

### Paper Use

Optional downstream validation section or appendix. Do not overstate as full
human-quality evaluation.

## Task33.6 Optional Additional Seeds

### Risk Addressed

Task29.3 currently uses three seeds. That is useful but limited.

### Planned Test

If compute allows, add two more seeds for the most important configuration:

- LoTTE 100k Task29-C;
- optionally LoTTE 638k Task29-C if compute is acceptable.

### Acceptance Criteria

Use this only to strengthen stability diagnostics. It is not required for the
main claim if Task33.1 and Task33.2 are completed.

## Summary of Pre-Writing Completion Criteria

Before final paper writing, aim to have:

- at least one additional embedding-model robustness check. Task33.1a now
  satisfies the minimum CPU-friendly robustness requirement; Nomic/BGE remain
  optional if compute allows;
- feedback sensitivity results over multiple noise/trust settings. Task33.2
  satisfies this requirement on LoTTE 100k with the main paper evidence model;
- a clean ablation table with contribution attribution;
- a protocol defense subsection in the draft;
- optionally, a small LLM generation smoke;
- optionally, additional seeds for the main context policy.

The final paper should keep the current bounded claim: IntentWeight is a
feedback-driven adaptive retrieval controller and context-budget controller, not
a universal dense-retrieval replacement.
