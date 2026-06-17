# Publication Readiness and Figure/Table Improvement Plan

Date: 2026-06-16

This note records the current assessment before further manuscript polishing. It is intended as a writing and figure/table alignment checkpoint, not as a new experimental result.

## Current Judgment

The core evidence chain is substantially closed, but the manuscript presentation is not yet as strong as it should be for formal publication.

The current paper has a defensible logic loop:

1. Vertical or domain-structured evidence corpora often show usable local relevance geometry.
2. Dense retrieval is a strong global recall floor, but it can be inefficient when every query always receives a fixed top-10 context.
3. IntentWeight combines dense recall, BM25 lexical anchoring, cluster-local LinUCB routing, trust-weighted feedback, and calibrated context budgeting.
4. The main LoTTE technology/search results show that calibrated policies can reduce final LLM evidence-context input tokens while preserving near-dense or above-dense query-level Hit@10.
5. LoTTE science/search provides cross-domain evidence, with a more nuanced compression behavior that supports domain-specific calibration rather than universal compression.
6. Feedback recovery experiments show that some budget-induced failures can be repaired by post-feedback adaptation, supporting the self-improving retrieval-control claim.
7. Geometry diagnostics support the piecewise relevance-manifold framing as a useful empirical motivation and diagnostic, not as a theorem.

The current risk is not that the project lacks results. The risk is that the manuscript still relies too much on dense tables and does not yet use figures to make the hypothesis-method-result loop visually obvious.

## Figure/Table Readiness

Current manuscript structure:

- Main figures: 3
  - Figure 1: system/controller diagram.
  - Figure 2: token-quality frontier.
  - Figure 3: geometry diagnostics.
- Main tables: 6.
- Appendix tables: many detailed audit, robustness, boundary, and recovery tables.

This is technically acceptable, but visually weak. The paper currently feels table-heavy. Important claims such as geometry usefulness, feedback-driven adaptation, and cross-domain/encoder robustness are still mostly table-driven.

For publication readiness, figures should do more of the argumentative work:

- show the quality-cost frontier directly;
- show why IntentWeight is not just dense truncation;
- show how local geometry relates to route quality;
- show feedback adaptation over policy metrics;
- show generalization across domains and embedding encoders once external runs are available.

## Recommended Main-Figure Structure

### Figure 1: Evidence-Selection Controller

Keep this as the method figure, but ensure the diagram matches the real pipeline:

- Dense and BM25 are global recall routes.
- LinUCB is a cluster-local route controller, not a replacement for dense/BM25.
- Route confidence flows into final context-budget control.
- Final evidence context is what drives downstream LLM input-token cost.

### Figure 2: Token-Quality Frontier

Keep and strengthen this as the headline result figure.

It should show:

- dense top-10 as the quality/cost reference;
- dense-only adaptive truncation as a cheaper but quality-degrading baseline;
- IntentWeight calibrated policies as the quality-preserving or near-quality-preserving compression path;
- LoTTE technology/search scale-up and science/search validation points on the same chunk-count x-axis.

This figure supports the main cost claim: the relevant saving is final LLM evidence-context input tokens, not merely retrieval-side candidate count.

### Figure 3: Geometry Diagnostics

Keep this figure, but treat it as diagnostic support rather than proof.

It should show:

- local cluster routing signal remains usable across scale;
- context retention and PCA concentration vary by scale/domain;
- geometry helps explain where route control is plausible, but it does not justify removing dense fallback.

### New Figure 4: Geometry-to-Gain Relationship

This is the most important missing figure.

Recommended design:

- x-axis: `NearestClusterHit@3` or `ContextRetention@10`;
- y-axis: IntentWeight hit delta or final context-token saving;
- points: domain/scale combinations;
- optional point labels: 100k, 200k, 400k, 638k, science 20k, science 100k.

Purpose:

This directly answers the reviewer question: if the method is motivated by local relevance geometry, does stronger geometry correspond to better routing or compression behavior?

The expected conclusion should be cautious: geometry diagnostics are explanatory and useful for calibration, but not a sufficient predictor of universal gains.

### New Figure 5: Feedback Adaptation Curve

Feedback self-improvement should not be expressed only as a table.

Recommended design:

- x-axis: feedback setting or repeated interaction epoch;
- y-axis options:
  - selected-cluster hit;
  - last true reward;
  - dense rate;
  - LinUCB route rate;
  - token ratio.

Purpose:

This figure supports the claim that trust-weighted simulated feedback improves the route policy itself, especially when final Hit@10 is partly saturated by dense/BM25 rescue routes.

### Future Figure 6: External Robustness Matrix

This should be added after off-device experiments are completed.

Recommended design:

- rows: LoTTE domains or embedding encoders;
- columns: dense Hit@10, IntentWeight Hit@10, hit delta, context-token saving, key geometry diagnostic;
- format: compact heatmap or grouped bar chart.

Purpose:

This figure will address external validity:

- not only technology/search;
- not only one embedding model;
- not only one representation geometry.

## Table Strategy

The current number of tables is acceptable only if the main text remains selective.

Recommended main-text tables:

1. Main calibrated token-quality frontier.
2. Cross-domain validation summary.
3. Component ablation summary.
4. Feedback/recovery summary.
5. Geometry diagnostic summary if Figure 4 is not sufficient.

Appendix tables should remain for:

- full scale tables;
- multi-seed stability;
- detailed correction audits;
- boundary datasets;
- LLM answer-quality sanity checks;
- encoder robustness details;
- recovery variants.

Avoid using large appendix tables as the only evidence for a major claim. If a claim is central, it should have either a main-text figure or a compact main-text table.

## Additional Experiments Not Planned on This Device

The following experiments are important but should be run on the other GPU-capable machine, not on the current device.

### More LoTTE Domains

Goal:

Strengthen generalization beyond technology/search and science/search.

Suggested minimal loop per domain:

1. Dense baseline.
2. IntentWeight fixed top-10.
3. Calibrated context-budget policy.
4. Geometry diagnostics.

Recommended start:

- run 100k per new domain first;
- only expand promising or informative domains to 200k/400k;
- keep weak domains as boundary cases if they explain limitations.

### BGE or Stronger Encoder Robustness

Goal:

Test whether the quality-cost effect persists under a stronger independent embedding model.

Recommended order:

1. `BAAI/bge-base-en-v1.5`.
2. Optionally `BAAI/bge-large-en-v1.5` if GPU throughput is acceptable.

Interpretation:

The goal is not to prove IntentWeight always beats BGE dense retrieval. The stronger claim is that, under a stronger encoder, IntentWeight can still preserve a favorable quality-cost frontier by reducing final evidence-context tokens under calibrated confidence control.

## Next Local Task

The next local task should focus on manuscript figure/table improvement, not new large-scale experiments.

Suggested scope:

1. Generate Figure 4: geometry-to-gain relationship from existing LoTTE technology/search and science/search data.
2. Generate Figure 5: feedback adaptation curve from existing feedback sensitivity and route-policy results.
3. Re-balance main-text tables so that the central argument is figure-led rather than table-heavy.
4. Re-run manuscript table/figure audit and LaTeX PDF audit.

This keeps the current device focused on presentation quality and evidence integration while leaving GPU-heavy encoder robustness and additional LoTTE-domain experiments to the other machine.
