# 8. Conclusion

This paper presents IntentWeight, a feedback-driven adaptive retrieval
controller for vertical-domain RAG. Instead of treating RAG retrieval as a fixed
top-k dense search, IntentWeight builds a multi-route retrieval surface over
dense, BM25, and cluster-local retrieval, uses trust-weighted LinUCB to learn
route preferences from controlled feedback, and applies confidence-based final
context compaction to reduce retrieved context tokens.

The main evidence comes from LoTTE technology/search at 100k to 638k corpus
chunks. Under the conservative confidence-based context policy, IntentWeight
reduces final retrieved context tokens by approximately 4.7-5.3% while
preserving dense-level $\mathrm{Hit@10}$. Mean $\mathrm{Hit@10}$ is above
dense-only retrieval at 200k, 400k, and 638k. Additional diagnostics show that
local geometry provides useful routing signal, trust-weighted feedback improves
route-policy metrics, and a small downstream generation smoke test does not
show obvious answer-quality degradation from context compaction.

The result is intentionally bounded. IntentWeight is not a universal dense
replacement, and it does not prove that geometry alone solves retrieval. Dense
retrieval remains an important recall floor. The contribution is a controller
that learns when multiple retrieval routes and route confidence can be used to
preserve retrieval quality while reducing the final context budget.
