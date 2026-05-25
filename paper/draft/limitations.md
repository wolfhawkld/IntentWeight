# Limitations Draft

Updated: 2026-05-25

IntentWeight should be presented with explicit boundaries. These limitations do
not invalidate the current paper claim, but they define what the current
experiments do and do not prove.

## Simulated Feedback

The current experiments use simulated feedback derived from ground truth and
controlled noise/trust settings. This validates whether the policy can improve
under a feedback signal, but it does not prove the same behavior under real
human feedback. Real deployments must handle delayed feedback, biased implicit
signals, adversarial or low-quality users, and non-stationary intent.

## Retrieval Layer Only

The experiments stop at retrieval and final retrieved context tokens. They do
not evaluate end-to-end LLM answer generation, answer faithfulness, or user
satisfaction. The supported claim is about evidence retrieval and retrieved
context budget, not generated answer quality.

## Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentWeight should not be
claimed as a universal replacement for dense retrieval. The evidence supports a
controller that can reduce final context tokens while preserving near- or
above-dense Hit@10 in the main LoTTE setting, and that can expose a quality-cost
frontier across routes.

## Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
nearest-cluster hit@3, PCA spectrum, and context retention. These diagnostics do
not prove a mathematical manifold theorem. They show that local geometry is
informative for routing on LoTTE, while dense retrieval remains necessary.

## KMeans Is an Experimental Arm Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and the
experiments need reproducible, scalable arms. This is not a claim that KMeans is
the best clustering method for all RAG systems. HDBSCAN or graph-based clusters
may perform better in some deployments, but dynamic arm counts complicate the
current LinUCB setup.

## Limited Encoder Coverage

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2`. The paper
should not generalize the result to stronger domain-specific encoders, rerankers,
or late-interaction models without additional experiments.

## Seed Count

Task29.3 reports three-seed confidence intervals. These are useful engineering
stability diagnostics, but they should not be over-framed as strong statistical
significance proof.

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

## Future Work

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- end-to-end LLM answer quality and citation faithfulness;
- stronger dense encoders and rerankers;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- larger seed counts and additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.
