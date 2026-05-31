# Table and Figure Placement Plan

Updated: 2026-05-31

This file is a paper-facing placement plan. It does not introduce new
experiments or new claims. Its purpose is to decide which evidence belongs in
the main paper and which evidence should be moved to an appendix or supplement.
The appendix-facing tables are instantiated in `12_appendix.md`.

The table labels in the current draft are aligned with this plan:

- Table 1: dataset roles and evaluation guardrails;
- Table 2: LoTTE token-quality frontier;
- Table 3: LoTTE 100k component ablation;
- Table 4: feedback self-evolution summary;
- Table 5: LoTTE geometry diagnostics;
- Appendix Tables A1, D1, and F1: seed stability, secondary datasets, and the
  downstream generation smoke.

## Main-Paper Tables

### Table 1: Dataset Roles and Evaluation Guardrails

Evidence basis: dataset-role guardrails from the experimental setup.

Purpose: explain why LoTTE is the main benchmark and why PubMedQA, Banking77,
eManual, and CUAD are supporting or boundary cases.

Keep in the main paper because the dataset-role distinction is essential to
the claim boundary.

Recommended columns:

- dataset;
- role;
- paper use;
- caveat.

### Table 2: LoTTE Token-Quality Frontier

Evidence basis: the LoTTE 100k-638k final context-token frontier.

Purpose: main quantitative result. It shows that the conservative policy
reduces final retrieved context tokens by about 4.7-5.3% across LoTTE
100k-638k while preserving dense-level $\mathrm{Hit@10}$.

Keep in the main paper because this is the central evidence for the
quality-token trade-off.

Recommended columns:

- scale;
- corpus size;
- dense $\mathrm{Hit@10}$;
- conservative policy $\mathrm{Hit@10}$;
- hit delta;
- dense $\mathrm{Tokens@10}$;
- conservative policy $\mathrm{Tokens@10}$;
- token saving.

### Table 3: LoTTE 100k Component Ablation

Evidence basis: the clean LoTTE 100k component ablation.

Purpose: attribute the result to dense fallback, BM25, cluster-local routing,
feedback, trust weighting, and conservative context compaction.

Keep in the main paper because it answers the likely reviewer question:
which component actually contributes?

Recommended columns:

- component;
- role;
- $\mathrm{Hit@10}$;
- $\mathrm{EvidenceRecall@10}$;
- $\mathrm{Tokens@10}$ or token ratio;
- dense rate;
- LinUCB rate;
- selected-cluster hit;
- last reward.

If space is tight, move $\mathrm{EvidenceRecall@10}$ and last reward to an
appendix and keep dense rate, LinUCB rate, $\mathrm{Hit@10}$, and token ratio
in the main table.

### Table 4: Feedback Self-Evolution Summary

Evidence basis: controlled feedback-sensitivity and trust-weighting analysis.

Purpose: show that feedback affects route-policy internals even when final
ranking quality is partly saturated by dense and BM25 rescue paths.

Keep a compact version in the main paper because feedback-driven adaptation is
part of the core method.

Recommended columns:

- feedback mode;
- selected-cluster hit;
- last true reward;
- dense rate;
- LinUCB rate;
- token ratio;
- $\mathrm{Hit@10}$.

### Table 5: Geometry Diagnostics Across LoTTE Scales

Evidence basis: LoTTE geometry diagnostics across corpus scale.

Purpose: support the piecewise relevance-manifold framing without claiming a
theorem-level proof.

Keep in the main paper if the venue allows five tables. If space is tight,
move the full numeric table to the appendix and keep only the geometry figure
in the main paper.

Recommended columns:

- scale;
- $\mathrm{PCAdim90}$;
- $\mathrm{PCAvar@64}$;
- $\mathrm{NearestClusterHit@3}$;
- $\mathrm{ContextRetention@10}$;
- conservative-policy hit delta.

## Main-Paper Figures

### Figure 1: IntentWeight System Diagram

Draft asset:

- `figures/figure1_system_diagram.svg`
- `figures/figure1_system_diagram.mmd`

Purpose: explain the method more clearly than prose.

Recommended visual flow:

1. query and optional user/session context;
2. feature construction;
3. LinUCB route policy;
4. route set: dense fallback, BM25 lexical path, cluster-local dense path, and
   hybrid/fusion path;
5. confidence-based final context budget;
6. answer generation or downstream agent response;
7. simulated or deployment feedback returning to the LinUCB state.

Caption boundary: dense is a recall floor and rescue path, not a component
that the method claims to eliminate.

### Figure 2: Token-Quality Frontier Across Corpus Scale

Draft asset:

- `figures/figure2_token_quality_frontier.svg`
- `figures/figure2_token_quality_frontier_data.csv`

Purpose: visualize the main result from Table 2.

Recommended plot:

- x-axis: LoTTE corpus scale;
- left y-axis: $\mathrm{Hit@10}$ for dense and conservative policy;
- right y-axis or separate panel: token ratio / token saving.

Caption boundary: mean above-dense $\mathrm{Hit@10}$ at 200k/400k/638k should
not be described as statistically significant unless supported by the reported
intervals.

### Figure 3: Geometry Diagnostic Trend

Draft asset:

- `figures/figure3_geometry_diagnostics.svg`
- `figures/figure3_geometry_diagnostics_data.csv`

Purpose: connect the manifold-inspired hypothesis to measured local geometry.

Recommended plot:

- $\mathrm{NearestClusterHit@3}$ across scale;
- $\mathrm{ContextRetention@10}$ across scale;
- optionally $\mathrm{PCAvar@64}$ or $\mathrm{PCAdim90}$ in a secondary panel.

Caption boundary: these are diagnostics supporting a piecewise local-structure
interpretation, not proof that the true corpus is a smooth manifold.

## Appendix Tables

### Appendix A: Full Seed Stability and Confidence Intervals

Evidence basis: LoTTE multi-seed confidence intervals and the five-seed 100k
extension.

Include the three-seed LoTTE 100k-638k diagnostics and the five-seed LoTTE 100k
extension.

### Appendix B: Full Static Baseline Metrics

Evidence basis: BM25, dense, and hybrid retrieval baseline artifacts.

Include $\mathrm{MRR@10}$, $\mathrm{nDCG@10}$, and
$\mathrm{EvidenceRecall@10}$ in addition to $\mathrm{Hit@10}$.

### Appendix C: Source-Candidate and Dense-Invocation Diagnostics

Evidence basis: source-candidate diagnostics and the final context-token
correction audit.

Use this appendix to preserve the engineering diagnostic value of historical
candidate-cost results while keeping the main cost claim on final context
tokens.

### Appendix D: Secondary Dataset and Boundary-Case Details

Evidence basis: secondary dataset synthesis, eManual duplicate-text analysis,
CUAD sparse smoke/stress artifacts, and PubMedQA/Banking77 feedback artifacts.

This appendix should make clear that PubMedQA and Banking77 support the
feedback mechanism, while eManual and CUAD bound the method's applicability.

### Appendix E: Encoder Robustness

Evidence basis: CPU-friendly encoder selection rationale and MiniLM-family
robustness check.

Include model-resource rationale and the MiniLM-family robustness result.

### Appendix F: Downstream Generation Smoke

Evidence basis: the small downstream generation smoke test.

Keep this in the appendix unless the target venue specifically values a small
generation sanity check in the main results.

### Appendix G: Historical or Superseded Experiments

Evidence basis: paper-use status index for historical and superseded artifacts.

Do not include historical/superseded task results as primary evidence. They may
be mentioned only when explaining why source-candidate cost was replaced by
final context tokens as the main efficiency metric.

## Appendix Figures

### Appendix Figure A: Feedback Sensitivity Curves

Plot selected-cluster hit, last true reward, dense rate, and token ratio across
feedback modes. This supports Table 4 without overloading the main paper.

### Appendix Figure B: Context-Token Distribution

Plot per-query context token distributions for dense and conservative policy
at one or more LoTTE scales. This can show whether savings come from broad
small reductions or a smaller number of high-confidence compaction cases.

### Appendix Figure C: eManual Duplicate-Text Diagnostic

Visualize strict chunk-id evaluation versus text-equivalent and deduplicated
evaluation. This makes the boundary case easier to understand.

## Main-Text Budget Recommendation

For a conference-length paper, target:

- 3 main figures;
- 4 main tables, or 5 only if space permits;
- detailed metric tables in the appendix.

If one main table must be removed, move the full geometry table to the appendix
and keep the geometry trend as Figure 3. The main paper should not drop Table 2
or the component ablation table.

## Claim Guardrail

The visual and table package should support this bounded story:

IntentWeight improves the quality-token trade-off in a large-scale vertical
retrieval setting by combining dense fallback, lexical coverage, local
geometry, and feedback-updated route control. The evidence supports practical
context compaction and policy adaptation, not universal dense replacement,
theorem-level manifold proof, or real-human-feedback deployment validation.
