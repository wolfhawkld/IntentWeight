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
| LoTTE science/search | 400k | evidence_retrieval | 400902 | 596 | 596 | passage_qrels | cross_domain_scale_boundary | complete_scale_boundary |
| LoTTE lifestyle/search | 100k | evidence_retrieval | pending | pending | pending | passage_qrels | deferred_hypothesis_driven_expansion | deferred_post_task69 |
| LoTTE recreation/search | 100k | evidence_retrieval | 100714 | 924 | 924 | passage_qrels | task73_external_validity_boundary | complete_task73_boundary |
| LoTTE writing/search | 100k | evidence_retrieval | 100696 | 1071 | 1071 | passage_qrels | task73_external_validity_useful_frontier | complete_task73_useful_frontier |
| PubMedQA | native full | evidence_retrieval | 4348 | 1000 | 1000 | abstract_context_section | mechanism_transfer | complete_native_full |
| CovidQA-RAG | native full | evidence_retrieval | 32392 | 1765 | 1726 | ragbench_relevant_sentence_keys | biomedical_discriminative_transfer | complete_native_full |
| eManual deduplicated | native full | evidence_retrieval | 1729 | 132 | 130 | text_equivalent_after_deduplication | corrected_boundary | complete_corrected_boundary |
| CUAD GT-anchored sample | 10k sample | evidence_retrieval | 10000 | 2550 | 79 | sparse_contract_evidence_anchors | sparse_gt_boundary | boundary_not_poolable |
| Banking77 | native full | intent_retrieval_proxy | 10003 | 3080 | 3080 | same_intent_exemplar | feedback_route_learning | mechanism_not_poolable |

## Evidence Coverage Matrix

| Dataset | Scale | BM25 | Dense | Hybrid | Route | Geometry | OOF budget | Tokens | Paired | Feedback | Recovery | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LoTTE technology/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE science/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE science/search | 200k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE science/search | 400k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE lifestyle/search | 100k | no | no | no | no | no | no | no | no | no | no | 0/10 |
| LoTTE recreation/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| LoTTE writing/search | 100k | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| PubMedQA | native full | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| CovidQA-RAG | native full | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
| eManual deduplicated | native full | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | 10/10 |
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
| LoTTE recreation/search | 100k | 0.8496 | 0.8420 | -0.76 | 5.42 | 0/3 | -- | complete Task73 external-validity boundary |
| LoTTE writing/search | 100k | 0.8739 | 0.8752 | 0.12 | 10.09 | 2/3 | -- | complete Task73 useful-frontier row |
| LoTTE science/search | 100k | 0.8926 | 0.8915 | -0.11 | 16.88 | 0/3 | -- | reusable complete cross-domain row |
| LoTTE science/search | 200k | 0.8574 | 0.8507 | -0.67 | 10.75 | 0/3 | -- | reusable complete cross-domain scale row |
| LoTTE science/search | 400k | 0.8238 | 0.8171 | -0.67 | 3.15 | 0/3 | -- | complete boundary; recovery has 3-6 affected queries/seed |
| PubMedQA | native full | 0.9930 | 0.9930 | 0.00 | 0.00 | 3/3 | -- | complete native-full transfer row |
| CovidQA-RAG | native full | 0.6095 | 0.6074 | -0.21 | 8.34 | 0/3 | -- | complete native-full discriminative transfer row |
| Banking77 | native full | 0.9805 | 0.9844 | 0.39 | -- | -- | 0.9983 | mechanism/boundary only |
| CUAD GT-anchored | 10k sample | 0.0759 | 0.0886 | 1.27 | -- | -- | 0.2900 | mechanism/boundary only |
| eManual deduplicated | native full | 0.8615 | 0.8590 | -0.26 | 16.20 | 0/3 | -- | complete corrected-boundary row |

## Missing Experiment Batches

| Priority | Dataset | Scale | Missing endpoints | Action |
|---|---|---|---|---|

## Interpretation Guardrail

LoTTE technology/search, LoTTE science/search 100k/200k/400k, PubMedQA native full, CovidQA-RAG native full, and corrected eManual native full provide complete rows under the common endpoint set. Science/search 400k is a weak boundary row: only one of five folds is budget eligible, its OOF mean Hit@10 delta is -0.67pp with 3.15% saving, and recovery has only 3-6 affected queries per seed. Task73 adds complete recreation/search and writing/search 100k rows without pooling them: recreation is a weaker no-feedback boundary, writing provides a useful no-feedback frontier, and trust-weighted calibration falls back in both. Lifestyle remains a deferred post-Task69 candidate rather than a missing endpoint. Technology reuses verified Task38/65 artifacts; science uses Task69.3 standalone baselines and frozen budget evaluation; PubMedQA is a native-full transfer row whose selector safely falls back to Dense; CovidQA-RAG is a more discriminative biomedical transfer row; eManual is a corrected-boundary row on the deduplicated text corpus. Banking77 remains an intent-routing mechanism test, and CUAD remains a sparse-GT boundary case.
