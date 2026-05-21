# IntentWeight Academic Audit Report

**Reviewer**: Independent Academic Audit (PhD Advisor Perspective)  
**Date**: 2026-05-21  
**Branch**: `review/academic-audit`  
**Scope**: Full project review covering experimental methodology, result validity, theoretical claims, and publication risks

---

## 1. Executive Summary & Verdict

### Overall Assessment

IntentWeight demonstrates **solid engineering execution** and proposes a **useful practical framework** for adaptive retrieval in vertical-domain RAG systems. However, the work has **several critical methodological issues** that must be resolved before submission to any peer-reviewed venue. The theoretical framing significantly overstates what the implementation actually delivers, and key experimental design choices introduce confounders that weaken causal claims.

### Verdict: NOT READY FOR SUBMISSION IN CURRENT STATE

**Minimum changes for a credible submission:**
1. Fix the Recall@k metric naming (critical, easy)
2. Add a static ensemble ablation to isolate LinUCB's contribution (critical, moderate)
3. Clearly frame prequential evaluation as test-time adaptation (critical, easy)
4. Add simple online baselines (epsilon-greedy, Thompson Sampling) (high, easy)
5. Tone down "manifold" language or add rigorous geometric evidence (high, moderate)

### Recommended Venue (after fixes)

| Venue Tier | Suitability | Condition |
|-----------|-------------|-----------|
| CCF-A (NeurIPS/ICML/ACL) | Low (15-25%) | Requires genuine geometric theory contribution + real user study |
| CCF-A (SIGIR) | Moderate (30-40%) | Best fit if positioned as system/engineering paper with honest scope |
| CCF-B (CIKM/ECIR/RecSys) | Good (50-60%) | Natural home for well-scoped adaptive retrieval contribution |
| SCI Q1 (IR Journal/TOIS) | Good (45-55%) | Journal format allows thorough ablation and bounded claims |
| SCI Q2 (IPM/JASIST) | High (65-75%) | Safe option with current evidence base |

---

## 2. Experimental Methodology Audit

### 2.1 CRITICAL: Recall@k Definition is Non-Standard

**File**: `paper/experiments/scripts/retrieval_metrics.py`, lines 35-39

```python
def recall_at_k(ranking: Sequence[str], ground_truth: set[str], k: int) -> float:
    """Binary Recall@k: 1 if any relevant chunk appears in top-k, else 0."""
    if not ground_truth:
        return 0.0
    return 1.0 if any(str(chunk_id) in ground_truth for chunk_id in ranking[:k]) else 0.0
```

**Issue**: This is **Binary Hit Rate@k** (also called Success@k), NOT standard Recall@k.

Standard Recall@k in IR literature (Manning et al., Introduction to Information Retrieval):
```
Recall@k = |{relevant documents in top-k}| / |{all relevant documents}|
```

The implementation returns 1.0 if ANY single relevant chunk appears in top-k, regardless of how many relevant chunks exist. For LoTTE with an average of 3.4 GT references per query (2045 refs / 596 queries), this dramatically inflates the appearance of retrieval quality.

**Impact**: When the paper reports "Recall@10 = 0.8826", this means "88.26% of queries have at least one relevant chunk in top-10". It does NOT mean "88.26% of relevant documents are retrieved". A reviewer familiar with standard IR metrics will immediately notice this discrepancy, especially since nDCG@10 = 0.6573 (much lower) suggests many relevant chunks are missed.

**Recommendation**: 
- Option A: Rename to "Success@10" or "Hit@10" throughout (honest and fast)
- Option B: Implement proper recall: `len(gt.intersection(ranking[:k])) / len(gt)` (more informative but will lower numbers)
- Option C: Report both. Binary recall is actually common in some RAG evaluation contexts, but it MUST be clearly defined.

### 2.2 MEDIUM: Zero Variance Across Seeds at Top Positions

**File**: `paper/experiments/results/linucb_cost_lotte-technology-search-100k_heldout-test_test_corpus-full_q596_prequential_metrics.json`

```json
"mrr@1_std": 0.0,
"mrr@5_std": 0.0,
"ndcg@1_std": 0.0,
"ndcg@5_std": 0.0,
"recall@10_std": 0.003625  // Only this shows variance
```

**Root Cause Analysis**: The combination of:
- `dense_weight = 2.0` (highest among all routes)
- `dense_floor_k = 5` (guarantees 5 dense results in final top-10)
- Dense ranking is deterministic (same cosine similarities regardless of seed)

This means top-5 positions are effectively determined by dense retrieval alone. LinUCB + cluster routing only affects positions 6-10, which is why only recall@10 shows variance.

**Implication**: LinUCB's learned routing has **negligible effect on the most important ranking positions (1-5)**. Its contribution is limited to the tail of the top-10. This severely undermines claims about "adaptive retrieval" improving results.

**Recommendation**: Report this finding transparently. Consider experiments with reduced dense dominance (lower dense_weight, lower dense_floor_k) to truly test LinUCB's independent contribution. Currently the system is "dense retrieval with a small cluster/BM25 bonus at the margin."

### 2.3 HIGH: Prequential Evaluation Confounds Learning with Testing

**Design**: The system runs 3 epochs over 596 held-out test queries, computing reward from GT and updating LinUCB parameters at each step.

**Problem**: This is **test-time adaptation**, not zero-shot evaluation. The "improvement" metrics (reward_gain = +0.288, epoch_hit_rate_gain = +0.007) are measured on the SAME queries the system learns from. There is no separate held-out set to validate generalization.

In standard online learning evaluation, prequential (interleaved train-test) evaluation IS a valid protocol. However:

1. The paper must CLEARLY state this is prequential evaluation, not zero-shot improvement
2. The claim "self-evolving" is misleading if the system only improves on queries it has already seen
3. With 3 epochs over 596 queries = 1788 total interactions, the system sees each query 3 times. By epoch 3, it has memorized optimal arm selections for familiar queries.

**Recommendation**:
- Add a clear "Evaluation Protocol" section explaining prequential evaluation
- Add a separate held-out set (e.g., split test queries into 400 learning + 196 held-out)
- Report both: online cumulative performance AND held-out generalization
- If generalization is weak, frame as "test-time adaptation" not "self-evolution"

### 2.4 HIGH: Dense Dominance Makes LinUCB Attribution Unclear

**Hyperparameters from the experiment**:
```
dense_weight = 2.0    (highest)
bm25_weight = 0.8
cluster_weight = 0.8
dense_floor_k = 5     (50% of top-10 guaranteed from dense)
dense_depth = 100
bm25_depth = 100
cluster_depth = 100
```

The weighted RRF fusion with these weights means dense candidates always dominate the final ranking. Combined with dense_floor_k=5, the system guarantees that dense retrieval determines most of the top-10.

**Critical Missing Ablation**: A static ensemble without LinUCB learning:
```
Ablation needed: dense(weight=2.0, depth=100) + BM25(weight=0.8, depth=100) + 
                 cluster-from-random-arms(weight=0.8, depth=100) + dense_floor_k=5
                 → same fusion, same weights, NO learning
```

If this static ensemble achieves similar Recall@10 to the full LinUCB system, then the +1.5% gain over dense-only comes from **multi-source fusion**, not from **LinUCB learning**. This is the most important ablation missing from the entire project.

The existing "hybrid baseline" (dense + BM25, RRF) uses different parameters (default weights, no floor), making it an unfair comparison point.

**Recommendation**: Run this ablation immediately. If the static ensemble matches LinUCB, reposition the paper's contribution as "multi-route fusion with adaptive route selection" rather than "online learning improves retrieval."

### 2.5 MEDIUM: Cost Comparison Framing

**Current framing**: "Gated mode reduces source candidate cost by 36% (300 -> 192)"

**Reality check**:
| Mode | Total candidates evaluated | vs Dense-only |
|------|---------------------------|---------------|
| Dense-only | 100 | baseline |
| Full multi-route | 300 | 3x dense cost |
| Gated | 192-236 | 1.9-2.4x dense cost |

The "cost saving" is relative to the inflated full multi-route baseline, not relative to the simpler dense-only system. A reviewer will ask: "Why should I pay 2x the cost of dense retrieval for +1.5% hit rate?"

**Recommendation**: 
- Report absolute candidate counts against dense-only as reference
- Frame cost reduction as "operational efficiency within the multi-route system" not as "cost saving vs. the practical alternative"
- Address: under what deployment conditions does paying 2-3x candidate computation cost for +1.5% hit rate make business sense?

### 2.6 HIGH: Simulated Feedback Does Not Validate Real-World Utility

**Current implementation** (`paper/experiments/scripts/linucb_trust_feedback.py`):
- `trust_weighted` mode: 70% high-trust users (accuracy=0.9), 30% low-trust (accuracy=0.55)
- Feedback is derived from GT: if arm contains GT chunk → true_reward = 1, else 0
- Observation noise added per user trust level

**Problems**:
1. Simulated feedback is fundamentally circular: GT defines the target, GT derives the reward, GT evaluates the result
2. Real user feedback has systematic biases not captured by random noise:
   - Position bias (users examine top results more)
   - Satisficing (users stop after first good result)
   - Domain expertise variation
   - Temporal drift in preferences
3. The "trust_weighted" mode adds noise but preserves GT-alignment. Real users may have different relevance judgments than GT annotations.

**Recommendation**:
- Clearly acknowledge this as a simulation study in limitations
- Consider at minimum: a position-biased feedback model (users only give feedback on results they actually examine)
- Future work: even a small (50-100 interaction) user pilot would dramatically strengthen claims
- The paper should NOT claim "user feedback improves retrieval" — it should claim "GT-aligned simulated feedback improves retrieval, suggesting potential for real user feedback"

---

## 3. Result Validity Audit

### 3.1 Improvement Magnitudes Are Modest But Real

| Scale | Dense Recall@10 | Full Multi-route | Absolute Gain | Relative Gain |
|-------|----------------|-----------------|---------------|---------------|
| 100k | 0.8674 | 0.8826 | +0.0152 | +1.74% |
| 200k | 0.7970 | 0.8300 | +0.0330 | +4.14% |
| 400k | 0.7718 | 0.8003 | +0.0285 | +3.69% |
| 638k | 0.7282 | 0.7612 | +0.0330 | +4.53% |

The gains increase with corpus size, which supports the claim that adaptive routing becomes more valuable when the search space is larger and dense retrieval degrades. However:

- Only 3 random seeds per experiment
- No statistical significance test (t-test, bootstrap CI)
- At 100k scale, the gain is within what might be noise for many methods
- 3 seeds give unreliable variance estimates (2 degrees of freedom)

**Recommendation**: Run at minimum 10 seeds for the main claim (LoTTE 100k and 638k), report 95% confidence intervals, and conduct paired t-tests or bootstrap hypothesis tests.

### 3.2 Scale-Up Pattern is Encouraging

The consistent pattern across 4 scales (gains increase with corpus size) is the strongest empirical argument in the paper. It suggests the method has genuine value at scale, even if individual gains are modest. This should be the primary empirical narrative.

However, all 4 scales use the SAME domain (LoTTE technology/search) with SAME queries. This is scale-up within a single domain, not generalization across domains.

### 3.3 Failure Cases Weaken the Narrative

| Dataset | Dense Recall@10 | LinUCB Full | Verdict |
|---------|----------------|-------------|---------|
| eManual | 0.3231 | 0.1487 (trust) | FAILURE: -54% |
| CUAD smoke | 0.0759 | 0.0886 | Marginal on unreliable sample |

eManual is a clear failure case where the method dramatically underperforms dense. The explanation (duplicate text, strict chunk-ID evaluation) is plausible but not fully exonerating — it shows the method is fragile to corpus properties.

**Recommendation**: Report failures prominently. Frame them as "boundary conditions" not buried footnotes. This actually strengthens credibility when honestly presented.

### 3.4 Consistent Internals (Positive)

Cross-checking result files:
- Numbers in `task23_lotte_scaleup_summary.csv` match individual JSON result files exactly
- Baseline numbers are consistent between baseline summary CSVs and LinUCB comparison tables
- GT coverage = 100% for all LoTTE runs (properly enforced by guardrails)
- No evidence of data corruption or selective reporting

---

## 4. Theoretical Claims Audit

### 4.1 "Dynamic Value Manifold" — Concept vs. Implementation Gap

**The theoretical claim** (from `paper/research-hypothesis-and-theory.md`):
```
M       = fixed semantic geometry from embeddings
V(x, t) = time-varying value field shaped by feedback
M*      = (M, V), the dynamic value manifold
```

**The actual implementation**:
```
M       = 384-dim embedding space, reduced to 64-dim via PCA, partitioned by KMeans into 32 clusters
V(x, t) = LinUCB parameters (A matrices + b vectors) for 32 arms
M*      = cluster-routing policy learned by LinUCB
```

**Gap analysis**:
- "Manifold" in mathematics means a topological space that locally resembles Euclidean space. The implementation uses a flat linear projection (PCA) + centroidal Voronoi tessellation (KMeans). There is NO topology, NO curvature, NO geodesics.
- "Value field" in the theory is a continuous function V(x,t). In implementation, it's 32 discrete arm parameters. There is no field interpolation between clusters.
- "Dynamic" means parameters update with feedback. This is true — but it's standard online learning, not "manifold dynamics."

**What reviewers will ask**:
1. "What does calling this a 'manifold' add beyond standard cluster-based routing?"
2. "Where are the geometric operations that distinguish this from KMeans + UCB?"
3. "How is 'dynamic value manifold' different from 'learned cluster selection policy'?"

**Honest answer**: The manifold framing is a useful conceptual metaphor and research direction, but the current implementation does not realize any actual manifold geometry. It implements KMeans clustering + LinUCB selection + multi-source fusion.

**Recommendation**:
- **Option A (safe)**: Remove "manifold" from the core claim. Frame as "adaptive multi-route retrieval with online cluster-routing policy." Still novel and publishable.
- **Option B (ambitious but requires work)**: Add genuine geometric evidence: intrinsic dimensionality estimation (e.g., MLE estimator), local density analysis, actual comparison to manifold learning (UMAP, t-SNE for visualization; correlation dimension for validation). Show that the embedding space IS manifold-structured and that cluster arms correspond to genuine local structure.
- **Option C (risky)**: Keep manifold language but explicitly acknowledge it as "motivating framework" rather than "geometric contribution." Risk: reviewers may see this as hand-waving.

### 4.2 Manifold Hypothesis Evidence is Insufficient

**Claimed evidence** (from manifold diagnostics):
- PCA 90% variance at dim=182 (out of 384)
- nearest_cluster_hit@3 = 0.8809
- context_recall_retention@10 = 0.9033

**Why this is insufficient**:

1. **PCA variance retention**: ANY data with structure (clusters, correlations, non-uniform distribution) will show PCA concentration. This does NOT distinguish manifold structure from simpler alternatives. A dataset of points uniformly distributed in a 200-dimensional subspace would show similar retention.

2. **Cluster hit rate**: This measures whether GT chunks fall in the same clusters as the query, which tests cluster quality (KMeans captures GT locality), not manifold structure.

3. **Missing null hypothesis**: No comparison to:
   - Random data in same dimensions (what PCA retention would you get by chance?)
   - Uniformly distributed points with same cluster structure
   - A simple k-NN baseline without any cluster machinery

4. **Missing intrinsic dimensionality**: Methods like Maximum Likelihood Estimation (Levina & Bickel, 2004) or two-nearest-neighbor estimator can estimate actual manifold dimensionality. If true intrinsic dimension ≈ PCA dimension, it's just a linear subspace, not a manifold.

### 4.3 LinUCB Modifications Not Clearly Documented

**Non-standard features in `intent_weight/linucb.py`**:

1. **Alpha decay** (line 61-68): `alpha(t) = max(alpha_min, alpha_0 / (1 + decay * total_feedback))`
   - Standard LinUCB uses fixed alpha
   - This creates a time-dependent exploration schedule
   - In the experiments, alpha reaches minimum (0.3) by convergence
   - Not mentioned in standard reference (Li et al., 2010)

2. **Multi-arm selection**: Select top-3 arms per query (vs. standard single arm per round)
   - Changes the exploration-exploitation trade-off
   - Affects regret bound analysis

3. **Weighted updates**: `policy.update(arm, context, reward, weight=w)` allows fractional updates
   - Used for cross-arm propagation
   - Changes the effective sample size interpretation

These are reasonable engineering choices, but they MUST be documented clearly in the paper with justification. A reviewer expecting standard LinUCB will flag these as undocumented deviations that may invalidate theoretical guarantees (e.g., regret bounds from Li et al.).

### 4.4 "Self-Evolving" Claim vs. Reality

**Claim**: "Self-evolving RAG system" (title-level positioning)

**Reality**:
- The system improves over 3 epochs of test-time feedback on 596 queries
- After seeing each query ~3 times with GT-derived reward, it learns better arm selections
- "Self-evolving" implies continuous autonomous improvement in deployment
- No evidence of generalization beyond the training distribution of queries

**What would genuinely support "self-evolving"**:
- Show improvement on UNSEEN queries after learning on a separate set
- Show improvement continuing beyond initial convergence (currently reaches alpha_min quickly)
- Show robustness to distribution shift (new query types after initial training)
- Show real deployment improvement over time

**Recommendation**: Replace "self-evolving" with "feedback-adaptive" or "online-learning-based" unless generalization evidence is added.

---

## 5. Comparison with Related Work

### 5.1 Missing Critical Baselines

| Missing Baseline | Why Critical | Difficulty |
|-----------------|-------------|-----------|
| **Static ensemble** (same 3 sources, same fusion, NO learning) | Isolates learning contribution from ensemble benefit | Easy - modify existing code to skip LinUCB update |
| **Epsilon-greedy over clusters** | Shows whether UCB exploration matters vs. simpler exploration | Easy - 20 lines of code |
| **Thompson Sampling over clusters** | Standard bandit comparison | Moderate - need posterior sampling |
| **Simple reranker** (e.g., cross-encoder on top-10 from dense) | Shows whether a standard reranking approach beats LinUCB routing | Moderate |
| **DynamicRAG** (actual numbers, not discussed in abstract) | The claimed main competitor | Hard - requires running their code |

The project acknowledges DynamicRAG, Online-Opt RAG, and FLAIR as comparisons but has NOT actually run any of them. The paper cannot claim superiority or complementarity without real numbers.

### 5.2 Single-Domain Scale-Up is Insufficient

All scale-up experiments use LoTTE technology/search. The other datasets serve as:
- Banking77: "intent proxy" (acknowledged as not evidence retrieval)
- PubMedQA: Near-ceiling baseline makes improvement invisible
- eManual: Failure case
- CUAD: Smoke/sample only

**For a convincing paper, need at minimum**:
- 2-3 domains where the method succeeds at scale
- 1 domain where it fails (already have eManual)
- Analysis of WHY it succeeds/fails per domain (manifold diagnostics partially address this)

### 5.3 Existing Nemesis Review (Third-Party)

The existing review (`paper/critical-third-party-review-nemesis-2026-04-21.md`) was conducted before the main experiments were completed. Its key finding ("manifold must be more than metaphor") remains UNRESOLVED in the current experimental results. The "supplementary theoretical ideas" (curvature, geodesics, metric tensor evolution) proposed in that review have NOT been implemented — they remain aspirational.

---

## 6. Publication Risk Matrix

### Critical Issues (Must Fix Before Submission)

| # | Issue | Risk if Unfixed | Fix |
|---|-------|----------------|-----|
| 1 | Binary Recall@k labeled as standard Recall@k | Immediate desk rejection or reviewer credibility loss | Rename to Success@k/Hit@k, or implement standard recall and report both |
| 2 | No static ensemble ablation | Cannot attribute gains to learning vs. fusion | Add ablation: same fusion, same weights, random arm selection instead of LinUCB |
| 3 | Prequential evaluation not clearly framed | Reviewers will flag "testing on training data" | Add clear protocol description; add held-out split experiment |
| 4 | No simple online baselines | Cannot show LinUCB > trivial alternatives | Add epsilon-greedy and Thompson Sampling |

### High-Risk Issues (Should Fix)

| # | Issue | Risk if Unfixed | Fix |
|---|-------|----------------|-----|
| 5 | "Manifold" without geometric substance | Reviewers reject as buzzword abuse | Either add intrinsic dim estimation + geometric evidence, or tone down to "structured embedding space" |
| 6 | Simulated feedback only | "Self-evolving" claim lacks real-world validation | Acknowledge clearly; add position-biased feedback model; consider small pilot |
| 7 | Dense dominance + zero variance at top-5 | Shows LinUCB doesn't affect important positions | Report transparently; test with lower dense_floor_k |
| 8 | Only 3 seeds | Statistical significance unestablished | Add seeds (10+) or bootstrap CIs |

### Medium-Risk Issues (Acknowledge in Paper)

| # | Issue | Risk | Mitigation |
|---|-------|------|-----------|
| 9 | Cost comparison framing | Misleading cost claims | Report absolute vs. dense-only |
| 10 | Single domain scale-up | Generalization unknown | Acknowledge; position as "demonstrated on one domain" |
| 11 | LinUCB modifications undocumented | Appears as hidden changes | Document alpha decay, multi-arm, weighted updates explicitly |
| 12 | eManual/CUAD failure | Weakens universal claim | Present as boundary analysis (already partially done) |

---

## 7. Positive Findings & Genuine Contributions

Despite the critical issues above, the project has real strengths:

### 7.1 Engineering Quality is Excellent
- `experiment_guardrails.py` prevents data leakage with explicit GT-corpus coverage checks
- All experiments log complete metadata (params, cache hits, coverage stats)
- Reproducibility infrastructure (embedding cache, artifact cache, scale store) is well-designed
- The `comparable_group` mechanism prevents unfair cross-setup comparisons

### 7.2 Honest Bounded Claims
The project documents its own limitations extensively:
- eManual failure is analyzed in depth (duplicate text, strict chunk-ID, centroid routing)
- CUAD is explicitly labeled as "smoke/sample only"
- The `task21_paper_ready_summary.md` has a clear "Not Supported" section
- This intellectual honesty is rare and reviewers will appreciate it

### 7.3 Scale-Up Evidence is the Strongest Argument
The consistent improvement across 100k/200k/400k/638k with increasing gains as scale grows is the most convincing empirical pattern. It suggests genuine value at operational scale even if individual gains are modest.

### 7.4 Cost-Quality Pareto Frontier is a Real Contribution
Showing that retrieval can be traded off between quality and computational cost in a principled way (via confidence-gated routing) is practically valuable. This is more defensible than "we beat dense."

### 7.5 Zero Cold-Start Design
The prior injection + immediate deployment capability (no GPU training required) is a genuine practical advantage over RL-based alternatives. This should be emphasized as a system contribution.

### 7.6 Multi-Route Fusion Architecture
The combination of dense + BM25 + cluster-local retrieval with adaptive weighting is architecturally sound and could serve as a useful framework even without the online learning component.

---

## 8. Actionable Recommendations (Priority Order)

### Immediate (Before any submission)

1. **Fix metric naming**: Change all "Recall@k" references to "Success@k" or "Hit@k" in code and documentation. Alternatively, implement proper recall alongside binary recall and report both.

2. **Add static ensemble ablation**: Same 3-source fusion with identical weights but random/fixed arm selection (no LinUCB learning). This single experiment will determine whether the paper's core contribution (online learning) is real.

3. **Add simple bandit baselines**: Epsilon-greedy (epsilon=0.1) and uniform-random arm selection, both with the same fusion architecture. 

4. **Reframe evaluation protocol**: Add a section clearly explaining prequential evaluation. Consider splitting queries 70/30 (learn on 70%, evaluate generalization on 30%).

### Short-Term (For CIKM/SIGIR submission)

5. **Reduce dense dominance experiment**: Run variant with dense_floor_k=0, dense_weight=1.0 to show LinUCB's contribution when dense doesn't dominate.

6. **Add statistical significance**: 10+ seeds, paired bootstrap test, 95% CI on key claims.

7. **Replace "manifold" with precise language**: "Structured embedding space", "cluster-organized corpus", "semantic neighborhoods." Use "manifold" only in motivation/future-work if geometric evidence is not added.

8. **Position-biased feedback ablation**: Add a feedback model where users only provide signal for the top-3 examined results (not all).

### Long-Term (For top venue)

9. **Actual geometric evidence**: Intrinsic dimensionality estimation, comparison to random/uniform null hypothesis, local density analysis.

10. **Real user pilot study**: Even 100 interactions with real users validating the simulated feedback model.

11. **Cross-domain scale-up**: Add a second domain (e.g., LoTTE science/search, or a medical corpus) at scale.

12. **Actual comparison with DynamicRAG/Online-Opt RAG**: Run their code or clearly state why comparison is impossible.

---

## 9. Conclusion

IntentWeight is an ambitious project with genuine engineering merit and a coherent research vision. The adaptive multi-route retrieval framework with cost-quality trade-off control is a real contribution. However, the current experimental evidence does not cleanly support the headline claims due to:

1. **Metric mislabeling** that inflates apparent performance
2. **Missing ablations** that would isolate the learning component's contribution
3. **Theoretical overreach** in using "manifold" terminology without geometric substance
4. **Evaluation protocol** that conflates test-time adaptation with generalization

The path to publication is clear and achievable. The work needs 2-4 weeks of additional experiments (ablations, baselines, more seeds) and a careful repositioning of claims. The honest, bounded framing already present in internal documents should be promoted to the paper's main narrative.

**Final verdict**: The research direction is sound. The implementation is high quality. The claims need to be aligned with what the evidence actually supports. This is a common and fixable gap in pre-submission manuscripts.

---

*Reviewed on branch `review/academic-audit`, 2026-05-21*
