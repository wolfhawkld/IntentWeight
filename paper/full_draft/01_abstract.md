# Abstract

Knowledge-augmented agents must select enough evidence to support answer
quality while limiting latency, noise, and final context cost. This trade-off is
especially difficult for vertical-domain data, where relevance is shaped by
domain terminology, local semantic neighborhoods, workflow structure, and
evolving user intent. We propose IntentWeight, a feedback-guided evidence
selection controller motivated by a piecewise relevance-manifold assumption.
Here, the assumption means that query-document relevance in vertical domains
often exposes exploitable local structure rather than a uniform embedding-space
distribution. IntentWeight combines dense semantic retrieval, BM25 lexical
recall, and cluster-local routing, and uses trust-weighted LinUCB to learn route
preferences from simulated feedback. A confidence-based final context policy
then compacts the selected evidence sent to the generator while preserving
dense fallback under low confidence. We instantiate this framework in
retrieval-augmented question answering on LoTTE technology/search from 100k to
638k corpus chunks. Frozen calibration/test budget policies save 6-18% of the
LLM input tokens consumed by retrieved evidence context while outperforming
dense-only adaptive truncation in $\mathrm{Hit@10}$, with scale-dependent
non-inferiority. A conservative confidence policy provides a stable 4.7-5.3%
saving baseline on the same generator-input-token measure. Results generalize
to a second LoTTE domain with domain-calibrated compression, and simulated
feedback recovers a meaningful fraction of compression-induced tail failures.
IntentWeight is therefore not a universal dense replacement, but an adaptive
quality-cost and recovery controller for structured domain evidence.
