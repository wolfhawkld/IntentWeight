# 7. Limitations and Future Work

## 7.1 Simulated Feedback

The current experiments use simulated feedback derived from ground truth and
controlled noise/trust settings. This validates whether the policy can improve
under a feedback signal, but it does not prove the same behavior under real
human feedback. Real deployments must handle delayed feedback, biased implicit
signals, adversarial or low-quality users, and non-stationary intent.

## 7.2 Limited Generation Evaluation

The main experiments evaluate retrieval and final retrieved context tokens.
Task33.5 adds a 60-query LLM generation smoke test showing no obvious answer
quality degradation from Task29-C context compaction, but this is not a full
end-to-end human evaluation. The supported main claim remains evidence retrieval
and retrieved context budget, not generated answer superiority or user
satisfaction.

## 7.3 Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentWeight should not be
claimed as a universal replacement for dense retrieval. The evidence supports a
controller that can reduce final context tokens while preserving dense-level
Hit@10 in the main LoTTE setting, and that can expose a quality-cost frontier
across routes.

## 7.4 Evidence Completeness Trade-Off

The main retrieval headline is query-level Hit@10. Final context compaction can
preserve whether at least one relevant chunk is retrieved while reducing the
fraction of all ground-truth chunks retrieved. For tasks that require complete
evidence collection, such as legal review, medical evidence synthesis, or
exhaustive compliance analysis, a more conservative context policy or no
compaction may be preferable.

## 7.5 Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
nearest-cluster hit@3, PCA spectrum, and context retention. These diagnostics do
not prove a mathematical manifold theorem. They show that local geometry is
informative for routing on LoTTE, while dense retrieval remains necessary.

## 7.6 KMeans Is an Experimental Arm Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and
the experiments need reproducible, scalable arms. This is not a claim that
KMeans is the best clustering method for all RAG systems. HDBSCAN or
graph-based clusters may perform better in some deployments, but dynamic arm
counts complicate the current LinUCB setup.

## 7.7 Limited Encoder and Domain Coverage

The main dense baseline uses `sentence-transformers/all-MiniLM-L6-v2`. Task33.1a
adds a CPU-friendly robustness check with
`sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, but the paper should not
generalize the result to stronger domain-specific encoders, rerankers, or
late-interaction models without additional experiments.

LoTTE technology/search is the main positive large-scale domain. Additional
LoTTE domains or other vertical corpora would strengthen external validity.

## 7.8 Seed Count and 400k Variance

Task29.3 reports three-seed confidence intervals across LoTTE 100k-638k, and
Task33.6 extends LoTTE 100k to five seeds. These are useful engineering
stability diagnostics, but they should not be over-framed as strong statistical
significance proof. The LoTTE 400k token-saving interval is notably wider than
the other scales and should be interpreted as seed-level variance in route
confidence and context-budget control.

## 7.9 Future Work

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- larger end-to-end LLM answer-quality and citation-faithfulness studies;
- stronger dense encoders, rerankers, and late-interaction retrieval models;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- larger seed counts and additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.
