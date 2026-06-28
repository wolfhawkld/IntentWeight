# 8. Conclusion

This paper presents IntentRoute, a feedback-adaptive
confidence-gated route and calibrated-budget controller motivated by local relevance structure
in vertical-domain data. In the evaluated retrieval-backed QA implementation,
geometry defines reproducible cluster-local routes, trust-weighted LinUCB
updates route confidence, dense and BM25 provide rescue paths, and a calibrated
policy separately controls the final evidence-context budget.

The main evidence comes from LoTTE technology/search at 100k to 638k corpus
chunks. Under calibration/test budget selection, calibration-eligible operating
points at 100k, 200k, and 638k reduce final LLM evidence-context input tokens
by 6-18%; the 400k point remains a positive diagnostic result pending
follow-up calibration. Across these scales, IntentRoute avoids the larger
$\mathrm{Hit@10}$ losses of dense-only adaptive truncation, while strict
seed-level non-inferiority remains scale-dependent. A conservative
confidence-only policy remains a stable 4.7-5.3% saving baseline. Split
sensitivity checks strengthen the 200k and 638k operating points while showing
that 100k and especially 400k policy selection is more partition-dependent.
Additional diagnostics and controls show that local geometry provides useful route signal
over random routing and trust-weighted feedback improves route confidence over
no-feedback controls, without implying that either alone explains fused
quality. Matched BGE/E5 comparisons retain near-dense retrieval quality with
about 12% context saving, while a BGE quality-first point demonstrates frontier
tunability. A 300-query downstream evaluation finds 6.00-12.04% matched context
savings without a statistically detectable correctness change.
LoTTE science/search provides cross-domain ranking support with a clear
compression-calibration boundary. Hard-case recovery experiments further show
that simulated feedback can repair part of the tail failures caused by
aggressive context compression.

Strong post-retrieval baselines refine rather than weaken the conclusion.
Sentence-level MMR and SelectiveContext-lite are effective shared downstream
compressors, and cross-encoder reranking can improve top-ranked evidence
support. However,
reranking alone can increase final context tokens, and same-budget reranking
does not uniformly dominate the calibrated IntentRoute policies. These results
support a layered interpretation: candidate generation, reranking, compression,
route control, and budget calibration are separate system functions that can be
composed.

The result is intentionally bounded. IntentRoute is not a universal dense
replacement, a universal compressor replacement, or a universal reranker
replacement, and it does not prove that geometry alone solves retrieval. Dense
retrieval remains an important recall floor. The contribution is a calibrated
controller that combines geometry- and feedback-informed route control with a
separately calibrated final context budget, trading compact context against retrieval risk while
remaining compatible with late reranking and prompt compression. The manifold
hypothesis remains the motivation for local route structure, not a
theorem-level claim.
