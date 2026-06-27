# Task64 Manuscript Claim Reframe Summary

Task64 is complete.

The paper-facing method name is `IntentRoute`, replacing the earlier
`IntentWeight` name. Historical result paths and machine-readable labels retain
`IntentWeight` as a legacy identifier to preserve reproducibility.

## Central Claim

The manuscript now centers its novelty on route-confidence-to-budget control:
IntentRoute estimates confidence over dense, lexical, and cluster-local routes
and maps that confidence to a calibrated final evidence-context budget.

The component roles are stated consistently:

- local geometry and the piecewise relevance-manifold hypothesis motivate and
  diagnose reproducible route structure;
- trust-weighted LinUCB and feedback adapt route confidence and support
  controlled recovery;
- dense retrieval remains the primary baseline, recall floor, and rescue path;
- BM25 provides lexical rescue;
- SentMMR, SelectiveContext-lite, and cross-encoder reranking are complementary
  downstream layers.

## Evidence Integrated

- Task53 matched MiniLM, BGE-base, and E5-base backbones;
- Task54 BGE quality-first frontier tunability and its E5 boundary;
- Task58 geometry-versus-random route attribution;
- Task59 learned/static/no-feedback controls;
- Task60 arm-count sensitivity over $K=8$-$128$;
- Task61 geometry-to-control interpretation;
- Task62 SelectiveContext-lite prompt-pruning composition;
- Task63 frozen 300-query, 2,100-answer/judgment downstream evaluation.

The downstream wording is explicitly bounded: matched variants reduce context
without a statistically detectable correctness change. The manuscript does not
claim significant answer-quality improvement, universal dense replacement, or
theorem-level proof of a relevance manifold.

## Updated Artifacts

- paper-facing Markdown under `paper/full_draft/`;
- generated LaTeX under `paper/latex/`;
- generated review manuscript under `paper/review_packet/`;
- compiled PDF at `paper/latex/main.pdf`.

## Validation

- full-draft consistency validation: passed;
- canonical `intent_route` API and legacy `intent_weight` compatibility tests:
  passed;
- LaTeX migration and static validation: passed;
- review packet validation: passed;
- PDF compilation and visual/log audit: passed;
- final PDF: 30 pages, zero critical LaTeX log warnings.

Task65 remains responsible for final table selection, figure refresh, and
journal-facing visual compression.
