# Abstract Draft

Updated: 2026-06-11

## Primary Draft

Retrieval-augmented generation systems must retrieve enough evidence to preserve
answer quality while limiting latency, noise, and final context cost. This
trade-off is especially difficult in vertical-domain corpora, where relevance is
shaped by domain terminology, local semantic neighborhoods, and evolving user
intent. We propose IntentWeight, a feedback-driven adaptive retrieval controller
for vertical-domain RAG. IntentWeight combines dense retrieval, BM25 lexical
recall, and cluster-local retrieval under a piecewise relevance-manifold
assumption, and uses trust-weighted LinUCB to learn route preferences from
simulated feedback. A confidence-based final context policy then compacts the
retrieved evidence sent to the generator while preserving dense fallback under
low confidence. On LoTTE technology/search, evaluated from 100k to 638k corpus
chunks, the conservative policy reduces final retrieved context tokens by
approximately 4.7-5.3% while preserving near-dense Hit@10 at 100k and achieving
mean above-dense Hit@10 at 200k, 400k, and 638k. A calibration/test validation
further shows that budgeted final contexts can save 6-18% evidence-context
tokens under frozen policy selection, though strict seed-level non-inferiority
is scale-dependent. On a second LoTTE science/search domain, IntentWeight
improves fixed top-10 ranking quality at both 20k and 100k scales, while
revealing that context-compression strength must be domain calibrated. Finally,
feedback-driven hard-case recovery experiments show that simulated feedback can
repair a meaningful fraction of budget-induced tail failures in post-feedback
retry. Geometry diagnostics and ablations show that local cluster structure
provides useful routing signal, while dense retrieval remains an important
recall floor. These results position IntentWeight not as a universal
replacement for dense retrieval, but as an adaptive quality-cost and recovery
controller for large-scale vertical-domain retrieval.

## Shorter Variant

We present IntentWeight, a feedback-driven adaptive retrieval controller for
vertical-domain RAG. Instead of relying on a single fixed retriever, IntentWeight
routes queries over dense, BM25, and cluster-local retrieval surfaces, learns
route value with trust-weighted LinUCB, and applies confidence-based final
context compaction. On LoTTE technology/search up to 638k corpus chunks, the
conservative policy reduces final retrieved context tokens by 4.7-5.3% while
preserving dense-level Hit@10, and calibration/test experiments show larger
context-token savings under frozen policy selection. Cross-domain LoTTE
science/search results support ranking-side generalization, while hard-case
recovery experiments show that feedback-triggered fallback can repair a
meaningful fraction of budget-induced failures. The results support a bounded
claim: feedback and geometry can help control retrieval quality, context budget,
and tail-query recovery, but dense retrieval remains a necessary recall floor.

## Abstract Claim Checklist

- Mentions vertical-domain RAG and the retrieval trade-off.
- States that feedback is simulated, not real human feedback.
- Reports final context-token reduction, not source-candidate reduction.
- Uses LoTTE scale-up as the main evidence.
- Includes cross-domain and recovery evidence without making them the main
  headline.
- Avoids universal dense replacement claims.
- Avoids statistically significant improvement claims where CI does not support
  them.
- Avoids end-to-end LLM answer-quality claims.
