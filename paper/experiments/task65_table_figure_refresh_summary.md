# Task65 Table And Figure Refresh Summary

Task65 is complete.

## Scope

This task changed paper-facing evidence selection and presentation only. It did
not rerun experiments, alter metric definitions, or introduce new claims.

## Main-Paper Display Set

The Results section now uses five main tables:

1. calibrated token-quality frontier;
2. matched MiniLM/BGE/E5 backbone robustness;
3. geometry/random and learned/static/no-feedback route controls;
4. arm-count sensitivity over $K=8$-$128$;
5. paired downstream answer-quality and context-token comparisons.

The main paper now uses three figures:

1. IntentRoute system diagram;
2. calibrated token-quality frontier;
3. geometry-to-control diagnostic.

Cross-domain validation, feedback recovery, full downstream metrics, strong
compressor/reranker baselines, and detailed control tables remain available in
the appendix. No supporting result was deleted from the experiment artifacts.

## Claim Alignment

- final context-token control remains the primary outcome;
- matched-backbone and downstream tables support bounded robustness;
- route reward and selected-cluster hit expose geometry and feedback effects
  separately from dense/BM25-rescued final fused quality;
- arm-count sensitivity presents $K=32$ as a reproducible engineering choice,
  not a theoretical optimum;
- geometry remains an explanatory control signal rather than a deterministic
  predictor of final gain.

## Generated Artifacts

- refreshed `paper/full_draft/06_results.md`;
- refreshed `paper/full_draft/11_table_figure_plan.md`;
- new Figure 3 SVG/CSV and PDF assets;
- regenerated modular LaTeX sections and references;
- regenerated review packet and manifest;
- compiled `paper/latex/main.pdf`.

## Validation

- full-draft consistency validation: passed;
- LaTeX migration and static validation: passed;
- review-packet validation: passed with three indexed main figures;
- PDF compile and rendering audit: passed;
- critical LaTeX log warnings: zero;
- visual contact-sheet inspection: no clipping, overlap, or abnormal main-text
  float placement;
- ACL-style working PDF reduced from 30 to 28 pages.

Task66 remains responsible for conversion to the Elsevier/IP&M submission
template and further venue-specific shortening.
