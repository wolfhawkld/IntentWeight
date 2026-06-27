# 7. Limitations and Future Work

## 7.1 Simulated Feedback

The current experiments use simulated feedback derived from ground truth and
controlled noise/trust settings. This validates whether the policy can improve
under a feedback signal, but it does not prove the same behavior under real
human feedback. Real deployments must handle delayed feedback, biased implicit
signals, adversarial or low-quality users, and non-stationary intent.

The hard-case recovery experiment also uses GT-derived simulated feedback.
Same-query retry should be interpreted as an engineering recovery test after a
failed compressed answer, not as first-pass IID held-out improvement. The result
shows that feedback can repair a meaningful fraction of affected queries when
the evidence remains reachable through the candidate pool and arm structure; it
does not imply universal recovery.

## 7.2 Limited Generation Evaluation

The downstream evaluation expands to 300 frozen-test queries, seven methods,
2,100 generated answers, and 2,100 valid LLM judgments. It finds positive
context-token savings for matched BGE, E5, and SentMMR comparisons without a
statistically detectable correctness change. However, one model serves as both
generator and judge, no human ratings are collected, and the benchmark covers
one LoTTE domain. The result supports answer-level quality preservation under
this protocol, not generated-answer superiority or user satisfaction.

## 7.3 Dense Remains Strong

Dense-only retrieval remains a strong baseline. IntentRoute should not be
claimed as a universal replacement for dense retrieval. The evidence supports a
controller that can reduce final context tokens while preserving dense-level
$\mathrm{Hit@10}$ in the main LoTTE setting, and that can expose a quality-cost
frontier across routes.

## 7.4 Evidence Completeness Trade-Off

The main retrieval headline is query-level $\mathrm{Hit@10}$. Final context
compaction can preserve whether at least one relevant chunk is retrieved while
reducing the fraction of all ground-truth chunks retrieved. For tasks that
require complete evidence collection, such as legal review, medical evidence
synthesis, or exhaustive compliance analysis, a more conservative context
policy or no compaction may be preferable.

## 7.5 Context Budget Requires Domain Calibration

The LoTTE science/search replication shows that fixed top-10 ranking gains can
transfer to a second domain, but context-budget strength does not transfer
automatically. At science/search 100k, an aggressive budget still saves
17-21% final context tokens but can introduce small $\mathrm{Hit@10}$ drops on
the frozen test split. Compression should therefore be calibrated per domain
and scale, with dense fallback retained for low-confidence or high-risk local
regions.

## 7.6 Geometry Is Diagnostic, Not a Proof

The piecewise relevance-manifold framing is supported by diagnostics such as
$\mathrm{NearestClusterHit@3}$, PCA spectrum, and context retention. These
diagnostics do not prove a mathematical manifold theorem. They show that local
geometry is informative for routing on LoTTE, while dense retrieval remains
necessary.

## 7.7 Fixed Routing Arms Are an Experimental Design

KMeans/MiniBatchKMeans is used because LinUCB requires a fixed arm space and
the experiments need reproducible, scalable arms. This is not a claim that
KMeans is the best clustering method for all RAG systems. HDBSCAN or
graph-based clusters may perform better in some deployments, but dynamic arm
counts complicate the current LinUCB setup. The tested $K=8$-$128$ grid shows
stable full multi-route quality but sensitive gated routing, so $K=32$ remains
an engineering operating point rather than an optimum.

## 7.8 Limited Encoder and Domain Coverage

The paper evaluates matched MiniLM, BGE-base, and E5-base dense/IntentRoute
backbones, plus a QA-tuned MiniLM-family check and a cross-encoder reranker.
This establishes backbone-level robustness within the tested LoTTE setting,
but it does not cover domain-specific encoders, late-interaction models, or
proprietary embedding systems. The above-dense quality-first point is currently
demonstrated for BGE only; E5 supports a near-dense token-saving point instead.

LoTTE technology/search is the main positive large-scale domain. LoTTE
science/search strengthens external validity but does not replace evaluation on
additional vertical corpora.

## 7.9 Seed Count and 400k Variance

The stability analysis uses the fixed seeds 13, 17, and 19 across the main
LoTTE route experiments. These are engineering stability diagnostics, not a
claim that a large seed population has been sampled. Query-level paired tests
provide the main inferential evidence. The LoTTE 400k
token-saving interval is notably wider than the other scales and should be
interpreted as seed-level variance in route confidence and context-budget
control. In the calibrated-budget experiment, the 400k frozen-test result is
positive but the selected policy is not calibration-eligible under the
zero-observed-hit-drop gate; this scale is therefore marked as a follow-up
calibration gap rather than pooled into the strongest eligible operating-point
claim.

## 7.10 Future Work

Future work should evaluate:

- real user feedback with trust scoring and delayed-feedback handling;
- multi-model and human-rated answer-quality and citation-faithfulness studies;
- stronger dense encoders, rerankers, and late-interaction retrieval models;
- graph or density-based dynamic clustering under bandit-compatible arm
  management;
- repeated evaluations on additional vertical-domain corpora;
- production policies that lower dense usage only after route confidence is
  demonstrably stable.
- recovery policies evaluated with real delayed feedback rather than
  GT-derived same-query retry.
