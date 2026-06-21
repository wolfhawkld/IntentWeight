# 8. Conclusion

This paper presents IntentWeight, a feedback-adaptive evidence-selection
controller motivated by local relevance structure in vertical-domain data. In
the evaluated retrieval-backed QA implementation, IntentWeight builds a
multi-route retrieval surface over dense, BM25, and cluster-local retrieval,
uses trust-weighted LinUCB to learn when compact local evidence should be
trusted, and applies confidence-based final context compaction while preserving
dense fallback.

The main evidence comes from LoTTE technology/search at 100k to 638k corpus
chunks. Under calibration/test budget selection, calibration-eligible operating
points at 100k, 200k, and 638k reduce final LLM evidence-context input tokens
by 6-18%; the 400k point remains a positive diagnostic result pending
follow-up calibration. Across these scales, IntentWeight avoids the larger
$\mathrm{Hit@10}$ losses of dense-only adaptive truncation, while strict
seed-level non-inferiority remains scale-dependent. A conservative
confidence-only policy remains a stable 4.7-5.3% saving baseline. Additional
diagnostics show that local geometry provides useful routing signal,
trust-weighted feedback improves route-policy metrics, and a small downstream
answer-quality check does not show obvious degradation from context compaction.
LoTTE science/search provides cross-domain ranking support with a clear
compression-calibration boundary. Hard-case recovery experiments further show
that simulated feedback can repair part of the tail failures caused by
aggressive context compression.

Strong post-retrieval baselines refine rather than weaken the conclusion.
Sentence-level MMR is an effective shared final-context compressor, and
cross-encoder reranking can improve top-ranked evidence support. However,
reranking alone can increase final context tokens, and same-budget reranking
does not uniformly dominate the calibrated IntentWeight policies. These results
support a layered interpretation: candidate generation, reranking, compression,
and route-budget control are separate system functions that can be composed.

The result is intentionally bounded. IntentWeight is not a universal dense
replacement, a universal compressor replacement, or a universal reranker
replacement, and it does not prove that geometry alone solves retrieval. Dense
retrieval remains an important recall floor. The contribution is a
manifold-inspired controller that learns when multiple retrieval routes, route
confidence, and feedback can be used to trade compact final context against
retrieval risk, while remaining compatible with late reranking and sentence
compression.
