# IntentWeight Research Hypothesis and Theory

**Created**: 2026-04-28
**Status**: Working paper-positioning summary

---

## Core Claim

IntentWeight is not primarily a study of a single algorithm such as LinUCB. Its core research question is:

> Do domain-specific RAG corpora exhibit exploitable semantic manifold structure, and can that structure support a self-evolving retrieval system through clustering, online bandit navigation, and feedback-driven value updates?

In Chinese:

> IntentWeight 研究垂类 RAG 语料是否存在可利用的语义流形结构，并进一步验证该结构能否作为系统自进化的基础：通过聚类识别局部语义区域，通过上下文 Bandit 学习检索导航策略，通过问答反馈持续更新流形上的价值场，最终实现 RAG 系统的自动优化与升级。

---

## Research Chain

The project follows this chain of hypotheses:

```text
垂类 RAG 数据是否存在可利用的语义流形结构？
        ↓
如果存在，能否通过聚类/降维识别其局部结构？
        ↓
如果局部结构可识别，能否把检索视为流形上的导航问题？
        ↓
如果检索是导航问题，用户/GT 反馈能否持续修正导航价值场？
        ↓
最终能否形成自动升级、自我进化的 RAG 系统？
```

This reframes retrieval optimization from "find the nearest chunk once" to "learn how to navigate a domain semantic manifold over time."

---

## Layer 1: Verifying the Manifold Hypothesis

The first layer of the research is to show that domain-specific knowledge data is not random scatter in a high-dimensional embedding space. It should have usable structure:

- embeddings concentrate around lower-dimensional effective structure;
- PCA or similar reductions preserve most useful variation;
- clustering reveals semantically coherent local regions;
- domains, intents, document types, or evidence types show spatial regularity;
- local neighborhoods correlate with retrieval relevance and feedback outcomes.

This layer answers:

> Why is it valid to model RAG retrieval as navigation over a semantic manifold?

---

## Layer 2: Self-Evolving Optimization on the Manifold

If the manifold hypothesis holds, RAG should not remain a static nearest-neighbor system. The system should learn:

- which semantic regions are valuable for different query types;
- which retrieval route works best for each query context;
- which user feedback is trustworthy;
- which local feedback should propagate to nearby regions;
- which aliases, corrections, and knowledge gaps should be persisted as system updates.

This layer corresponds to:

- clustering and local semantic-region discovery;
- BM25, dense, and hybrid retrieval inside or across regions;
- LinUCB online navigation;
- multi-dimensional reward from explicit, implicit, and contextual feedback;
- user credibility and anti-poisoning;
- insight extraction, alias expansion, correction memory, and knowledge-gap accumulation;
- future manifold-local feedback propagation.

---

## Dynamic Value Manifold

The central theoretical abstraction is the Dynamic Value Manifold (DVM):

```text
M       = fixed semantic geometry from embeddings
V(x, t) = time-varying value field shaped by feedback
M*      = (M, V), the dynamic value manifold
```

The embedding model defines the relatively stable geometric manifold `M`. User feedback, historical rewards, cluster behavior, domain signals, and credibility shape the value field `V(x, t)`.

LinUCB is one practical parameterization of that value field:

```text
V(x, t) ~= theta(t)^T phi(x)
```

where `phi(x)` contains query, cluster, retrieval, and feedback-context features, and `theta(t)` changes as feedback arrives.

Thus, LinUCB is a mechanism for learning the value field and navigation policy. It is not the research object by itself.

---

## Distinction From Existing RAG Optimization

| Direction | What It Optimizes |
|-----------|-------------------|
| Traditional RAG | Static nearest-neighbor retrieval in embedding space |
| Hybrid RAG | Lexical + semantic scoring |
| Graph / HypRAG / GNN-RAG | Geometry or graph structure `M` |
| IntentWeight | Dynamic value field `V(x, t)` over a fixed domain manifold |

The key distinction is:

> Existing manifold-aware approaches often change or enrich the geometry. IntentWeight keeps the geometry mostly fixed and learns where value lies on that geometry as interactions accumulate.

This makes the system lightweight, CPU-friendly, and suitable for low-data enterprise deployment.

---

## Role of Current and Future Tasks

The current experiment pipeline maps to the theory as follows:

| Task Area | Role in Theory |
|-----------|----------------|
| Static BM25/dense/hybrid baselines | Establish non-learning retrieval baselines |
| Guardrails and comparison tables | Prevent invalid claims across split/sample/task-type boundaries |
| Global LinUCB baseline | First implementation of online value-field learning |
| Manifold-local feedback | Make feedback propagation local in semantic geometry |
| Global vs local comparison | Test whether manifold-aware feedback improves convergence and stability |
| Soft-routed multi-route retrieval | Combine dense/BM25 bypass with LinUCB-selected local manifold retrieval to avoid hard-pruning loss |
| Manifold diagnostics | Directly test PCA concentration, cluster/local purity, and query-to-GT cluster routing |
| Paper synthesis | Turn the theory and experiments into a coherent system-paper argument |

For Task 11-13, the intended progression is:

1. **Task 11**: evaluate global LinUCB as the online-learning baseline;
2. **Task 12**: implement manifold-local feedback using neighborhood distance, cross-arm decay, and possibly local credibility;
3. **Task 13**: compare global value updates against manifold-local value propagation.
4. **Task 13.5**: replace hard cluster pruning with soft multi-route retrieval, using global dense/BM25 as a recall floor and LinUCB-selected clusters as the adaptive local-manifold route.
5. **Task 14**: directly diagnose the manifold assumption by measuring PCA spectrum, local neighborhood purity, metadata-label alignment, nearest-cluster GT hit rates, and context-space recall retention.
6. **Task 14.5**: isolate the eManual negative case by separating strict chunk-id recall, text-equivalent evidence recall, duplicate-text effects, and centroid-routing geometry from LinUCB policy quality.

---

## Lessons From Task 14

Task 14 separates the manifold hypothesis from the retrieval policy. It asks
whether the geometry itself contains useful signal before asking whether LinUCB
has learned to exploit that signal.

The diagnostics show four different regimes:

- **Banking77** has the clearest local structure: intent labels align with local
  neighborhoods, nearest clusters almost always contain GT chunks, and
  soft-routing performance matches or slightly exceeds dense retrieval.
- **PubMedQA** has strong GT-cluster routing and high context-space recall
  retention, even though document-level metadata labels are not a perfect proxy
  for semantic neighborhoods. Here Task 13.5 mainly preserves a strong dense
  baseline while avoiding hard-pruning loss.
- **CUAD smoke** has weak local purity and only moderate nearest-cluster hit
  rates. Its slight Task 13.5 gain should be interpreted as a sampled robustness
  result, not as full legal-domain superiority.
- **eManual** is the key negative case: nearest-cluster hit@3 and context-space
  GT recall are not weak, but Task 13.5 remains far below dense. This means the
  failure is likely not simply "no manifold structure"; it is more likely an arm
  selection, credit assignment, fusion/ranking, or feedback-utilization problem.

This improves the paper argument. The manifold assumption is no longer only a
theoretical metaphor: it is measured with independent diagnostics. At the same
time, the diagnostics prevent overclaiming by showing where the current policy
does not yet exploit available geometry.

## Lessons From Task 14.5

Task 14.5 refines the eManual interpretation. The low strict Task 13.5 score
does not by itself falsify the manifold hypothesis.

The eManual corpus has a special structure:

- 18812 sentence chunks collapse to only 1729 unique normalized sentence texts;
- all 861 test GT references have duplicate text elsewhere in the corpus;
- each GT text appears 22.26 times on average;
- the available `record_id` label is an instance/context-set identifier, not a
  domain topic or function label.

This means low `record_id` purity is not reliable evidence against local
semantic geometry, and strict chunk-id recall can underestimate evidence
retrieval. A system can retrieve the same manual sentence from another record
and still receive zero strict credit.

Task 14.5 confirms this gap:

- dense recall@10 rises from 0.3231 strict chunk-id to 0.5615
  text-equivalent;
- Task13.5 soft recall@10 rises from 0.1436 strict chunk-id to 0.5795
  text-equivalent;
- deduplicated dense and hybrid recall@10 both reach 0.8615;
- nearest-centroid 3-cluster routing reaches 0.5462 text-equivalent recall@10,
  while LinUCB selected-cluster hit remains only 0.2641.

Therefore eManual should be treated as a policy/measurement boundary case, not
as a clean no-manifold case. The geometry contains usable evidence signal, but
the current LinUCB arm selection, reward credit assignment, and fusion/ranking
do not reliably turn that signal into strict chunk-id hits. In the paper, strict
chunk-id metrics should remain the guarded main result, while text-equivalent
and deduplicated-corpus results should be reported as diagnostic evidence.

## Ablation as Core Evidence

Because IntentWeight is a composite retrieval policy rather than a single
retriever, ablation is not optional. It is the main way to turn mixed results
into mechanism-level evidence.

The final system combines BM25, dense retrieval, cluster-local retrieval,
LinUCB, feedback, fusion, dense floors, and guardrails. A single final score
cannot answer whether improvement comes from lexical coverage, semantic recall,
local manifold navigation, online policy learning, or simply the dense fallback.
It also cannot explain whether failures come from weak geometry, wrong arm
selection, reward attribution, fusion calibration, or strict evaluation labels.

The paper should therefore include ablations for:

- retrieval components: dense-only, BM25-only, static hybrid, hard cluster
  pruning, hard LinUCB, soft routing, without BM25, without cluster route, and
  without dense floor;
- feedback: no feedback, GT-derived feedback, noisy feedback,
  trust-weighted feedback, and feedback-budget curves;
- manifold diagnostics: nearest-centroid routing, LinUCB-selected clusters,
  GT-cluster oracle, local purity, and context-recall retention;
- eManual correction studies: strict chunk-id vs text-equivalent evaluation,
  duplicated vs deduplicated corpus, text-equivalent reward, nearest-centroid
  warm start, and fusion calibration;
- cost: full multi-route retrieval, confidence-gated routing, reduced dense/BM25
  depth, candidate count, context token count, and latency.

This framing makes the central claim more defensible: the method is not a
universal dense replacement, but an adaptive retrieval-control framework whose
benefit depends on measurable corpus structure, feedback quality, and
cost-quality trade-offs.

## Dense as Fallback, Not Enemy

Dense retrieval is a strong baseline. The paper should not frame IntentWeight
as a universal replacement for dense retrieval. The stronger claim is that dense
retrieval can be placed inside a self-evolving retrieval-control system.

In early or uncertain states, dense/BM25 provide a robust recall floor. As
feedback accumulates, LinUCB can learn when cheaper or more localized routes are
reliable enough and when dense retrieval should be reduced to a fallback safety
channel. This creates a staged operating model:

```text
robustness phase: dense + BM25 + cluster-local retrieval all active
self-evolution phase: feedback updates arm and route values
efficiency phase: high-confidence routes reduce dense/BM25 depth or weight
safety phase: low confidence, drift, or negative feedback reactivates dense
```

Therefore the key value is not that the static policy always beats dense on
small public benchmarks. The key value is that, in large-scale vertical RAG
systems, retrieval can become a feedback-driven policy that controls where to
search, how much to search, when to pay for dense fallback, and how to trade
quality against cost and latency.

---

## Lessons From Task 13.5

Task 13.5 changes the practical interpretation of the method. LinUCB should not
be treated as a replacement for dense retrieval or BM25. Instead, it should be
treated as an adaptive policy over multiple retrieval routes.

Current retrieval routes:

- **global dense**: semantic recall and stable fallback;
- **global BM25**: lexical, entity, term, and exact-match coverage;
- **LinUCB-selected cluster-local dense**: adaptive local-manifold navigation;
- **weighted fusion and dense floor**: reduce the risk that fusion noise removes
  strong dense candidates.

The resulting system is better described as:

> LinUCB-guided adaptive multi-route retrieval over a domain relevance manifold.

This formulation is more defensible than claiming that LinUCB alone should beat
dense retrieval. It also explains the mixed experimental results:

- PubMedQA and Banking77 show that soft routing can recover most hard-pruning
  losses and approach or match dense retrieval.
- CUAD smoke/sample slightly improves over dense under the GT-anchored sample,
  but remains only a smoke result.
- eManual remains below dense, showing that sparse evidence, long-document
  structure, cluster quality, or source-retriever weakness can still dominate.

Therefore the current evidence supports a robustness and adaptivity claim, not a
universal accuracy dominance claim.

---

## Stability, Self-Evolution, and Cost

The current architecture has two near-term advantages and one future-facing
advantage.

**Stability** comes from the dense/BM25 bypass and dense floor. These channels
prevent the system from losing all relevant evidence when LinUCB selects the
wrong cluster arm.

**Self-evolution** comes from feedback-updated LinUCB arms. As interactions
accumulate, LinUCB can learn which local semantic regions and retrieval routes
produce higher reward for each query context. If user credibility scores are
used, feedback can be reliability-weighted so that high-trust users have more
impact on the online value-field update and noisy users have less impact.

**Cost reduction** is not the main property of Task 13.5 itself, because Task
13.5 runs multiple retrieval routes for robustness. The cost advantage should be
framed as a later cost-aware phase:

```text
reward = quality - lambda_cost * retrieval_cost
                 - lambda_token * context_tokens
                 - lambda_latency * latency
```

After LinUCB becomes confident in specific arms, the system can reduce global
dense/BM25 depth or weight, rely more on high-confidence cluster-local retrieval,
and shrink rerank candidates and final LLM context. This gives a plausible path
from robust retrieval to cost-aware adaptive pruning.

---

## Retrieval-Only Evaluation and Feedback Semantics

The current experiments intentionally evaluate the retrieval layer before adding
LLM generation. This is appropriate for the current research stage because the
method changes context selection, corpus pruning, multi-route recall, cluster
routing, and feedback-updated arm selection. The tested question is whether the
system can retrieve the correct evidence chunks, not whether a particular LLM can
write the final answer.

The evaluation therefore uses Recall@k, MRR@k, and nDCG@k over
`ground_truth_chunk_ids`. Correct context is a necessary condition for grounded
answer quality, but not a sufficient condition. End-to-end LLM answer relevance,
faithfulness, citation correctness, and LLM-as-judge or RAGAS-style metrics
remain future extensions.

Ignoring the LLM stage does not break the feedback loop. In the current
prequential experiments, GT-derived reward is attached to retrieval outputs. In
a deployed system, the same update can use user feedback attached to contexts,
chunks, citations, or retrieval routes:

```text
query -> multi-route retrieval -> context/citation exposure
      -> user feedback -> reward -> LinUCB arm update
```

The reward should be assigned to the retrieval routes or cluster arms that
contributed useful evidence. Dense, BM25, and cluster-local routes can receive
credit based on whether their chunks were used, clicked, accepted, cited, or
marked useful. If user credibility is available, the update can be
reliability-weighted:

```text
A_arm += trust_user * x x^T
b_arm += trust_user * reward * x
```

This makes high-trust feedback influence the value field more strongly and
reduces the variance caused by noisy or low-trust users.

The composite reward is not the manifold feature itself. It is an observation of
the value field defined over the manifold:

```text
M       = semantic geometry from embeddings, PCA, clusters, and neighborhoods
V(x, t) = dynamic value field estimated from quality, feedback, and cost
M*      = (M, V), the dynamic value manifold
```

Thus BM25, dense, clustering, and neighborhood structure describe the geometry
`M`, while reward samples where value lies on that geometry. LinUCB uses those
samples to approximate the query-document relevance/value manifold over time.

---

## Lessons From Task 15

Task 15 tests whether the retrieval policy can self-evolve from feedback while
keeping the Task13.5 multi-route recall floor. The key result is that feedback
mostly improves the policy/value layer rather than producing a large jump in
final Recall@10.

This is expected. Global dense, BM25, and dense floor already protect the final
candidate list, so recall can stay stable even when the selected LinUCB arm is
weak. Therefore Task 15 should be interpreted through policy-level metrics:

- `last_epoch_true_reward`: whether the selected arm produces higher true
  reward after repeated interactions;
- `epoch_true_reward_gain`: whether the policy improves from early to late
  epochs;
- `last_epoch_selected_cluster_hit_rate`: whether the selected cluster arms
  increasingly contain GT evidence;
- `epoch_selected_cluster_hit_gain`: whether cluster-arm selection improves
  over time.

The primary self-evolution indicator is `last_epoch_true_reward`. It measures
the value of the arms selected by the learned policy after feedback has been
applied. Recall@k remains necessary as the downstream retrieval metric, but it
is affected by dense/BM25 fallback, fusion, and dense floor. A run can therefore
strongly validate policy self-evolution without showing a final Recall@k gain.

The current results support the self-evolution claim:

- PubMedQA: trust-weighted feedback improves `last_epoch_true_reward` to
  `0.8727` and selected-cluster gain to `+0.3950` while maintaining
  `Recall@10=0.9940`.
- Banking77 full: trust-weighted feedback reaches `last_epoch_true_reward`
  `0.9805` and selected-cluster gain `+0.0627`, while final
  `Recall@10=0.9844` is slightly below the no-feedback control `0.9855`.
  This makes Banking77 a useful example where feedback clearly improves the
  policy/value field but does not automatically improve final R@k.
- Banking77 sample: the 1000-query sample shows both policy improvement and a
  small final recall gain (`Recall@10=0.9863` versus no-feedback `0.9840`), but
  the full held-out run should anchor the main claim.
- CUAD smoke: sparse GT limits the conclusion, but trust-weighted feedback moves
  policy metrics in the positive direction.
- eManual: feedback improves policy metrics only modestly; strict chunk-id
  labels, duplicate evidence text, and underused centroid geometry remain the
  dominant failure factors.

The result strengthens the paper's central framing: the method is not a static
replacement for dense retrieval. It is a feedback-driven controller that learns
which retrieval routes and local semantic regions are valuable. Dense should
remain a fallback and safety floor, then become cost-gated once policy
confidence is high.

---

## Lessons From Task 16

Task 16 tests the engineering consequence of Task 15: if feedback makes the
LinUCB value field more reliable, can retrieval cost be reduced by routing fewer
global dense/BM25 candidates?

The conservative Task 16 gate keeps dense as an active safety channel. It does
not fully switch dense off. Instead, it uses:

- `full_multi_route`: full global dense + BM25 + cluster-local retrieval;
- `gated_cost_aware`: hybrid-lite retrieval under sufficient confidence and
  full dense fallback otherwise.

This setting validates a quality-cost trade-off:

- PubMedQA: candidate cost drops by `49.20%` with `Recall@10` moving from
  `0.9940` to `0.9893`.
- Banking77 full: candidate cost drops by `52.50%` with `Recall@10` moving
  from `0.9844` to `0.9813`.
- eManual: candidate cost drops by `28.64%`, but `Recall@10` falls from
  `0.1487` to `0.1154`.
- CUAD smoke: candidate cost drops by `32.18%`, but `Recall@10` falls from
  `0.0886` to `0.0633`.

The lesson is that cost-aware routing is feasible, but not universally safe.
For datasets where the policy/value field is reliable, dense/BM25 depth can be
reduced with modest quality loss. For sparse or evaluation-fragile datasets such
as CUAD and eManual, the system should keep a stronger full dense fallback.

This supports a staged deployment model:

```text
stage 1: full multi-route retrieval for stability
stage 2: confidence-gated dense-lite/BM25-lite routing
stage 3: LinUCB-primary retrieval only under very high confidence
stage 4: full dense fallback for low confidence, semantic drift, OOD, or negative feedback
```

Task 16 therefore strengthens the engineering-value claim: IntentWeight is not
only a way to learn retrieval policy from feedback, but also a path toward
adaptive cost control once the policy has accumulated enough reliable feedback.

---

## Task 17 Direction: LoTTE Scale-Up

Task 17 should use LoTTE as the main large-scale vertical-domain validation
target. PubMedQA and Banking77 have already been evaluated on their full
processed corpora and query sets, so they should remain full small/medium-scale
anchors rather than large-scale evidence. CUAD has a large corpus, but its sparse
GT and weak structure make it better suited to stress-test and limitation
analysis.

LoTTE is a better fit for the scale-up claim because it combines:

- domain-specific search queries;
- hundreds of thousands of corpus passages in the technology/search split;
- explicit qrels that map queries to positive evidence passages;
- enough scale to test whether dense-heavy retrieval becomes costly and whether
  confidence-gated LinUCB can preserve quality while reducing candidate depth.

The initial LoTTE technology/search sample passed the current guardrails:
`5018` corpus chunks, `20` test queries, `56` GT refs, `BM25 Recall@10=0.9000`,
`dense Recall@10=0.9000`, `hybrid Recall@10=1.0000`, LinUCB full-route
`Recall@10=1.0000`, and cost-aware gated `Recall@10=0.9500` in a one-seed,
one-epoch smoke run.

The first large-scale stage also passed the guardrails: LoTTE
technology/search with `596` full test queries and `101311` GT-anchored corpus
chunks. BM25 reached `Recall@10=0.7232`, dense reached `0.8674`, full
multi-route LinUCB reached `0.8725`, and gated cost-aware LinUCB reached
`0.8356` with average source candidate cost reduced from `300.00` to `224.16`.
This is an encouraging stage-1 signal because the method slightly exceeds the
dense baseline in full-route mode and shows a measurable quality-cost trade-off
in gated mode.

However, the 100k run also exposes a practical requirement: CPU exact dense
encoding took `1640.076s`, and the old LinUCB script repeated embedding work
instead of reusing cached embeddings. The experiment code now has a reusable
embedding cache for dense, hybrid, and cost-aware LinUCB runs. After
embedding-cache integration, the same LoTTE 100k one-seed/one-epoch LinUCB run
preserved the retrieval metrics while reducing elapsed time to `134.640s` for
full route and `266.344s` for gated route. A shared large-scale artifact runner
has now been added for dense top-depth rankings, BM25 top-depth rankings, and
PCA/context cluster artifacts. With those artifacts already on disk, the same
LoTTE 100k run preserves the retrieval metrics while reducing elapsed time
further to `7.392s` for full route and `14.080s` for gated route. Before
expanding Task 17 to the full `638509`-passage test corpus, the next engineering
concern is artifact size and full-corpus BM25/index construction, not repeated
embedding or repeated 100k ranking computation.

As of 2026-05-06, the LoTTE 100k embedding cache has been generated locally:
corpus embeddings have shape `[101311, 384]`, query embeddings have shape
`[596, 384]`, first generation took `1598.231s`, and a second cache-hit check
took `0.204s`. This removes repeated dense encoding as the next bottleneck for
LoTTE 100k and makes large-scale diagnostics practical.

The large-scale manifold diagnostics have now been run for LoTTE 100k. The
diagnostics show `pca_dim_for_90pct=182`, `pca_var@64=0.6432`,
`nearest_cluster_hit@1=0.6997`, `nearest_cluster_hit@3=0.8809`,
`nearest_cluster_hit@5=0.9413`, `dense_gt_recall@10=0.8674`, and
`context_gt_recall@10=0.7836`, giving `context_recall_retention@10=0.9033`.
This supports the claim that large-scale LoTTE has usable retrieval geometry:
the correct evidence often lies in nearby clusters, and the compressed
PCA/context space preserves most dense retrieval signal. It does not justify
removing dense retrieval entirely, because context-only recall remains below
full dense recall.

LoTTE does not provide corpus-level topic labels in the processed qrels schema.
Therefore label-alignment and local label purity are disabled for `lotte_*`
datasets instead of treating the constant `source=lotte` metadata field as a
surrogate label. The LoTTE evidence should be interpreted through geometry and
GT-routing metrics, not label-purity metrics.

This result is not yet evidence of final method superiority. It shows that the
dataset schema, GT mapping, static baselines, and LinUCB routing all work on
LoTTE. The formal Task 17 experiment should scale query count and corpus scope,
then report both retrieval quality and cost-control metrics: Recall@k, MRR@k,
nDCG@k, average source candidate cost, dense query rate, fallback rate, policy
reward evolution, and selected-cluster hit evolution.

The next research plan is to treat dense as a strong recall floor rather than an
opponent to be removed immediately. Task 18 has now tested LoTTE 100k with
`seeds=13,17,19` and `epochs=3`. Full multi-route LinUCB reaches
`Recall@10=0.8826` with std `0.0036`, above dense-only `0.8674`. Gated
cost-aware routing reaches `Recall@10=0.8440` with std `0.0107`, while reducing
average source candidate cost from `300.00` to `191.68` and lowering dense
query rate to `0.8220`. This strengthens the method-validity claim for
adaptive multi-route retrieval, but it also confirms that cost-aware gating
still needs tuning before it can be described as near-lossless.

Task 19 should map the dense/LinUCB weight and threshold ablation space to find
a quality-cost Pareto frontier. This has now been run on LoTTE 100k with five
gated configurations. The medium-cost points A/B/C remain below dense-only, but
quality-first configurations D and E exceed dense-only `Recall@10=0.8674`:
D reaches `0.8770` at average source candidate cost `229.97`, and E reaches
`0.8865` at cost `258.84`. Their reward evolution is also stronger
(`+0.3160` and `+0.3507`) than the Task18 gated reference (`+0.2931`).

The theoretical implication is important: the current method should not be
claimed as an unconditional low-cost dense replacement. Instead, it provides an
adaptive Pareto controller over dense, BM25, cluster, and LinUCB routes. When
the gating policy is conservative, dense acts as a strong recall floor and the
multi-route policy can surpass dense-only quality. When the policy is more
aggressive about low-cost routing, cost falls but recall drops. This is exactly
the expected quality-cost trade-off under the piecewise relevance-manifold
view: LinUCB learns useful route value from feedback, but dense remains the
global semantic safety channel until confidence, drift, and reward history
justify reducing it.

Task 20 has now evaluated conditional dense fallback. The routing controller
was extended to record whether fallback is caused by low confidence, high
semantic drift, or recent reward decline. The best current setting, Task20-S,
uses confidence/drift-only fallback and reaches `Recall@10=0.8747`, above
dense-only `0.8674`, while reducing dense query rate to `0.8945` and average
source candidate cost to `227.29`. Task19-D remains slightly higher in quality
(`0.8770`) but also has higher cost (`229.97`) and a higher dense query rate
(`0.9029`). Task20-S is therefore the better conditional-fallback cost point
under the `dense_query_rate < 0.90` constraint.

The reward-drop fallback trigger is useful as a safety diagnostic, but it did
not dominate in Task20. The M/H runs show that reward-drop fallback can increase
dense usage and cost without reliably improving Recall@10. The stronger
evidence is therefore confidence/drift gating: dense can be treated as a
conditional semantic safety channel, not a permanent first-stage requirement,
when the learned LinUCB route has enough confidence and stays close to the
selected semantic region.

Task 21 should convert these results into paper-ready tables and a bounded
claim. This synthesis is now captured in
`paper/experiments/task21_paper_ready_summary.md`. The paper-level conclusion is
that IntentWeight supports feedback-driven adaptive route learning and
quality-cost Pareto control under a vertical-domain piecewise relevance-manifold
view, but it should be explicitly bounded by dense fallback dependence,
dataset-specific geometry, and failure/limitation cases such as eManual and
CUAD smoke. Task 22 should only expand to full LoTTE if 100k evidence is stable
and the paper needs a stronger scale claim.

Task 22 has begun as an incremental scale-up rather than a single full-corpus
jump. The 200k LoTTE checkpoint supports the scale argument: dense-only drops to
`Recall@10=0.7970`, while full multi-route reaches `0.8300` and the
Task20-S-style gated route reaches `0.8154` at average source candidate cost
`232.01`. This suggests the adaptive multi-route advantage is not limited to the
100k subset. The next prudent checkpoint is 400k before attempting the full
`638509` corpus.

---

## One-Sentence Positioning

English:

> IntentWeight frames self-evolving RAG as online value-field learning on a domain-specific semantic manifold: dense/BM25 provide a stable recall floor, clustering exposes local semantic regions, and LinUCB with reliability-weighted feedback learns which retrieval routes are valuable and how that value should evolve over time.

Chinese:

> IntentWeight 将自进化 RAG 建模为垂类语义流形上的在线价值场学习：dense/BM25 提供稳定召回底座，聚类识别局部语义区域，LinUCB 结合可信反馈持续学习不同检索路径的价值分布和导航策略，从而推动 RAG 系统自动优化、升级，并在后续阶段具备成本自适应压缩的潜力。
