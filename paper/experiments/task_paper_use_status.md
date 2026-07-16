# Task Paper-Use Status

Updated: 2026-07-16

This file marks which internal task summaries should be used when writing the
paper. It prevents historical or superseded experiment notes from being
accidentally promoted into paper-facing claims.

## Status Labels

- **Main evidence**: can support main paper claims.
- **Supporting evidence**: can support ablations, robustness, protocol defense,
  or boundary discussion.
- **Boundary/negative evidence**: useful because it limits overclaiming; do not
  present as positive main evidence.
- **Historical/superseded**: kept for provenance only; do not cite as current
  evidence unless the newer correction is also cited.
- **Internal handoff/backlog**: not paper evidence.

## Main Evidence

| File | Status | Use in paper |
|---|---|---|
| `task38_calibrated_context_budget_validation.md` | Main evidence | Calibrated/frozen token-budget validation on LoTTE technology/search; use for the main token-quality frontier. |
| `task39_lotte_cross_domain_validation.md` | Main/supporting evidence | LoTTE science/search cross-domain validation at 20k/q200 and 100k; use for ranking transfer and compression-calibration boundary. |
| `task29_2_token_quality_frontier.md` | Main evidence | Main token-quality frontier for the conservative confidence-based context policy. |
| `task29_confidence_context_policy_summary.md` | Main evidence | Defines the final context compaction policy and its LoTTE scale-up results. |
| `task30_lotte_geometry_scale_validation.md` | Main evidence | LoTTE technology/search geometry diagnostics supporting the piecewise relevance-manifold framing. |
| `task43_lotte_science_geometry_diagnostics.md` | Main/supporting evidence | LoTTE science/search geometry diagnostics; use together with Task39 to show the second-domain geometry signal and calibration boundary. |
| `task31_paper_evidence_package.md` | Main evidence package | Aggregated evidence source; use together with the later consistency audit and full draft. |
| `task33_3_clean_ablation_table.md` | Main/supporting evidence | Clean LoTTE 100k ablation table for dense floor, feedback, trust weighting, and final policy. |
| `task33_6_additional_seeds_summary.md` | Supporting evidence | Five-seed stability check for LoTTE 100k; do not claim statistical superiority. |
| `task69_3_science_100k_checkpoint_summary.md` | Main/supporting cross-domain evidence | Common-protocol LoTTE science/search 100k baselines, matched feedback control, and five-fold context-budget result; report the `-0.11pp` Hit delta and `16.88%` saving together with `0/3` strict NI and the EvidenceRecall boundary. |
| `task69_3_science_200k_checkpoint_summary.md` | Main/supporting cross-domain evidence | Common-protocol LoTTE science/search 200k scale extension; report the `-0.67pp` Hit delta and `10.75%` saving together with `0/3` strict NI and the EvidenceRecall boundary. |
| `task70_formal_frozen_policy_summary.md` | Boundary evidence | Formal frozen unseen-query results for technology/search 100k and science/search 100k, including paired inference and the feedback-transfer boundary. | Use to bound feedback to repeated-query adaptation/hard-case recovery; do not claim a first-pass learned-feedback advantage on unseen queries. |
| `task73_lotte_domain_expansion_summary.md` | Main/supporting external-validity evidence | Predeclared recreation/search and writing/search 100k common-protocol study. Report writing's `+0.12pp`/`10.09%` useful frontier and recreation's `-0.76pp`/`5.42%` boundary together with strict NI (`2/3` and `0/3`), trust-weighted Dense fallback, and the reversed lexicality premise. Do not pool domains or attribute compression directly to geometry. |

## Supporting Evidence

| File | Status | Use in paper |
|---|---|---|
| `task24_audit_fixes_summary.md` | Supporting evidence | Audit fixes, naming corrections, and guardrails. |
| `task25_credit_assignment_summary.md` | Supporting evidence | Route-level credit assignment and LinUCB self-evolution evidence. Cost columns are source-candidate proxies only. |
| `task28_1_context_token_backfill_summary.md` | Supporting guardrail | Backfilled final context token correction for historical runs. |
| `task28_context_token_cost_summary.md` | Supporting guardrail | Shows candidate-cost savings did not imply final context token savings under fixed top-10. |
| `task33_1_embedding_model_selection.md` | Supporting rationale | Explains CPU-friendly embedding model choice. |
| `task33_1a_multiqa_minilm_robustness_summary.md` | Supporting evidence | Same-resource-class encoder robustness check. |
| `task33_2_feedback_sensitivity_summary.md` | Supporting evidence | Feedback-noise sensitivity and trust-weighting behavior. |
| `task33_4_protocol_defense.md` | Supporting defense | Prequential simulated-feedback protocol defense. |
| `task33_5_llm_generation_smoke_summary.md` | Supporting sanity check | Small downstream generation smoke test; not a full human evaluation. |
| `task33_7_pre_writing_consistency_audit.md` | Supporting guardrail | Pre-writing claim consistency audit. |
| `task34_review_defense_revision_plan.md` | Supporting guardrail | Review-defense revision checklist incorporated into the draft. |
| `task40_feedback_recovery_summary.md` | Supporting evidence | Hard-case feedback recovery on LoTTE technology/search and science/search 100k; use as post-feedback repair evidence, not as first-pass IID improvement. |
| `task47_cross_encoder_reranker_summary.md` | Supporting/strong reranker baseline evidence | Cross-encoder reranking over dense top-50 improves support metrics at full top-10 but increases context tokens; same-budget reranking does not uniformly dominate IntentRoute. |
| `task48_compressor_normalized_summary.md` | Supporting/strong baseline evidence | Applies the same SentMMR compressor to dense and IntentRoute evidence pools; use to support the route-and-budget controller plus shared-compressor framing. |
| `task52_strong_embedding_baseline_summary.md` | Supporting/strong embedding baseline evidence | BGE-base dense raises the dense quality floor on Task38 held-out LoTTE 100k while increasing context tokens; use to tighten claims and motivate rerunning IntentRoute with a stronger dense branch. |
| `task53_embedding_backbone_generalization_summary.md` | Supporting/backbone robustness evidence | Matched-backbone MiniLM/BGE/E5 comparison; use full multi-route rows as quality-preserving token-saving evidence and gated rows as cost-aggressive boundary evidence. |
| `task54_positive_hit_tradeoff_summary.md` | Supporting/tunability evidence | BGE quality-first operating point: slightly above BGE dense Hit@10 while still saving final context tokens; note that E5 does not currently show the same positive-Hit point. |
| `task55_backbone_stability_summary.md` | Supporting/stability evidence | Fixed-seed stability check for MiniLM/BGE/E5 matched-backbone results; use to show the claims are statistically checkable without presenting seeds as tuning targets. |
| `task58_geometry_random_ablation_summary.md` | Supporting/boundary geometry-control evidence | Static-nearest versus uniform-random cluster-arm control under the same budget protocol; use to show geometry appears in route-control metrics while dense/BM25 rescue masks final Hit@10. |
| `task59_feedback_control_ablation_summary.md` | Supporting/boundary feedback-control evidence | Learned LinUCB versus static-nearest, no-feedback, and random controls; use to show feedback improves route quality over no-feedback/random but does not by itself explain final fused Hit@10. |
| `task72_1_cluster_credit_ablation_summary.md` | Supporting/boundary feedback mechanism evidence | Cluster-only credit-alignment ablation on fixed recurrent streams. Oracle feedback verifies route-learning capacity; noisy/trust-weighted gains over cold are conditional and static geometry remains stronger. Always pair with the Task72 full-fusion boundary. |
| `task60_arm_count_sensitivity_summary.md` | Supporting/design-sensitivity evidence | KMeans arm-count grid over K={8,16,32,64,128}; use to defend n_clusters as a reproducible engineering parameter and to show full multi-route robustness plus gated-routing sensitivity. |
| `task61_geometry_to_control_analysis.md` | Supporting/diagnostic synthesis evidence | Geometry-to-control correlation analysis across Task30/43/58/60 and Figure 3; use to show geometry is an explanatory route-control signal, not proof that geometry alone determines final Hit@10 or token saving. |
| `task62_prompt_compression_baseline_summary.md` | Supporting/strong prompt-compression baseline evidence | Selective Context-style prompt-pruning baseline with tiktoken/cl100k_base accounting; use to show prompt compression is a strong downstream layer that can be stacked with IntentRoute rather than replaced by it. |
| `task63_downstream_llm_evaluation_summary.md` | Supporting/downstream evidence | Frozen 300-query, 2,100-answer evaluation; use for lower-context answer-quality support without claiming significant correctness improvement. |
| `task64_manuscript_claim_reframe_summary.md` | Supporting writing revision | Historical reframe task; the current manuscript further separates confidence-gated route control from independently calibrated final-context budgeting. |
| `task65_table_figure_refresh_summary.md` | Supporting writing revision | Defines the five-table, three-figure main display set and journal-facing evidence hierarchy. |
| `task65_1_safe_compression_attribution_summary.md` | Boundary/mechanism evidence | Matched selector audit showing that learned confidence and geometry do not currently outperform random controls for per-query safe-compression discrimination; use to separate confidence-gated routing from the calibrated length budget. |
| `task65_2_factorial_safe_compression_summary.md` | Boundary/mechanism evidence | Fixed-dense-pool geometry/random-partition by feedback/no-feedback audit; confirms strong route-quality differences but no stable per-query safe-compression identification advantage. |
| `task65_3_dynamic_route_mediation_summary.md` | Mechanism and boundary evidence | Frozen-trajectory replay shows that correct confidence-tier assignment materially protects route quality versus shuffled or unconditional cluster-primary routing, while confidence remains unrelated to compression headroom. |
| `task65_4_matched_frontier_summary.md` | Main/supporting calibration evidence | Independent Dense and IntentRoute action selection on a common fine grid; supports a nonzero conservative IntentRoute point under the pre-specified zero-drop calibration rule without claiming strict NI or Pareto dominance. |
| `task65_5_calibration_split_sensitivity_summary.md` | Supporting/boundary calibration evidence | Twenty overlapping query partitions per scale strengthen 200k/638k stability while exposing moderate 100k and mixed 400k split sensitivity. |
| `task65_6_cross_scale_cross_fitted_calibration_summary.md` | Supporting/cross-fitted calibration evidence | Five disjoint canonical-query folds under an identical four-scale protocol close the 400k follow-up with 14.50% mean saving and no mean Hit change, while retaining policy instability and 0/3 strict NI. |
| `task65_7_multi_judge_analysis_summary.md` | Supporting/multi-judge answer evidence | Reuses the fixed 2,100 answers with DeepSeek, GLM-5.2, and MiniMax-M3 judges; use for shared-key agreement, judge-specific paired correctness, mixed faithfulness effects, and the explicit 35-judgment content-filtering gap. |
| `task36_1_geometry_formula_definitions.md` | Supporting writing revision | Paper-facing geometry diagnostic formulas; no new experiment. |
| `task36_2_secondary_dataset_evidence.md` | Supporting writing revision | Integrates PubMedQA, Banking77, eManual, and CUAD as supporting/boundary evidence; no new experiment. |
| `task36_3_related_work_citation_framework.md` | Supporting writing revision | Adds a paper-facing related-work structure, provisional citation keys, and reference seed list; no new experiment. |
| `task36_4_table_figure_placement_plan.md` | Supporting writing revision | Defines which tables and figures belong in the main paper versus appendix; no new experiment. |
| `task36_5_main_text_table_alignment.md` | Supporting writing revision | Aligns draft table captions and appendix-facing notes with the table/figure placement plan; no new experiment. |
| `task36_6_main_figure_assets.md` | Supporting writing revision | Adds regenerable draft assets for the system diagram, token-quality frontier, and geometry diagnostic trend; no new experiment. |
| `task36_7_bibtex_normalization.md` | Supporting writing revision | Converts the reference seed list into a provisional `references.bib` and checks citation-key coverage; no new experiment. |
| `task36_8_appendix_draft.md` | Supporting writing revision | Adds a paper-facing appendix draft for stability, baseline, cost-guardrail, boundary-case, encoder, and generation-smoke evidence; no new experiment. |
| `task36_9_full_draft_consistency_audit.md` | Supporting writing revision | Adds an automated manuscript/BibTeX audit and tightens the broad evidence-selection framing to avoid manifold and RAG overclaiming; no new experiment. |
| `task36_10_review_packet.md` | Supporting writing revision | Adds a regenerable venue-neutral independent-review packet with manuscript, references, figure index, checklist, validation report, and file manifest; no new experiment. |
| `task36_11_literature_gap_expansion.md` | Supporting writing revision | Adds direct adaptive-retrieval, bandit-routing, and context-compression prior art; explicitly distinguishes IntentRoute from MBA-RAG and avoids first-use overclaiming; no new experiment. |
| `task69_cross_dataset_consistency_plan.md` | Supporting protocol guardrail | Defines the cross-dataset common endpoint set, separates evidence retrieval from intent-routing and sparse-GT boundary evidence, and records deferred post-Task69 expansion candidates. |
| `task74_task73_manuscript_integration_plan.md` | Supporting writing revision | Defines the source-derived Task73 integration boundary, benchmark-count update, and submission-validation gate; no new experiment. |
| `task74_task73_manuscript_integration_summary.md` | Supporting writing revision | Records the completed Task73 manuscript integration, source-derived S30 table, synchronized packages, and final author-owned submission items; no new experiment. |
| `task75_final_text_and_literature_summary.md` | Supporting writing revision | Records the final terminology, cost-scope, feedback-framing, 2026-literature, conclusion, and CAS font corrections; no new experiment. |
| `task76_manuscript_editorial_compression_summary.md` | Supporting writing revision | Records the 10.53% evidence-preserving main-text compression, preservation guardrails, 25-page CAS result, and validation; no new experiment. |
| `task36_12_acl_latex_migration.md` | Supporting writing revision | Adds a modular ACL-style LaTeX migration, official ACL style files, PDF figure assets, and static validation; the subsequent PDF compile audit is recorded in `task36_13_pdf_compile_audit.md`. |
| `task36_13_pdf_compile_audit.md` | Supporting writing revision | Installs lightweight TinyTeX, resolves real ACL compile issues, adds PDF rendering audit, and records the 19-page complete-draft layout; the next pass must produce a shorter submission cut. |
| `task49_strong_baseline_reframing_summary.md` | Supporting writing revision | Integrates Task46/47/48 strong baselines into the manuscript framing; use for the route-and-budget controller plus shared compressor/reranker decomposition. |
| `task51_experiment_validation_framework.md` | Supporting guardrail | Unified artifact audit for dimension, paired-statistics, and display-readiness checks; use before promoting new experiment outputs into paper-facing claims. |
| `task56_claim_evidence_alignment.md` | Supporting writing revision | Aligns manifold-inspired motivation, geometry diagnostics, matched-backbone results, strong baselines, and stability evidence into bounded paper-facing claims. |
| `task57_review_response_action_map.md` | Internal handoff/backlog | Converts the Hermes/GLM review into the Task58-67 execution plan; preserves geometry and feedback/LinUCB while tightening the route-and-budget claim. |

## Boundary Or Negative Evidence

| File | Status | Use in paper |
|---|---|---|
| `task26_low_cost_routing_summary.md` | Boundary/negative evidence | Candidate-cost trade-off only; does not prove final token savings. |
| `task27_dense_linucb_tradeoff_summary.md` | Boundary/negative evidence | Two-route dense-vs-LinUCB boundary test; sub-dense candidate cost loses quality and does not prove token savings. |
| `task46_sentence_mmr_same_budget_summary.md` | Boundary/strong baseline evidence | Dense+Sentence-MMR preserves dense chunk-support at 100k with lower selected sentence tokens; use to qualify IntentRoute as complementary to context compression, not dominant over it. |
| `task69_3_science_400k_checkpoint_summary.md` | Boundary/negative evidence | Science/search 400k matched endpoint and OOF budget boundary: only `1/5` folds are eligible, average saving is `3.15%`, Hit@10 changes by `-0.67pp`, and strict NI is `0/3`. Its recovery endpoint has only 3-6 affected queries/seed; do not present this row as robust lossless compression evidence. |
| `task72_recurrent_feedback_stream_summary.md` | Boundary/negative feedback evidence | Controlled recurrent-stream evaluation with no answer/context caching. Full-fused feedback does not yield a stable final-retrieval or recovery advantage; use only to bound credit assignment and keep Task40 recovery conditional. |

## Historical Or Superseded

| File | Status | Replacement |
|---|---|---|
| `task21_paper_ready_summary.md` | Historical/superseded | Use `task31_paper_evidence_package.md`, `task33_7_pre_writing_consistency_audit.md`, and `paper/full_draft/` instead. |
| `task23_lotte_scaleup_summary.md` | Partially superseded | Use only for historical scale-up provenance. For paper-facing token-cost results, use `task29_2_token_quality_frontier.md`; for geometry, use `task30_lotte_geometry_scale_validation.md`. |
| `task28_pre_token_cost_audit.md` | Historical/superseded guardrail | Use `task28_context_token_cost_summary.md` and `task28_1_context_token_backfill_summary.md` for completed corrections. |

## Internal Handoff Or Backlog

| File | Status | Note |
|---|---|---|
| `task33_5_llm_generation_smoke_handoff.md` | Internal handoff | Superseded by `task33_5_llm_generation_smoke_summary.md`. |
| `task33_pre_writing_validation_backlog.md` | Internal backlog | Use only for project management, not paper evidence. |
| `task53_embedding_backbone_generalization_plan.md` | Internal handoff/backlog | Superseded by `task53_embedding_backbone_generalization_summary.md`; kept as task provenance. |
| `results/task71_2_systems_profile/` and `scripts/task71_2_*systems_profile.py` | Internal implementation audit | Single-configuration timing, memory, and cache measurements. Retain for reproducibility only; do not cite as comparative systems evidence or include in the main/supplementary experiment tables. |

## Paper-Facing Rule

Do not cite internal `TaskXX` labels in the paper body. Convert them into
paper-facing names such as:

- conservative confidence-based context policy;
- token-quality frontier;
- multi-seed stability analysis;
- component ablation;
- geometry scale diagnostic;
- encoder robustness check;
- downstream generation smoke test;
- duplicate-evidence limitation analysis.
