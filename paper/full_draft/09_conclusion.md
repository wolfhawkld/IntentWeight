# 8. Conclusion

This paper presents IntentRoute, a feedback-adaptive route controller motivated
by local relevance structure. Geometry defines reproducible cluster-local
routes, trust-weighted LinUCB updates route state under controlled feedback,
Dense and BM25 provide rescue paths, and an independent calibration policy sets
the final evidence-context budget.

The evaluation spans nine dataset settings across eight domain areas, with
distinct full-stack, transfer, mechanism, and benchmark-boundary roles.

The main full-stack evaluation covers LoTTE technology/search from 100k to 638k
chunks. Calibration-eligible 100k, 200k, and 638k policies reduce final
evidence-input tokens by 6-18% while avoiding the larger $\mathrm{Hit@10}$
losses of Dense-only adaptive truncation. The normalized 400k follow-up yields
14.50% mean saving with no mean Hit change, but its selected policies remain
unstable and strict seed-level non-inferiority is not established. Matched BGE
and E5 comparisons retain near-Dense quality at about 12% saving, and the BGE
quality-first point demonstrates frontier tunability. On 300 frozen queries,
three LLM judges find 6-12% matched context savings without a statistically
detectable correctness difference, while faithfulness remains method-dependent.

Cross-domain results define the boundary rather than a universal guarantee.
Science/search shows that route signal can transfer while safe budget strength
changes with domain and scale. In the prospectively specified 100k expansion,
writing/search saves 10.09% at a +0.12pp mean Hit change and 2/3 strict seeds;
recreation/search saves 5.42% at -0.76pp and 0/3 strict seeds; trust-weighted
calibration falls back to Dense in both. Biomedical, banking, manual, and legal
settings provide transfer, mechanism, and benchmark-boundary checks without
being pooled as equivalent replications.

The controls separate the source of these outcomes. Geometry improves local
route metrics over random routing but does not directly predict compression
safety. Controlled feedback updates route state and can repair some same-query
tail failures, yet it does not beat matched static or cold full routing on the
formal frozen unseen-query audit. Sentence-MMR remains an effective shared
downstream compressor, while cross-encoder reranking can improve
evidence support but may increase context length. Route control, rescue,
reranking, compression, and final-budget calibration are therefore composable
system functions.

IntentRoute is not a universal Dense replacement or a theorem-level manifold
result. Its contribution is a bounded, auditable quality-context controller:
local geometry structures routes, controlled feedback adapts route state,
Dense remains the recall floor, and independent calibration trades compact
evidence input against retrieval risk. Total serving cost and real-user
feedback effectiveness remain deployment questions beyond the measured claim.
