# Abstract

Retrieval-augmented systems must select enough evidence to support an answer
while limiting noise and language-model context cost. We study this as a
route-confidence-to-budget problem: confidence in a multi-route evidence pool
should determine how much context is sent to the generator. IntentRoute
combines dense retrieval, BM25, and geometry-defined cluster-local routes,
uses trust-weighted LinUCB feedback to update route confidence, gates route
usage with that confidence, and applies a separately calibrated final context
budget. Dense retrieval remains a
recall floor. A piecewise relevance-manifold hypothesis motivates the local
route construction, but geometry is tested as a diagnostic and control signal
rather than claimed as a standalone retrieval theory.

On LoTTE technology/search from 100k to 638k chunks, frozen
calibration/test policies at eligible operating points reduce retrieved
evidence-context tokens by 6-18% while avoiding the larger $\mathrm{Hit@10}$
losses of dense-only adaptive truncation; a 400k point remains diagnostic
because it fails the calibration gate. Matched-backbone tests with BGE-base and
E5-base find near-dense $\mathrm{Hit@10}$ with about 12% token reduction, and a
BGE quality-first operating point reaches +0.88 percentage points in mean
$\mathrm{Hit@10}$ with 7.23% saving. Geometry, random-route, no-feedback, and
arm-count controls show that local structure and feedback improve route-level
confidence signals, while dense/BM25 rescue can mask weak routes in final fused
quality. A matched selector audit does not show that learned confidence or
geometry predicts safe per-query compression better than random controls. In a
frozen 300-query downstream evaluation, BGE, E5, and
SentMMR-composed IntentRoute variants reduce context by 6.00%, 12.04%, and
6.65%, respectively, without a statistically detectable change in judged
answer correctness. Prompt compression and reranking remain complementary
downstream layers. The supported contribution is therefore a calibrated
route-and-budget controller, not universal superiority over dense retrieval or
a proof that manifold geometry alone determines relevance.
