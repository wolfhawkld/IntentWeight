# 4. Experimental Setup

## 4.1 Datasets

The experiments cover nine dataset settings across eight domain areas:
technology, science, recreation, writing, biomedical QA, banking intents,
product manuals, and legal contracts. They have different tasks, ground-truth
semantics, and evidentiary roles, so we do not treat them as equal support for
the main claim:

- **LoTTE technology/search** is the main large-scale vertical-domain evidence
  benchmark. We evaluate nested corpus scales from 100k to 638k chunks with
  596 test queries.
- **LoTTE science/search** is the cross-domain validation benchmark. It tests
  whether ranking and context-budget behavior transfer beyond technology/search
  at 20k/q200, 100k, 200k, and 400k scales. The 400k row is retained as a
  scale boundary rather than a lossless-compression replication.
- **LoTTE recreation/search and writing/search** are prospectively specified 100k
  external-validity tests with 924 and 1,071 positive-qrel queries,
  respectively. Both use the full common protocol and remain in the analysis
  after the prospectively specified lexicality ordering is contradicted by the measured
  query-positive overlap.
- **PubMedQA and CovidQA-RAG** are biomedical transfer checks. PubMedQA is an
  evidence-retrieval proof-of-concept with abstract-level ground truth and a
  near-ceiling dense baseline; CovidQA-RAG is a more discriminative native-full
  RAGBench evidence-retrieval row.
- **Banking77** is a supporting feedback-adaptation check for intent routing
  rather than a strict evidence-retrieval benchmark.
- **eManual and CUAD** are boundary cases. eManual exposes duplicate-text and
  strict chunk-id issues; CUAD is a sparse GT-anchored legal-domain smoke case.

This hierarchy separates full-stack evidence, cross-domain transfer, mechanism
transfer, and boundary analysis. The complete quality-efficiency claim is
anchored in LoTTE technology/search, science/search tests domain transfer, and
recreation/search and writing/search test domain heterogeneity under a matched
100k protocol. The secondary datasets test whether feedback behavior transfers,
whether a biomedical evidence-retrieval transfer row remains discriminative,
or where corpus duplication and sparse labels limit inference.

The supplementary protocol registry records the dataset/query scope, route-feedback
protocol, context-budget endpoint, and evidentiary role for each result family.
It distinguishes the common evidence-retrieval protocol from the Banking77
intent proxy, the CUAD sparse-GT boundary, and historical fixed-split
diagnostics. This prevents unlike evaluation families from being treated as
pooled replications.

## 4.2 Baselines and Variants

The baseline family includes:

- BM25-only lexical retrieval.
- Dense-only retrieval with `sentence-transformers/all-MiniLM-L6-v2`.
- Matched dense and IntentRoute variants with BGE-base and E5-base embeddings.
- BM25 + dense hybrid retrieval using reciprocal-rank fusion.
- Full multi-route IntentRoute.
- Gated cost-aware IntentRoute.
- Conservative confidence-conditioned final-context baseline.
- Dense+Sentence-MMR final-context compression.
- Cross-encoder reranking over dense top-50 candidates.
- Static geometry controls such as nearest-cluster routing.
- Naive controls such as random or epsilon-greedy arm selection.
- No-feedback and uniform-random route controls.
- Arm-count sensitivity over $K \in \{8,16,32,64,128\}$.

Dense-only retrieval is the primary quality baseline and remains a required
recall floor in the proposed method. Sentence-MMR is the matched downstream
compression baseline, while the cross-encoder tests whether a heavier late
ranking layer can select a smaller context more simply. These components are
not mutually exclusive alternatives to IntentRoute; they occupy different
stages in the retrieval-to-context pipeline.

## 4.3 Metrics

Retrieval quality is measured with:

- $\mathrm{Hit@K}$: whether any ground-truth chunk appears in the top $K$.
- $\mathrm{EvidenceRecall@K}$: fraction of all ground-truth chunks retrieved.
- $\mathrm{MRR@K}$: reciprocal rank of the first relevant chunk.
- $\mathrm{nDCG@K}$: binary relevance ranking quality.

For query $q_t$, let $G_t$ be the set of ground-truth chunks and let $R_t^K$
be the top-$K$ retrieved chunks. The query-level hit metric is:

$$
\mathrm{Hit@K}(q_t) =
\mathbb{1}\left[ R_t^K \cap G_t \neq \varnothing \right].
$$

The evidence-recall metric is:

$$
\mathrm{EvidenceRecall@K}(q_t) =
\frac{\left| R_t^K \cap G_t \right|}{\left|G_t\right|}.
$$

MRR@K uses the reciprocal rank of the first relevant chunk, and nDCG@K uses
binary relevance with logarithmic rank discount and the standard ideal-DCG
normalization. Supplementary Section S12 gives the explicit formulas and the
zero-relevance convention.

The main headline uses query-level $\mathrm{Hit@10}$. This choice reflects the
target use case: retrieving at least one usable evidence chunk for RAG
generation under a smaller context budget. It does not imply complete evidence
collection. $\mathrm{EvidenceRecall@10}$ is reported separately where
multi-evidence coverage is important.

Cost and efficiency are separated into three layers:

- Source candidate cost: number of candidates considered before final fusion.
- Dense invocation rate: fraction of queries using the global dense path.
- Final context tokens: token count of retrieved chunks sent to the generator.

The main cost result uses final context tokens. Source candidate cost and dense
invocation rate are retrieval-stage diagnostics.

The downstream evaluation additionally reports LLM-judge correctness and
faithfulness, strict chunk-id citation support, insufficient-context rate, and
context tokens per judged-correct answer. These metrics are secondary
answer-level validation of the route-and-budget claim, not evidence of
generator superiority.

Let $C_t$ be the final retrieved context selected for query $q_t$ and let
$\mathrm{tok}(d)$ be the token count of chunk $d$. The final context token cost
is:

$$
\mathrm{Tokens}(C_t) =
\sum_{d \in C_t} \mathrm{tok}(d).
$$

## 4.4 Geometry Diagnostics

The geometry diagnostics are used to test whether the corpus has usable local
structure for route control. They are diagnostic support for the
piecewise relevance-manifold assumption, not mathematical proof of a manifold.

Let $E \in \mathbb{R}^{n \times p}$ be a sampled matrix of corpus chunk
embeddings after mean-centering. Let
$\lambda_1 \ge \lambda_2 \ge \cdots \ge \lambda_p \ge 0$ be the eigenvalues of
the empirical covariance matrix. The explained variance retained by the first
$m$ principal components is:

$$
\mathrm{PCAvar@m} =
\frac{\sum_{i=1}^{m} \lambda_i}
     {\sum_{i=1}^{p} \lambda_i}.
$$

The dimension needed to explain 90% of the variance is:

$$
\mathrm{PCAdim90} =
\min \left\{m:
\frac{\sum_{i=1}^{m} \lambda_i}
     {\sum_{i=1}^{p} \lambda_i}
\ge 0.9
\right\}.
$$

For cluster diagnostics, let $y_t$ be the PCA/context representation of query
$q_t$, let $\mu_c$ be the centroid of cluster $c$, and let $\ell_i$ be the
cluster label of chunk $d_i$. The top-$K$ nearest clusters for query $q_t$ are:

$$
\mathcal{N}_K(q_t) =
\operatorname{TopK}_{c}
\left(\mu_c^\top y_t\right).
$$

Let $\mathcal{C}_t = \{\ell_i : d_i \in G_t\}$ be the set of clusters that
contain ground-truth evidence for query $q_t$. The nearest-cluster hit metric
is:

$$
\begin{aligned}
\mathrm{NearestClusterHit@K} &=
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}} \\
&\quad
\mathbb{1}
\left[
\mathcal{N}_K(q_t) \cap \mathcal{C}_t \neq \varnothing
\right].
\end{aligned}
$$

where $\mathcal{Q}_{GT}$ is the set of queries with at least one ground-truth
chunk in the evaluated corpus.

Finally, let $R_{t,\mathrm{ctx}}^K$ be the top-$K$ chunks retrieved by inner
product in the PCA/context space, and let $R_{t,\mathrm{dense}}^K$ be the
top-$K$ chunks retrieved by dense embedding similarity. We define:

$$
\begin{aligned}
\mathrm{ContextHit@K} &=
\frac{1}{|\mathcal{Q}_{GT}|}
\sum_{q_t \in \mathcal{Q}_{GT}} \\
&\quad
\mathbb{1}
\left[
R_{t,\mathrm{ctx}}^K \cap G_t \neq \varnothing
\right],
\end{aligned}
$$

and report context retention relative to dense retrieval:

$$
\mathrm{ContextRetention@K} =
\frac{\mathrm{ContextHit@K}}
     {\mathrm{DenseHit@K}}.
$$

If $\mathrm{DenseHit@K}=0$, we set $\mathrm{ContextRetention@K}=0$.

## 4.5 Prequential Simulated Feedback

Following the update order in Section 3.8, ground truth becomes a controlled
feedback proxy only after the current result is scored. Oracle feedback is a
learning upper bound; equal-noisy and trust-weighted modes model imperfect
signals with different reliability; no-feedback, static-nearest, and random-arm
controls separate adaptation from fixed or uninformative routing. Trust changes
update strength, never current-query label availability. This design tests
whether route state responds coherently to a declared signal, not whether
production feedback has already been collected or debiased.

Some experiments use multiple prequential epochs over the same query stream to
simulate repeated interaction. Every epoch preserves rank-then-update order;
these are route-adaptation studies, not IID held-out generalization.

The formal frozen-policy audit makes the complementary first-pass boundary
explicit. It trains route state on four disjoint query folds, freezes policy and
feedback memory, and ranks the fifth fold once without held-out updates. Across
LoTTE technology/search and science/search 100k, learned full routing remains
near or above Dense but does not exceed matched static-nearest or cold
no-feedback full routing; learned gating is significantly below Dense in all
three route seeds. This audit is retrieval-only and does not evaluate
final-context token saving or answer quality.

## 4.6 Implementation Notes

The main dense baseline uses Sentence Transformers `all-MiniLM-L6-v2` with exact
cosine search. Matched-backbone checks use BGE-base and `intfloat/e5-base-v2`;
E5 applies the recommended `query:` and `passage:` prefixes. Embeddings and
retrieval artifacts are cached to avoid repeating deterministic computation.
Metrics are recomputed from saved rankings, not copied from prior summaries.
Historical experiment directories and machine-readable method labels retain the
legacy `IntentWeight` identifier so that existing hashes, selectors, and result
provenance remain reproducible; paper-facing terminology uses `IntentRoute`.

KMeans/MiniBatchKMeans uses 32 arms in the main scale experiments. A dedicated
100k sensitivity check evaluates 8, 16, 32, 64, and 128 arms. This supports
LinUCB comparability and tests engineering sensitivity, but it is not claimed
to identify a theoretically optimal clustering design.

The Sentence-MMR baseline starts from dense or IntentRoute evidence pools,
splits selected chunks into sentence-like units, and greedily selects
query-relevant but diverse sentences under a target token ratio or per-query
budget. The cross-encoder baseline reranks dense top-50 candidates with
`cross-encoder/ms-marco-MiniLM-L-6-v2`; it is evaluated both as a full reranked
top-10 and as a same-budget variant constrained by the calibrated IntentRoute
per-query token budgets. Reranker compute cost is not charged in final context
tokens, so reranker results should be interpreted as retrieval-quality
baselines rather than end-to-end latency measurements.

## 4.7 Calibration and Paired Testing Protocol

The final-context budget experiments use a calibration/test split over queries.
For each scale, 30% of queries are used only to select a budget policy. The
selected policy is then frozen and evaluated on the remaining held-out test
queries. This avoids choosing a context budget after seeing test labels.

A budget policy name has the form `token_budget_rX_mY`. Here, `rX` is the
maximum final-context token ratio relative to the original top-10 context, and
`mY` is the minimum safe prefix kept before token-budget filtering. For example,
`token_budget_r0.85_m4` keeps at least four top-ranked chunks and then admits
additional chunks only while the final context remains within 85% of the
original top-10 token budget.

Calibration eligibility is defined using the mean calibration
$\mathrm{Hit@10}$ delta against dense top-10. The main calibration selection
uses a zero observed-hit-drop margin: a policy is eligible only when its mean
calibration hit delta is non-negative. Among eligible policies, the selected
policy is the one with the largest final-context token saving. If no policy is
eligible, the best diagnostic policy is still reported, but it is not treated
as a strict calibration-eligible main operating point.

Frozen test results are paired by query against dense top-10. We report
bootstrap confidence intervals for $\mathrm{Hit@10}$ deltas and final-context
token savings where available, and use a 1 percentage-point non-inferiority
margin as a strict seed-level engineering guardrail. On the original 417-query
frozen test split, one percentage point corresponds to roughly four query-hit
outcomes; on the 596-query out-of-fold population, it corresponds to roughly
six. Passing this diagnostic is not treated as formal equivalence, and failing
it does not erase the descriptive paired result. This separates two claims:
whether the method preserves retrieval quality under a conservative paired
criterion, and whether it reduces the final evidence-context tokens sent to
the generator.

The frozen calibration/test comparisons and the normalized five-fold scale
results are the primary evidence families. Fine-grid action selection,
overlapping-partition sensitivity, same-saving interpolation, arm-count and
geometry controls, feedback recovery, transfer datasets, and multi-judge
analysis are mechanism, robustness, or boundary analyses. We report their
paired statistics where available, but do not pool heterogeneous conditions or
use an unadjusted cross-condition $p$-value to assert a global superiority
claim. They are interpreted conditionally and labeled accordingly.

The prospectively specified domain expansion applies the normalized five-fold protocol to all
924 recreation/search and 1,071 writing/search positive-qrel queries. Each
domain uses the same MiniLM backbone, $K=32$, route seeds 13/17/19, eight
prequential epochs, fixed top-10 endpoint, predefined budget grid, zero-drop
eligibility gate, Dense fallback, paired bootstrap, McNemar analysis, and 1pp
seed-level non-inferiority guardrail. The domains are calibrated and reported
separately; no cross-domain pooled effect is computed.

Two additional audits test selection robustness. First, Dense and IntentRoute
independently select actions on the same 100k calibration split over a fine
ratio grid from 1.00 to 0.80 in 0.01 increments, so the comparison does not
force Dense to inherit the routed policy's nominal action. Second, the original
calibration grid is repeated over 20 deterministic 30/70 query partitions at each
scale. These overlapping partitions diagnose split sensitivity; they are not
treated as additional training seeds or independent inferential samples.

## 4.8 Downstream Answer-Level Protocol

The answer-level evaluation draws 300 deterministic queries from the 417-query
frozen test split. Seven methods cover MiniLM dense, BGE dense and IntentRoute,
E5 dense and IntentRoute, and matched Dense+SentMMR versus
IntentRoute+SentMMR. The `deepseek-v4-flash` configuration generates one answer
from each retrieved context. The fixed answers are independently judged by
`deepseek-v4-flash`, `glm-5.2`, and `minimax-m3` for correctness,
faithfulness, relevance, and citation support against reference evidence.

The run contains 2,100 generated answers and 6,265 schema-valid judgments:
2,100 each from DeepSeek and GLM-5.2 and 2,065 from MiniMax-M3. Thirty-five
MiniMax-M3 inputs are rejected by provider-side content filtering and are not
imputed. Cross-judge agreement uses the 2,065 query-method keys valid for all
three judges. Correctness and faithfulness differences use paired query-level
bootstrap intervals and exact McNemar tests within each judge and for the
three-judge majority. Raw ordinal scores are not pooled across judges. The
under-specified `insufficient_context_appropriate` field is retained in raw
artifacts but excluded from headline and agreement analyses. This protocol
supports multi-judge answer-level robustness, not human-rated superiority.
