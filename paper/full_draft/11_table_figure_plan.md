# Table and Figure Placement Plan

Updated: 2026-06-27 (Task65)

This plan aligns the displays with the revised route-confidence-to-budget
claim. It introduces no new experiment or claim. The journal-facing main text
uses five tables and three figures; detailed seed, recovery, compressor, and
boundary-case results remain in the appendix.

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

### Table 4: Arm-Count Sensitivity

The $K=8$-$128$ grid. It shows that full multi-route quality is stable while
gated dense use and quality are more sensitive to feedback sparsity and arm
granularity.

### Table 5: Downstream Answer-Level Evaluation

Paired BGE, E5, and shared-MMR comparisons over 300 frozen queries. The display
reports correctness uncertainty and context-token saving uncertainty. Full
faithfulness and citation-support metrics remain in Appendix F.

## Main-Paper Figures

### Figure 1: IntentRoute System Diagram

Shows global dense/BM25 recall, cluster-local LinUCB routing, rank fusion,
confidence-based context budgeting, and trust-weighted feedback.

### Figure 2: Calibrated Token-Quality Frontier

Shows hit delta and final context-token saving across LoTTE scales. The caption
states that dense truncation compresses more aggressively but loses hit rate.

### Figure 3: Geometry-To-Control Diagnostic

Relates context retention to observed hit delta and token saving. It supports
geometry as a diagnostic route-control signal, not a deterministic gain law or
theorem-level manifold proof.

## Appendix Placement

- Appendix A/G: seed stability and complete frozen-policy validation;
- Appendix D/E: boundary datasets and encoder details;
- Appendix F: complete downstream answer, faithfulness, and citation results;
- Appendix H/I: cross-domain and feedback-recovery details;
- Appendix J: Sentence-MMR, SelectiveContext-lite, and cross-encoder controls;
- Appendix K: full geometry/random, feedback, and arm-count control tables.

The older clean component table, geometry scale table, cross-domain table, and
feedback-recovery table are represented in the main text as bounded prose and
retained in their experiment summaries or appendix tables. They no longer
compete with the evidence that directly supports the revised central claim.
