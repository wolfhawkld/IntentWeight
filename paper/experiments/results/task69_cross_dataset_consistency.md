# Task69 Cross-Dataset Consistency Audit

Generated from `task69_common_protocol.json` and traceable result artifacts.

## Frozen Common Protocol

- primary task: `evidence_retrieval`;
- top-k: `10`; encoder: `sentence-transformers/all-MiniLM-L6-v2`;
- route seeds: `[13, 17, 19]`; clusters: `32`;
- route evaluation: `eight_epoch_no_leakage_prequential_trajectory`;
- adaptation endpoint: `8` epochs with the non-IID boundary disclosed;
- context budget: `five_fold_cross_fitted` with `zero_observed_hit_drop_then_max_token_saving`;
- Banking77 and CUAD are not pooled into the common evidence-retrieval conclusion.

## Dataset And Protocol Inventory

| Dataset | Scale | Task | Corpus | Queries | Current eval | GT semantics | Role | Status |
|---|---|---|---|---|---|---|---|---|
| LoTTE technology/search | 100k | evidence_retrieval | 101311 | 596 | 417 | passage_qrels | full_stack_anchor | complete_reusable_anchor |
| LoTTE science/search | 100k | evidence_retrieval | 101187 | 596 | 596 | passage_qrels | cross_domain | complete_reusable_anchor |
| LoTTE science/search | 200k | evidence_retrieval | 201098 | 596 | 596 | passage_qrels | cross_domain_scale | complete_reusable_anchor |
| LoTTE lifestyle/search | 100k | evidence_retrieval | pending | pending | pending | passage_qrels | planned_cross_domain | planned |
| LoTTE recreation/search | 100k | evidence_retrieval | pending | pending | pending | passage_qrels | planned_cross_domain | planned |
| LoTTE writing/search | 100k | evidence_retrieval | pending | pending | pending | passage_qrels | planned_cross_domain | planned |
| PubMedQA | native full | evidence_retrieval | 4348 | 1000 | 1000 | abstract_context_section | mechanism_transfer | partial_common_protocol |
| eManual deduplicated | native full | evidence_retrieval | 1729 | 132 | 130 | text_equivalent_after_deduplication | corrected_boundary | partial_common_protocol |
| CUAD GT-anchored sample | 10k sample | evidence_retrieval | 10000 | 2550 | 79 | sparse_contract_evidence_anchors | sparse_gt_boundary | boundary_not_poolable |
| Banking77 | native full | intent_retrieval_proxy | 10003 | 3080 | 3080 | same_intent_exemplar | feedback_route_learning | mechanism_not_poolable |

## Evidence Coverage Matrix

| Dataset | Scale | BM25 | Dense | Hybrid | Route | Geometry | OOF budget | Tokens | Paired | Feedback | Recovery | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LoTTE technology/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE science/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE science/search | 200k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE lifestyle/search | 100k | no | no | no | no | no | no | no | no | no | no | 0/10 |
| LoTTE recreation/search | 100k | no | no | no | no | no | no | no | no | no | no | 0/10 |
| LoTTE writing/search | 100k | no | no | no | no | no | no | no | no | no | no | 0/10 |
| PubMedQA | native full | yes | yes | yes | yes | yes | no | no | no | yes | no | 6/10 |
| eManual deduplicated | native full | yes | yes | yes | no | yes | no | no | no | no | no | 4/10 |
| CUAD GT-anchored sample | 10k sample | yes | yes | yes | yes | yes | no | no | no | yes | no | 6/10 |
| Banking77 | native full | yes | yes | yes | yes | yes | no | no | no | yes | no | 6/10 |

## Current Result Snapshot

Rows below are intentionally not pooled. `--` means the current artifact does not contain that common-protocol endpoint.

| Dataset | Scale | Dense Hit@10 | Route Hit@10 | Delta pp | Token saving | NI seeds | Feedback route metric | Artifact status |
|---|---|---|---|---|---|---|---|---|
| LoTTE technology/search | 100k | 0.8674 | 0.8568 | -1.06 | 4.16 | 0/3 | -- | reusable complete anchor |
| LoTTE technology/search | 200k | 0.7970 | 0.8110 | 1.40 | 16.07 | 2/3 | -- | reusable complete anchor |
| LoTTE technology/search | 400k | 0.7718 | 0.7718 | 0.00 | 14.50 | 0/3 | -- | reusable complete anchor |
| LoTTE technology/search | 638k full | 0.7282 | 0.7310 | 0.28 | 15.23 | 0/3 | -- | reusable complete anchor |
| LoTTE science/search | 20k/q200 | 0.8929 | 0.9095 | 1.67 | 13.80 | 1/3 | -- | legacy fixed-split diagnostic |
| LoTTE science/search | 100k | 0.8926 | 0.8915 | -0.11 | 16.88 | 0/3 | -- | reusable complete cross-domain row |
| LoTTE science/search | 200k | 0.8574 | 0.8507 | -0.67 | 10.75 | 0/3 | -- | reusable complete cross-domain scale row |
| PubMedQA | native full | 0.9930 | 0.9940 | 0.10 | -- | -- | 0.8860 | mechanism/boundary only |
| Banking77 | native full | 0.9805 | 0.9844 | 0.39 | -- | -- | 0.9983 | mechanism/boundary only |
| CUAD GT-anchored | 10k sample | 0.0759 | 0.0886 | 1.27 | -- | -- | 0.2900 | mechanism/boundary only |
| eManual deduplicated | native full | 0.8615 | -- | -- | -- | -- | -- | partial; corrected Dense only |

## Missing Experiment Batches

| Priority | Dataset | Scale | Missing endpoints | Action |
|---|---|---|---|---|
| P1 | LoTTE lifestyle/search | 100k | bm25, dense, hybrid_rrf, intentroute_top10, geometry, cross_fitted_budget, final_context_tokens, paired_statistics, feedback_control, feedback_recovery | run common protocol |
| P1 | LoTTE recreation/search | 100k | bm25, dense, hybrid_rrf, intentroute_top10, geometry, cross_fitted_budget, final_context_tokens, paired_statistics, feedback_control, feedback_recovery | run common protocol |
| P1 | LoTTE writing/search | 100k | bm25, dense, hybrid_rrf, intentroute_top10, geometry, cross_fitted_budget, final_context_tokens, paired_statistics, feedback_control, feedback_recovery | run common protocol |
| P1 | PubMedQA | native full | cross_fitted_budget, final_context_tokens, paired_statistics, feedback_recovery | complete missing common-protocol stages |
| P1 | eManual deduplicated | native full | intentroute_top10, cross_fitted_budget, final_context_tokens, paired_statistics, feedback_control, feedback_recovery | complete missing common-protocol stages |

## Interpretation Guardrail

LoTTE technology/search and science/search 100k/200k now provide complete reusable rows under the common endpoint set. Technology reuses verified Task38/65 artifacts; science uses the Task69.3 standalone baselines, matched feedback control, and five-fold cross-fitted budget results. PubMedQA and corrected eManual can join the common table only after their missing token-budget and paired endpoints are run. Banking77 remains an intent-routing mechanism test, and CUAD remains a sparse-GT boundary case.
