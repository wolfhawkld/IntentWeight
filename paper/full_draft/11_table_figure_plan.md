# Table and Figure Placement Plan

Updated: 2026-07-17 (Task77)

This plan aligns the displays with the revised route-control and calibrated-budget
claim. It introduces no new experiment or claim. The journal-facing main text
uses five tables and three figures; detailed seed, recovery, compressor, and
boundary-case results remain in the separately submitted supplement.

See `figures/figure_enrichment_and_3d_plan.md` for the Task67 proposal to enrich
Figures 2/3 and add optional supplementary geometry, calibration, risk, and
multi-judge visualizations. That proposal is not yet an approved display-set
change.

## Main-Paper Tables

### Table 1: Calibrated Token-Quality Frontier

Central evidence for final evidence-context token reduction under frozen
calibration/test policy selection. It retains dense adaptive truncation as the
strong simple cost baseline and marks the 400k point as diagnostic.

### Table 2: Matched-Backbone Robustness

Matched MiniLM, BGE-base, and E5-base comparisons. This is the primary encoder
robustness display and includes the BGE quality-first operating point without
generalizing that positive-hit point to E5.

### Table 3: Route-Control Attribution

Compact geometry/random and learned/static/no-feedback controls. The table
separates route reward and selected-cluster hit from final fused hit and token
cost, making dense/BM25 rescue visible.

### Table 4: Cross-Dataset and Cross-Domain Evidence Matrix

All completed LoTTE scales/domains, biomedical transfers, corrected eManual,
and Banking77/CUAD mechanism-boundary rows in one non-pooled display. Protocol
and GT differences remain explicit; missing common budget endpoints are marked
rather than imputed.

### Table 5: Downstream Answer-Level Evaluation

Paired BGE, E5, and shared-MMR comparisons over 300 frozen queries. The display
reports per-judge correctness deltas, shared-key majority uncertainty, and
context-token saving uncertainty. Full judge calibration, agreement,
faithfulness, citation-support, and missingness details remain in Supplementary Section S6.

## Main-Paper Figures

### Figure 1: IntentRoute System Diagram

Shows global dense/BM25 recall, cluster-local LinUCB routing, rank fusion,
separately calibrated context budgeting, and trust-weighted feedback.

### Figure 2: Calibrated Token-Quality Frontier

Uses a paired Pareto-style arrow map with final context-token saving on the
x-axis and Hit@10 delta on the y-axis. Each arrow connects matched dense
adaptive truncation to IntentRoute for one domain/scale. Marker shape encodes
domain, and the hollow 400k technology pair remains explicitly diagnostic.

### Figure 3: From Local Geometry to Route-Control Behavior

Three panels show the cross-scale geometry profile, static geometry versus
uniform-random route attribution, and arm granularity versus Dense fallback and
gated quality. It supports geometry as a route-control surface while making
rescue and calibration boundaries visible.

## Supplementary Placement

- Supplementary Sections S1/S7: seed stability, independent Dense calibration, complete
  frozen-policy validation, overlapping-split sensitivity, and normalized
  cross-fitted calibration;
- Supplementary Sections S4/S5: boundary datasets and encoder details;
- Supplementary Section S6: complete downstream answer, faithfulness, and citation results;
- Supplementary Sections S8/S9: cross-domain and feedback-recovery details;
- Supplementary Section S10: Sentence-MMR and cross-encoder controls;
- Supplementary Section S11: arm-count and frozen-trajectory route controls;
- Supplementary Section S13: prospectively specified recreation/search and
  writing/search domain properties, route diagnostics, cross-fitted budgets,
  and strict seed-level non-inferiority.

The arm-count table moves from the main text to Supplementary Table S20 after
its trend is incorporated into Figure 3 Panel C. Exact duplicates, internal
reporting guardrails, and historical correction displays are removed from the
submission package while their experiment artifacts remain tracked.
