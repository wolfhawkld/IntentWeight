# Task73 Hypothesis-Driven LoTTE Domain Expansion

Completed: 2026-07-15

## Objective And Frozen Design

Task73 tests whether IntentRoute's bounded quality-context frontier is stable
across two preregistered LoTTE search domains. Recreation/search and
writing/search were selected before downloading or inspecting their outcomes.
Both use the Task69 common protocol: GT-anchored 100k corpora, all positive-qrel
test queries, MiniLM, top-10, K=32, seeds 13/17/19, eight no-leakage
prequential epochs, matched trust/no-feedback controls, the locked five-fold
budget grid, `cl100k_base`, and paired query-level statistics. Results are not
pooled across domains.

The source dataset is `mteb/LoTTE` at Hugging Face revision
`a9006514d20ec3353082b4272bf46a20dd96a195`. Exact processed corpus/query SHA-256
values are stored in the machine-readable Task73 audit.

The local AMD Radeon RX 9070 XT generated the canonical MiniLM embeddings.
Retrieval, routing, calibration, and statistics reused those fingerprint-bound
artifacts. Hardware is not an experimental factor and no runtime claim is made.

## Dataset And Baseline Results

| Domain | Corpus | Queries | GT refs | BM25 Hit@10 | Dense Hit@10 | Hybrid Hit@10 |
|---|---:|---:|---:|---:|---:|---:|
| recreation/search | 100,714 | 924 | 1,991 | 0.6937 | 0.8496 | 0.8171 |
| writing/search | 100,696 | 1,071 | 3,546 | 0.7283 | 0.8739 | 0.8758 |

All corpus/query IDs are unique and every positive-qrel chunk is present. The
realized corpora exceed 100,000 only because GT anchoring retains positives
encountered beyond the first 100,000 distractors.

## Preregistered Domain-Property Check

The H1 premise that recreation would be the relatively more lexical condition
is not supported. It is directionally reversed:

| Metric | recreation | writing | recreation-writing | 95% bootstrap CI |
|---|---:|---:|---:|---:|
| Max query-token coverage in a positive chunk | 0.6755 | 0.7478 | -0.0722 | [-0.0901, -0.0543] |
| Max query-positive Jaccard | 0.0787 | 0.1003 | -0.0216 | [-0.0268, -0.0165] |
| BM25 minus Dense Hit@10 | -15.58pp | -14.57pp | -1.02pp | [-4.90pp, +2.83pp] |

The two selected domains are retained exactly as preregistered. Their frontier
difference cannot be attributed to the originally assumed lexicality ordering.

## Route And Cross-Fitted Budget Results

| Domain | Feedback | Fixed top-10 route Hit@10 | Eligible folds | OOF Hit delta vs Dense | Token saving | Strict 1pp NI |
|---|---|---:|---:|---:|---:|---:|
| recreation/search | trust-weighted gated | 0.8395 | 0/5 | +0.00pp | 0.00% | n/a, Dense fallback |
| recreation/search | no feedback | 0.8546 | 4/5 | -0.76pp | 5.42% | 0/3 |
| writing/search | trust-weighted gated | 0.8677 | 0/5 | +0.00pp | 0.00% | n/a, Dense fallback |
| writing/search | no feedback | 0.8842 | 5/5 | +0.12pp | 10.09% | 2/3 |

Trust-weighted full-route Hit@10 is 0.8597 on recreation and 0.8842 on
writing. Its gated route loses fixed-top-10 quality relative to no feedback,
and the independent calibration gate therefore selects Dense fallback in all
folds. This is safe execution, not evidence of a token-saving operating point.

Writing/no-feedback is the positive Task73 frontier: all folds select a budget,
mean Hit changes by +0.12pp while final-context tokens fall by 10.09%, and two
of three seed-level bootstrap intervals satisfy the strict 1pp rule. Seed 19
does not, so Task73 does not establish universal strict non-inferiority.
Recreation/no-feedback is a weaker boundary: one fold falls back, mean Hit falls
0.76pp, and no seed satisfies the strict CI rule.

## Geometry And Feedback Recovery

| Domain | PCA dim 90% | Nearest-cluster hit@3 | Context recall@10 | Compression-only failures | Arm boost recovered | Conservative recovered |
|---|---:|---:|---:|---:|---:|---:|
| recreation/search | 196 | 0.8366 | 0.7316 | 40 | 12 | 12 |
| writing/search | 202 | 0.8655 | 0.7666 | 29 | 28 | 29 |

The recovery counts aggregate the three seeds and isolate `fixed route hit ->
budgeted miss`; they do not mix route substitution failures with compression
failures. On all queries, same-query arm feedback raises Hit by 0.14pp on
recreation while retaining 5.35% saving, and by 0.40pp on writing while
retaining 10.09% saving. This is simulated post-failure retry evidence, not
first-pass unseen-query generalization.

## Scientific Conclusion

1. H1's assumed lexical ordering is rejected; no mechanism claim relies on it.
2. H2 is supported as a descriptive heterogeneity result: writing admits a
   useful frontier, recreation is a weaker boundary, and Dense fallback is a
   legitimate outcome.
3. H3 does not support a global trust-weighted feedback advantage. Feedback is
   retained as repeated-query adaptation and domain-dependent recovery, not as
   the source of compression safety.

Task73 therefore strengthens the bounded external-validity account without
raising the claim to universal savings or universal non-inferiority. Geometry,
feedback, and independent budgeting remain distinct parts of the evidence
chain.

## Artifacts And Audit

- Generated summary: `results/task73_lotte_domain_expansion.{json,csv,md}`
- Baselines: `results/task73_{recreation,writing}_100k_{bm25,dense,hybrid}/`
- Routes: `results/task73_{recreation,writing}_100k_{trust,none}/`
- Budgets: `results/task73_{recreation,writing}_100k_{trust,none}_cross_fitted_budget.*`
- Geometry and recovery: Task73 domain-scoped result artifacts
- Generator: `scripts/task73_domain_expansion_summary.py`

The final audit passes 104 checks covering data/GT integrity, baseline and route
protocols, query/top-10 ranking integrity, checkpoint v2 fresh execution,
embedding and artifact fingerprints, five-fold calibration, geometry, and
cross-fitted recovery. The JSON summary records input and result checksums.
