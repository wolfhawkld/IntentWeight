# Task73 Hypothesis-Driven LoTTE Domain Expansion Plan

Date preregistered: 2026-07-15

Status: completed 2026-07-15; protocol was frozen before downloading or inspecting either selected domain

## Purpose

Task73 tests whether the quality-context frontier observed on LoTTE
technology/search and science/search changes across two deliberately contrasted
retrieval domains. It is an external-validity and boundary study, not a search
for another favorable row and not a pooled significance exercise.

The paper's bounded mechanism remains:

`local geometry -> adaptive route selection -> feedback-informed repeated-query adaptation -> independently calibrated context budget`

Task73 does not test or restore a direct causal claim from route confidence to
safe compression. Route quality and final-context budgeting remain separate
estimands.

## Domain Selection Before Outcome Inspection

The selected domains are:

1. `LoTTE recreation/search`: preregistered as the relatively more
   entity/term-matching-oriented condition.
2. `LoTTE writing/search`: preregistered as the relatively more
   paraphrastic/advice-oriented condition.

`LoTTE lifestyle/search` is deferred. Its mixed topical composition gives a
less discriminative contrast for the present hypothesis, and adding it only to
increase dataset count would violate the Task69 common-protocol rationale.

The completed download resolves `mteb/LoTTE` to source revision
`a9006514d20ec3353082b4272bf46a20dd96a195`; processed artifact hashes are
recorded separately so the source snapshot does not need to be embedded into
every corpus row.

The domain-property premise will be checked independently of IntentRoute's
budget outcome using query-to-positive lexical overlap and the matched
BM25-versus-Dense retrieval gap. A reversed or weak contrast will be reported
as such; it will not trigger replacement of either domain.

## Preregistered Questions and Hypotheses

### Q1: Does the retrieval regime differ across the two domains?

H1 predicts that recreation/search will show stronger lexical alignment than
writing/search, measured by preregistered query-positive token overlap and by a
smaller Dense advantage, or a larger BM25 advantage, at Hit@10. This hypothesis
describes the selected contrast and is evaluated before interpreting budget
results.

### Q2: Does the independently calibrated quality-context frontier vary by domain?

H2 predicts domain heterogeneity rather than universal positive saving. The
primary estimand in each domain is the five-fold out-of-fold Hit@10 difference
between calibrated IntentRoute and matched Dense, paired with final-context
token saving. EvidenceRecall@10, MRR@10, nDCG@10, dense invocation rate, and
fold eligibility are supporting outcomes.

The expected direction is that the more paraphrastic writing condition may
retain a broader useful frontier, while the more lexical recreation condition
may need more Dense fallback or yield a narrower frontier. This directional
expectation is secondary: a reversed result is scientifically valid evidence
of heterogeneity and will not cause protocol changes.

### Q3: What is attributable to feedback rather than the fixed retrieval stack?

H3 compares `trust_weighted` with `none` under identical route, seed, epoch,
candidate-pool, and budget settings. Feedback is evaluated as repeated-query
adaptation and conditional recovery. It is not interpreted as first-pass
unseen-query generalization or as the direct selector of a compression ratio.

## Frozen Common Protocol

The protocol is inherited from `task69_common_protocol.json` version 2:

- task: evidence retrieval, LoTTE search split;
- corpus construction: deterministic GT-anchored 100k target, preserving all
  positive-qrel chunks even when the realized corpus exceeds 100,000 rows;
- query set: all positive-qrel queries in the selected configuration;
- backbone: `sentence-transformers/all-MiniLM-L6-v2`;
- top-k: 10;
- baselines: BM25, Dense, and Hybrid RRF;
- route controller: K=32, seeds 13/17/19, eight no-leakage prequential epochs;
- route modes retained for artifact completeness: `full_multi_route` and
  `gated_cost_aware`;
- feedback modes: `none` and `trust_weighted`;
- reward attribution: `final_fused` for common-protocol rows;
- context budget: five-fold cross-fitted Task38 locked grid;
- selection rule: zero observed calibration-fold Hit@10 drop, then maximum
  token saving;
- non-inferiority margin: 1 percentage point;
- tokenization: cached `cl100k_base`, with no fallback tokenizer;
- paired inference: query-level paired bootstrap 95% intervals, exact McNemar,
  and win/loss/tie counts;
- reporting: each domain remains a separate comparison family; no pooled
  p-value or pooled claim is permitted.

Embedding construction may use the local AMD ROCm environment, while route,
calibration, and statistics use the standard `.venv`. Hardware choice is not
an experimental factor, and Task73 makes no runtime or end-to-end efficiency
claim. Cached exact scores must satisfy the Task72.2 provenance and structural
validation requirements.

## Primary Decision Rules

For each domain, report without post-hoc replacement:

1. Dense, BM25, Hybrid RRF, no-feedback IntentRoute, and trust-weighted
   IntentRoute retrieval metrics under the matched corpus and query set.
2. Five-fold out-of-fold calibrated Hit@10 delta versus Dense and final-context
   token saving, with the number of eligible folds.
3. Seed-level strict 1pp non-inferiority and paired query-level uncertainty.
4. Geometry diagnostics and feedback recovery as mechanism/boundary evidence,
   not as interchangeable replications of the primary budget result.

Interpretation is fixed as follows:

- Positive saving with the quality guardrail satisfied supports a useful
  domain-specific operating point.
- Zero eligible folds or zero saving is a valid Dense-fallback boundary.
- A mean point estimate inside the 1pp margin without all seed-level strict
  non-inferiority is reported as suggestive, not established non-inferiority.
- Improved top-10 routing does not by itself establish safe final-context
  compression.
- Agreement or disagreement between domains informs external validity; neither
  domain may be omitted because its outcome is unfavorable.

## Execution and Stop Rules

1. Download and preprocess both selected domains before running outcome
   comparisons; record realized corpus/query counts and GT coverage.
2. Build one canonical MiniLM scale store per domain and bind all dependent
   artifacts to its Task72.2 fingerprint.
3. Run matched Dense, BM25, Hybrid RRF, trust-weighted IntentRoute, and
   no-feedback IntentRoute artifacts.
4. Run five-fold cross-fitted budget calibration and paired statistics for
   both domains.
5. Run geometry and feedback-recovery diagnostics needed by the common
   evidence matrix.
6. Produce one Task73 audit containing checksums, coverage, protocol values,
   per-domain results, and cross-domain heterogeneity interpretation.

No seed, epoch count, cluster count, backbone, budget grid, sampling rule,
query subset, or selected domain may change after result inspection. Execution
may stop only for data corruption, missing positive-qrel coverage, hardware or
dependency failure, or a demonstrated implementation defect. A scientifically
unfavorable result is not a stop condition.

## Expected Artifacts

- processed data: `lotte_{recreation,writing}_search_100k_{corpus,queries}.json`;
- scale stores: `data/scale_store/lotte_{recreation,writing}_search/`;
- baselines: `results/task73_{domain}_100k_{dense,bm25,hybrid}/`;
- routes: `results/task73_{domain}_100k_{trust,none}/`;
- calibration: `results/task73_{domain}_100k_cross_fitted_budget.*`;
- geometry/recovery: Task73-scoped result directories;
- final record: `task73_lotte_domain_expansion_summary.md` plus a
  machine-readable audit JSON/CSV.

## Completion Outcome

The preregistered H1 domain-property ordering was not supported and was
directionally reversed. The selected domains were retained without replacement.
The full result supports a heterogeneous bounded frontier rather than universal
savings: writing/no-feedback yields the useful operating point, recreation is
a weaker boundary, and trust-weighted calibration safely falls back in both.
The completed interpretation and 104-check audit are recorded in
`task73_lotte_domain_expansion_summary.md` and
`results/task73_lotte_domain_expansion.{json,csv,md}`.
