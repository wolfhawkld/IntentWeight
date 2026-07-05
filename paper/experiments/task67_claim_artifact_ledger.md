# Task67 Claim-to-Artifact Ledger

Updated: 2026-07-05

This ledger maps the manuscript's quantitative evidence groups to their
tracked source artifacts. The combined evidence target performs three layers:
921 artifact checks, 139 exact legacy/supplement display checks, and current
main/supplement display-value provenance checks.

| Paper evidence | Primary source artifacts | Automated check |
| --- | --- | --- |
| Table 1 and Figure 2 technology points: frozen token-quality frontier | `task38_{100k,200k,400k,638k}_calibrated_context_budget.json` and `.test_paired.csv` | policy, eligibility, seed count, Hit delta, token saving, dense-truncation comparison |
| Figure 2 science points | Task39 LoTTE science calibrated-context-budget JSON/CSV artifacts | existence, dimensions, paired arithmetic, and plotted-data schema through Task51; visual plot audit through Task67 |
| Table 2: MiniLM/BGE/E5 matched-backbone robustness | `task53_embedding_backbone_generalization.csv` and `task54_bge_base_100k_positive_hit_context_budget.test_paired.csv` | dense and IntentRoute Hit@10, delta, and token saving recomputed |
| Table 3: geometry/random/feedback controls | `task58_geometry_random_ablation_summary.csv` and `task59_feedback_control_summary.csv` | route reward, cluster hit, dense rate, test Hit delta, and token saving recomputed |
| Table 4: arm-count sensitivity | `task60_arm_count_sensitivity_summary.csv` | static reward, full-route outcome, and gated outcome recomputed per K |
| Figure 3: geometry-to-control diagnostic | `task61_geometry_to_control_points.csv` and `figure3_geometry_to_control_data.csv` | plotted technology outcome fields cross-checked to Table 1; source tables covered by Task51 |
| Table 5: downstream correctness and context saving | `task65_7_multi_judge_analysis.paired.csv` | DeepSeek, GLM-5.2, MiniMax-M3, majority-vote deltas/CIs, and context-saving CIs recomputed |
| Downstream corpus size and judge coverage | Task63 `answers.jsonl`, `judgments.jsonl`, `judgment_failures.jsonl`; Task65.7 missingness tables | exact record counts, schema, unique-key cardinality, and missingness rows |
| Safe-compression attribution and matched-frontier boundaries | Task65.1-65.6 JSON/CSV artifacts | result schema, exact representative-table row counts, required columns, finite values, and probability ranges |
| Supplementary Tables S1-S6, S13, S17-S20 | Task23/28/29/33/38/39/40/43 source artifacts | 139 exact source-derived display and figure checks through the updated Task43 audit |
| Supplementary Tables S7-S12, S14-S16, S21-S28 | Task46-Task65 source CSV/JSON artifacts | 446 displayed numeric values checked against table-specific source fields, unit conversions, and source-group statistics |

## Boundary Statements Preserved

- Route quality, final fused retrieval quality, and post-ranking context
  compression are distinct outcomes.
- Geometry and feedback improve route construction and diagnosis; they are not
  claimed to deterministically predict whether compression preserves Hit@10.
- Dense/BM25 rescue remains a major source of final-quality robustness.
- Frozen-policy and cross-scale results are reported with their observed split
  sensitivity; no universal dominance claim is inferred.
- Three-model LLM judging is supporting evidence, not human evaluation.

## Reproduction

```bash
.venv/bin/python paper/experiments/scripts/task51_experiment_validation.py
.venv/bin/python paper/experiments/scripts/task43_audit_manuscript_tables_figures.py
.venv/bin/python paper/experiments/scripts/task67_validate_paper_evidence.py
```
