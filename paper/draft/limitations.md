# Limitations Draft

Updated: 2026-06-11

IntentWeight should be presented with explicit boundaries. These limitations do
not invalidate the current paper claim, but they define what the current
experiments do and do not prove.

## Simulated Feedback

The current experiments use simulated feedback derived from ground truth and
controlled noise/trust settings. This validates whether the policy can improve
under a feedback signal, but it does not prove the same behavior under real
human feedback. Real deployments must handle delayed feedback, biased implicit
signals, adversarial or low-quality users, and non-stationary intent.

Task40 adds post-feedback hard-case recovery experiments, but those experiments
still use GT-derived simulated feedback. Same-query retry should be interpreted
as an engineering recovery test after a failed compressed answer, not as
first-pass IID held-out improvement. The result shows that feedback can repair
a meaningful fraction of affected queries when the evidence remains reachable
through the candidate pool and arm structure; it does not imply universal
recovery.

## Limited Generation Evaluation

The main experiments evaluate retrieval and final retrieved context tokens.
Task33.5 adds a 60-query LLM generation smoke test showing no obvious answer
quality degradation from Task29-C context compaction, but this is not a full
end-to-end human evaluation. The supported main claim remains evidence
retrieval and retrieved context budget, not generated answer superiority or
user satisfaction.

## Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentWeight should not be
claimed as a universal replacement for dense retrieval. The evidence supports a
controller that can reduce final context tokens while preserving dense-level
Hit@10 in the main LoTTE setting, and that can expose a quality-cost frontier
across routes.

## Evidence Completeness Trade-Off

The main retrieval headline is query-level `Hit@10`. Final context compaction
can preserve whether at least one relevant chunk is retrieved while reducing the
fraction of all ground-truth chunks retrieved (`evidence_recall@10`). For tasks
that require complete evidence collection, such as legal review, medical
evidence synthesis, or exhaustive compliance analysis, a more conservative
context policy or no compaction may be preferable.

## Context Budget Requires Domain Calibration

The LoTTE science/search replication shows that fixed top-10 ranking gains can
transfer to a second domain, but context-budget strength does not transfer
automatically. At science/search 100k, an aggressive budget still saves
17-21% final context tokens but can introduce small Hit@10 drops on the frozen
test split. Compression should therefore be calibrated per domain and scale,
with dense fallback retained for low-confidence or high-risk local regions.

## Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
nearest-cluster hit@3, PCA spectrum, and context retention. These diagnostics do
not prove a mathematical manifold theorem. They show that local geometry is
informative for routing on LoTTE, while dense retrieval remains necessary.

## Fixed Routing Arms Are an Experimental Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and the
experiments need reproducible, scalable arms. This is not a claim that KMeans is
the best clustering method for all RAG systems. HDBSCAN or graph-based clusters
may perform better in some deployments, but dynamic arm counts complicate the
current LinUCB setup.

## Limited Encoder Coverage

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2`. Task33.1a
adds a CPU-friendly robustness check with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, but the paper should still
not generalize the result to stronger domain-specific encoders, rerankers, or
late-interaction models without additional experiments.

## Seed Count

Task29.3 reports three-seed confidence intervals across LoTTE 100k-638k, and
Task33.6 extends LoTTE 100k to five seeds. These are useful engineering
stability diagnostics, but they should not be over-framed as strong statistical
significance proof, especially at the larger scales that remain three-seed
experiments. The LoTTE 400k token-saving interval is notably wider than the
other scales and should be interpreted as seed-level variance in route
confidence and context-budget control.

## Dataset-Specific Caveats

LoTTE is the main positive evidence for large-scale vertical-domain retrieval,
but the processed qrels do not provide true corpus topic labels. Geometry
validation therefore relies on computed retrieval geometry, not external topic
labels.

PubMedQA provides a useful feedback and manifold proof-of-concept, but its
ground truth is abstract-level context rather than strict answer-sentence
evidence.

Banking77 is an intent/domain routing proxy, not an evidence retrieval dataset.
It should be reported separately from LoTTE-style retrieval results.

eManual has heavy duplicate text and strict chunk-id labels. Low strict recall
therefore partly reflects evaluation friction rather than complete retrieval
failure.

CUAD currently remains a sparse GT-anchored smoke/stress case and should not be
used as main full-corpus evidence.

## Cost Interpretation

Task28 corrected the cost story. Source candidate count, dense invocation rate,
and final context tokens are separate metrics. The main token-efficiency claim
must use final retrieved context tokens from Task29, not earlier candidate-count
reductions.

Task38 and Task39 extend this point to LLM evidence-context input tokens under
calibration/test policies. These results support meaningful context-token
reduction, but they do not measure full production cost including indexing,
embedding refreshes, reranking, generation output tokens, or infrastructure
overhead.

## Future Work

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- larger end-to-end LLM answer-quality and citation-faithfulness studies;
- stronger dense encoders and rerankers;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- larger seed counts and additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.
- recovery policies evaluated with real delayed feedback rather than
  GT-derived same-query retry.
