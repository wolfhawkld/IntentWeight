# Abstract

Retrieval-augmented generation (RAG) systems must retrieve enough evidence to
support answer quality while limiting latency, noise, and final context cost.
This trade-off is especially difficult in vertical-domain corpora, where
relevance is shaped by domain terminology, local semantic neighborhoods,
workflow structure, and evolving user intent. We propose IntentWeight, a
feedback-driven adaptive retrieval controller for vertical-domain RAG.
IntentWeight combines dense retrieval, BM25 lexical recall, and cluster-local
retrieval under a piecewise relevance-manifold assumption, and uses
trust-weighted LinUCB to learn route preferences from simulated feedback. A
confidence-based final context policy then compacts the retrieved evidence sent
to the generator while preserving dense fallback under low confidence. On LoTTE
technology/search, evaluated from 100k to 638k corpus chunks, the conservative
policy reduces final retrieved context tokens by approximately 4.7-5.3% while
preserving near-dense Hit@10 at 100k and achieving mean above-dense Hit@10 at
200k, 400k, and 638k. Geometry diagnostics and ablations show that local
cluster structure provides useful routing signal, while dense retrieval remains
an important recall floor. A 60-query downstream generation smoke test shows no
obvious answer-quality degradation from the compressed context. These results
position IntentWeight not as a universal replacement for dense retrieval, but as
an adaptive quality-cost controller for large-scale vertical-domain RAG.
