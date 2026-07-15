# Task73 LoTTE Domain Expansion Results

## Protocol

Two preregistered LoTTE search domains use the frozen Task69 common protocol: GT-anchored 100k corpora, all positive-qrel queries, MiniLM, top-10, K=32, seeds 13/17/19, eight prequential epochs, matched feedback/no-feedback controls, and five-fold cross-fitted context budgets. Domains are reported separately; no pooled p-value is used.

## Domain Property Check

| Domain | Corpus | Queries | Query-positive coverage | Jaccard | BM25 Hit@10 | Dense Hit@10 | BM25-Dense |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoTTE recreation/search | 100,714 | 924 | 0.6755 | 0.0787 | 0.6937 | 0.8496 | -15.58pp |
| LoTTE writing/search | 100,696 | 1,071 | 0.7478 | 0.1003 | 0.7283 | 0.8739 | -14.57pp |

The preregistered H1 characterization is not supported and is directionally reversed: writing has higher query-positive lexical overlap and a slightly smaller Dense advantage. Recreation-minus-writing differences are -0.0722 (95% CI -0.0901 to -0.0543) for coverage, -0.0216 (95% CI -0.0268 to -0.0165) for Jaccard, and -1.02pp (95% CI -4.90 to +2.83) for BM25-relative Hit. The domains are retained as preregistered; their frontier contrast cannot be attributed to the originally assumed lexicality ordering.

## Retrieval And Budget Results

| Domain | Dense | Hybrid | Trust full | Trust gated | No-feedback route | Feedback | Eligible folds | Hit delta | Token saving | Strict 1pp NI |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| LoTTE recreation/search | 0.8496 | 0.8171 | 0.8597 | 0.8395 | 0.8546 | trust | 0/5 | +0.00pp | 0.00% | n/a (fallback) |
| LoTTE recreation/search | 0.8496 | 0.8171 | 0.8597 | 0.8395 | 0.8546 | none | 4/5 | -0.76pp | 5.42% | 0/3 |
| LoTTE writing/search | 0.8739 | 0.8758 | 0.8842 | 0.8677 | 0.8842 | trust | 0/5 | +0.00pp | 0.00% | n/a (fallback) |
| LoTTE writing/search | 0.8739 | 0.8758 | 0.8842 | 0.8677 | 0.8842 | none | 5/5 | +0.12pp | 10.09% | 2/3 |

Trust-weighted gated routing triggers Dense fallback in all five folds for both domains. The no-feedback frontier is domain-dependent: recreation selects compression in four folds but does not establish seed-level non-inferiority; writing selects compression in all five folds, averages a +0.12pp Hit change with 10.09% token saving, and passes the strict CI rule for two of three seeds. This is useful heterogeneity evidence, not universal strict non-inferiority.

## Geometry And Recovery

| Domain | PCA dim 90% | Nearest cluster hit@3 | Context recall@10 | Compression-only failures | Arm-boost recovered | Conservative recovered | All-query retry Hit gain | Saving after arm boost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LoTTE recreation/search | 196 | 0.8366 | 0.7316 | 40 | 12 | 12 | +0.14pp | 5.35% |
| LoTTE writing/search | 202 | 0.8655 | 0.7666 | 29 | 28 | 29 | +0.40pp | 10.09% |

Both domains expose substantial static nearest-cluster signal, but this does not guarantee a calibrated compression point. Post-failure arm-level retry is also heterogeneous: it is weak on recreation and strong on writing. Recovery is same-query simulated-feedback evidence after an observed failure, not first-pass unseen-query performance.

## Hypothesis Outcomes

- H1 (recreation is the more lexical condition): not supported; the observed contrast is reversed.
- H2 (domain-dependent bounded frontier): supported descriptively. Writing admits the stronger no-feedback operating point; recreation is a weaker boundary; trust-weighted calibration safely falls back in both.
- H3 (global feedback advantage): not supported. Trust-weighted prequential feedback does not improve the calibrated frontier here, while post-failure feedback remains a domain-dependent recovery mechanism.

## Claim Boundary

Task73 strengthens the paper's bounded external-validity account but does not add a universal positive replication. Geometry can provide route signal, feedback can support repeated-query recovery, and independent calibration can expose a useful context frontier; none of these guarantees savings in every domain or seed. Dense fallback remains a substantive safety outcome rather than a hidden failure.

## Audit

All 104 protocol, coverage, ranking-integrity, fingerprint, checkpoint, calibration, geometry, and recovery checks passed. Input and result checksums are recorded in the JSON artifact.
