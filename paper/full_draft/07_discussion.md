# 6. Discussion

## 6.1 Supported Claim

IntentRoute supports a bounded confidence-gated-route plus calibrated-budget
claim. It gates dense, lexical, and geometry-defined local routes using
trust-weighted adaptive confidence, then applies a separately frozen
final-context policy. On LoTTE technology/search, eligible 100k, 200k, and 638k
points save 6--18% evidence-context tokens while avoiding the larger
$\mathrm{Hit@10}$ losses of dense-only truncation. The original 400k point is
calibration-ineligible despite a positive frozen-test result; a normalized
five-fold audit yields 14.50% mean saving with no mean Hit change, but varying
policies and no strict seed-level non-inferiority. The conservative
confidence-only policy provides a stable 4.7--5.3% saving baseline.

Matched BGE/E5 results extend the quality-cost pattern beyond MiniLM. The
300-query, three-judge evaluation finds positive savings without a statistically
detectable correctness change, but negative BGE/E5 point estimates from stricter
judges and a majority-detected BGE faithfulness decrease preclude uniform
answer-quality non-inferiority. Science/search supports ranking transfer while
requiring domain- and scale-specific budget calibration. Recreation/search and
writing/search retain local route signal, yet only writing/search provides a
useful 10.09% cross-fitted saving point with a slightly positive mean Hit change
and only 2/3 strict non-inferiority seeds; trust-weighted calibration safely falls back to Dense
in both.

The nine settings retain distinct evidentiary roles. PubMedQA shows biomedical
route adaptation near a dense ceiling; CovidQA-RAG adds a discriminative
transfer row with savings and a small mean hit loss; Banking77 supplies an
intent-routing feedback proxy; and eManual/CUAD expose duplicate, identity, and
sparse-label boundaries. They are transfer, mechanism, and boundary evidence,
not a pooled score or nine equivalent full-stack replications.

Dense retrieval remains the primary quality baseline and recall floor;
IntentRoute's contribution is separating adaptive route control, dense rescue,
and calibrated final-context compaction.

## 6.2 Role of Calibrated Context Budgeting

A static dense, BM25, and cluster-local combination can improve coverage yet use
more final-context tokens by surfacing longer or noisier chunks. Savings come
from the calibrated budget after confidence-gated route construction, not from
adding routes alone.

The conservative policy compresses only high-confidence cases to $k=8$ and
keeps mid-confidence cases at $k=10$, producing modest but stable savings. Frozen
calibrated budgets expose a stronger frontier, whereas simply truncating dense
top-$k$ causes visible $\mathrm{Hit@10}$ loss. The conservative result is an
empirical baseline, not a maximum-compression or per-query safety guarantee.

Under the same cross-fitted zero-drop gate, prefix-only Dense selects no
compressed action at any scale, whereas IntentRoute selects one in every 200k,
400k, and 638k fold. This indicates calibration headroom in the routed ranking,
not safety for every route or partition.

At 100k, no-feedback writing/search admits compression in all folds,
recreation/search in four, and the trust-weighted controller in none. Dense
fallback is therefore a valid calibrated outcome: route signal and a safe
budget frontier must be established separately by domain.

## 6.3 Reranking and Final-Context Control

A cross-encoder reranker reorders a candidate pool but neither expands its
recall nor controls LLM input length. On LoTTE technology/search 100k, reranking
dense top-50 improves full top-10 $\mathrm{Hit@10}$ and
$\mathrm{EvidenceRecall@10}$ from 0.8705/0.7081 to 0.8777/0.7332, while selecting
21.9% more evidence-context tokens than dense top-10.

Thus IntentRoute controls the upstream evidence pool and budget, reranking is a
late ranking layer, and SentMMR compresses downstream.
Under IntentRoute's per-query budgets, cross-encoder $\mathrm{Hit@10}$ does not
uniformly dominate calibrated IntentRoute. The components should be evaluated
as a composable pipeline with an explicit quality-cost frontier, not as mutually
exclusive alternatives.

## 6.4 Feedback Updates Route State under Controlled Credit

Dense/BM25 fallback can saturate fused $\mathrm{Hit@10}$, so feedback is clearer
in selected-cluster hit and last-true-reward metrics.

Under controlled simulated feedback, route reward reaches 0.6790, above the
no-feedback/random level near 0.15 but below the 0.8563 static-nearest prior.
Cluster-credit controls show learnable oracle capacity and conditional noisy
gains, but no stable trust-weighted advantage over static geometry. Feedback is
therefore a controlled route-state update, not the sole source of fused quality
or a universal gain (Section 7.1).

The supported ordering is deliberately limited: an observed outcome updates
later LinUCB route state; that state and the geometry-defined arms influence
route selection, confidence, and fallback; an independently calibrated budget
then acts on the fused ranking. Neither feedback nor route confidence directly
sets a per-query compression ratio, so the token-saving frontier belongs to the
complete controller rather than to a single causal arrow.

When aggressive compaction loses evidence, arm-level feedback can repair a
meaningful fraction of affected queries through safer retry or fallback. This
controlled recovery does not justify globally boosting the same arm for future
queries.

A frozen-trajectory counterfactual locates this effect. Frequency-preserving
confidence-tier shuffling lowers Hit@10 by 4.80pp. The original assignment sends
high-confidence queries to a cluster-primary route with source Hit@10 0.924 and
retains fallback for low-confidence queries, whose forced cluster-primary Hit@10
is 0.240. Confidence supports route-shape assignment before, and separately
from, final-context budgeting.

## 6.5 Geometry Is Useful but Not Sufficient

Geometry diagnostics support the piecewise relevance-manifold framing:
$\mathrm{NearestClusterHit@3}$ remains high across technology/search scales and
reaches 0.8366/0.8655 in recreation/search and writing/search. Yet context
retention and calibrated savings vary by scale and domain, and early cluster
pruning can lose evidence.

Geometry is therefore one controller signal alongside dense fallback, BM25
lexical anchors, and LinUCB confidence adaptation.

Static geometry strongly improves route reward and cluster hit over random
routing, while Dense/BM25 rescue protects fused hit in both. Mixed small-sample
correlations with final token-quality gain confirm that geometry guides route
construction but does not determine the calibrated controller's outcome.

A factorial audit fixes dense top-10, split, budget grid, and seeds while
crossing geometry/random partitions with feedback/no feedback. Geometry with
feedback does not beat random-partition feedback in failure discrimination
(mean AUROC 0.434 versus 0.573); near 10% saving, their Hit@10 differs by only
+0.08pp and every seed-level paired bootstrap interval includes zero. Because
97.8% of actions are safe, this is boundary evidence, not inverse prediction;
the 6--18% frontier cannot be attributed directly to per-query confidence
precision.

The replay also finds mean Spearman $-0.056$ between confidence and oracle
safe-token headroom, with all seed intervals including zero; dynamic routing has
fewer relevant top-10 chunks than fixed fusion (2.121 versus 2.315). Confidence
therefore assigns route shapes without the severe loss of shuffled or
unconditional cluster-primary routing, rather than creating redundancy that
directly predicts safe compaction.

## 6.6 Evidence Completeness Versus Usable Evidence

Query-level $\mathrm{Hit@10}$ asks whether the final context contains any
relevant chunk; $\mathrm{EvidenceRecall@10}$ measures coverage of all GT chunks.
Compaction can preserve the former while reducing the latter. IntentRoute thus
targets usable, not exhaustive, evidence; legal, medical, or compliance tasks
requiring completeness should use conservative budgets or disable compaction.

## 6.7 Production Interpretation

The measured 6--18% reduction lowers generation-stage evidence input; at a
declared provider input-token price, the same percentage applies only to that
price component. Total serving cost also includes prompts, outputs, model
execution, retrieval, routing, caching, and infrastructure; latency, memory, and
energy were not measured. The 4.7--5.3% confidence-only policy is a stable
input baseline, while calibrated budgets expose the stronger bounded frontier.
Richer post-fusion features may support a future safety estimator, but route
confidence alone is not one here.

The correct deployment interpretation is therefore:

- keep dense retrieval as a recall floor and optionally rerank before final
  context selection;
- use feedback and confidence for route control, while calibrating the final
  context budget separately;
- use negative feedback for safer retry or fallback rather than as a direct
  compression-ratio signal;
- monitor evidence quality and fallback rates, and disable aggressive
  compaction for complete-evidence tasks;
- treat evidence-input saving as a controllable frontier and measure total
  system cost separately.
