# Abstract

Knowledge-augmented agents must select enough evidence to support answer
quality while limiting latency, noise, and final context cost. This trade-off is
especially difficult in vertical domains, where relevance depends on
terminology, local semantic neighborhoods, workflows, and evolving intent. We
propose IntentWeight, a feedback-adaptive evidence-selection controller
motivated by the hypothesis that vertical-domain query-document relevance often
exposes exploitable local structure rather than a uniform embedding-space
distribution. IntentWeight combines dense retrieval, BM25 recall, and
cluster-local routing; uses trust-weighted LinUCB to learn when compact local
evidence is reliable and when dense fallback is needed; and applies a
confidence-based policy to compact the final evidence sent to the generator.

We evaluate on LoTTE technology/search from 100k to 638k chunks. Under frozen
calibration/test budget policies, calibration-eligible operating points reduce
language-model input tokens consumed by retrieved evidence context by 6-18% at
100k, 200k, and 638k; a 400k diagnostic point shows positive frozen-test
behavior but fails the calibration eligibility gate. IntentWeight avoids the
larger $\mathrm{Hit@10}$ losses of dense-only adaptive truncation, although
strict seed-level non-inferiority is scale-dependent. Strong post-retrieval
baselines narrow the claim: sentence-level MMR compresses both dense and
IntentWeight evidence pools, while cross-encoder reranking improves top-ranked
support but can increase final context tokens without budget control. Results
replicate on LoTTE science/search with domain-calibrated compression, and
simulated feedback recovers a meaningful fraction of compression-induced tail
failures. IntentWeight is therefore a route-and-budget controller for
quality-efficiency trade-offs, not a replacement for dense retrieval,
compressors, or rerankers.
