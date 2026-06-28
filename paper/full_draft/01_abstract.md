# Abstract

Retrieval-augmented systems must select enough evidence to support an answer
while limiting noise and language-model context cost. We formulate this as a
two-stage route-control and budget-calibration problem. IntentRoute combines
dense retrieval, BM25, and geometry-defined cluster-local routes, then uses
trust-weighted LinUCB feedback to update route confidence. Confidence gates
route usage and fallback, whereas an independently calibrated policy sets the
final context budget. Dense retrieval remains a recall floor. A bounded
piecewise relevance-manifold hypothesis motivates local route construction;
geometry is evaluated as a diagnostic and control signal rather than a
standalone retrieval theory.

On LoTTE technology/search from 100k to 638k chunks, eligible frozen
calibration/test policies reduce evidence-context tokens by 6-18% while
avoiding the larger $\mathrm{Hit@10}$ losses of dense-only adaptive truncation;
a 400k point remains diagnostic because it fails the calibration gate.
Matched-backbone BGE-base and E5-base tests retain near-dense
$\mathrm{Hit@10}$ with about 12% token reduction, while a BGE quality-first
point reaches +0.88 percentage points with 7.23% saving. Route controls show
that geometry and feedback affect route-level quality, but a fixed-pool
factorial audit does not show that either predicts safe per-query compression.
In a frozen 300-query downstream evaluation, matched variants reduce context
by 6.00-12.04% without a statistically detectable correctness change. Prompt
compression and reranking remain complementary downstream layers. The
supported contribution is a geometry-guided, feedback-adaptive route controller
combined with separate budget calibration, not universal superiority over
dense retrieval or a proof that geometry determines relevance.
