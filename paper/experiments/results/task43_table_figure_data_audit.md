# Task43 Manuscript Table/Figure Data Audit

This audit checks manuscript-facing table and figure numbers against the
source experiment CSV/JSON artifacts. It verifies the markdown draft and
figure data CSVs; LaTeX layout is checked separately by `make -C paper/latex audit`.
Task40 same-query recovery token savings are checked with the same
seed-level average used in `task40_feedback_recovery_summary.md`, not an
affected-query-weighted average.

- Checks: 238
- Passed: 238
- Failed: 0

## Full Check Log

| Status | Item | Source | Expected | Detail |
|---|---|---|---|---|
| PASS | Figure asset exists figure1_system_diagram.svg | `paper/full_draft/figures/figure1_system_diagram.svg` | `paper/full_draft/figures/figure1_system_diagram.svg` |  |
| PASS | Figure asset exists figure2_token_quality_frontier.svg | `paper/full_draft/figures/figure2_token_quality_frontier.svg` | `paper/full_draft/figures/figure2_token_quality_frontier.svg` |  |
| PASS | Figure asset exists figure2_token_quality_frontier_data.csv | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` |  |
| PASS | Figure asset exists figure3_geometry_diagnostics.svg | `paper/full_draft/figures/figure3_geometry_diagnostics.svg` | `paper/full_draft/figures/figure3_geometry_diagnostics.svg` |  |
| PASS | Figure asset exists figure3_geometry_diagnostics_data.csv | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` |  |
| PASS | Figure asset exists figure4_geometry_to_gain.svg | `paper/full_draft/figures/figure4_geometry_to_gain.svg` | `paper/full_draft/figures/figure4_geometry_to_gain.svg` |  |
| PASS | Figure asset exists figure4_geometry_to_gain_data.csv | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` |  |
| PASS | Figure asset exists figure5_feedback_adaptation.svg | `paper/full_draft/figures/figure5_feedback_adaptation.svg` | `paper/full_draft/figures/figure5_feedback_adaptation.svg` |  |
| PASS | Figure asset exists figure5_feedback_adaptation_data.csv | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` |  |
| PASS | Figure asset exists figure1_system_diagram.pdf | `paper/latex/figures/figure1_system_diagram.pdf` | `paper/latex/figures/figure1_system_diagram.pdf` |  |
| PASS | Figure asset exists figure2_token_quality_frontier.pdf | `paper/latex/figures/figure2_token_quality_frontier.pdf` | `paper/latex/figures/figure2_token_quality_frontier.pdf` |  |
| PASS | Figure asset exists figure3_geometry_diagnostics.pdf | `paper/latex/figures/figure3_geometry_diagnostics.pdf` | `paper/latex/figures/figure3_geometry_diagnostics.pdf` |  |
| PASS | Figure asset exists figure4_geometry_to_gain.pdf | `paper/latex/figures/figure4_geometry_to_gain.pdf` | `paper/latex/figures/figure4_geometry_to_gain.pdf` |  |
| PASS | Figure asset exists figure5_feedback_adaptation.pdf | `paper/latex/figures/figure5_feedback_adaptation.pdf` | `paper/latex/figures/figure5_feedback_adaptation.pdf` |  |
| PASS | Table 1 row 100k | `paper/experiments/results/task38_100k_calibrated_context_budget.test_paired.csv` | `\| 100k \| `token_budget_r0.95_m4` \| True \| +0.00 pp \| 0/3 \| 6.18% \| -1.44 pp \| 13.83% \|` |  |
| PASS | Appendix G1 row 100k | `paper/experiments/results/task38_100k_calibrated_context_budget.test_paired.csv` | `\| 100k \| `token_budget_r0.95_m4` \| True \| +0.00 pp \| 6.18% \| -1.44 pp \| 13.83% \|` |  |
| PASS | Table 1 row 200k | `paper/experiments/results/task38_200k_calibrated_context_budget.test_paired.csv` | `\| 200k \| `token_budget_r0.85_m4` \| True \| +1.20 pp \| 1/3 \| 16.00% \| -2.40 pp \| 21.95% \|` |  |
| PASS | Appendix G1 row 200k | `paper/experiments/results/task38_200k_calibrated_context_budget.test_paired.csv` | `\| 200k \| `token_budget_r0.85_m4` \| True \| +1.20 pp \| 16.00% \| -2.40 pp \| 21.95% \|` |  |
| PASS | Table 1 row 400k | `paper/experiments/results/task38_400k_calibrated_context_budget.test_paired.csv` | `\| 400k \| `token_budget_r0.98_m4` \| False / pending follow-up \| +2.32 pp \| 3/3 \| 6.57% \| -0.24 pp \| 11.44% \|` |  |
| PASS | Appendix G1 row 400k | `paper/experiments/results/task38_400k_calibrated_context_budget.test_paired.csv` | `\| 400k \| `token_budget_r0.98_m4` \| False / pending follow-up \| +2.32 pp \| 6.57% \| -0.24 pp \| 11.44% \|` |  |
| PASS | Table 1 row 638k | `paper/experiments/results/task38_638k_calibrated_context_budget.test_paired.csv` | `\| 638k \| `token_budget_r0.85_m4` \| True \| -0.08 pp \| 0/3 \| 17.53% \| -3.84 pp \| 21.90% \|` |  |
| PASS | Appendix G1 row 638k | `paper/experiments/results/task38_638k_calibrated_context_budget.test_paired.csv` | `\| 638k \| `token_budget_r0.85_m4` \| True \| -0.08 pp \| 17.53% \| -3.84 pp \| 21.90% \|` |  |
| PASS | Table 2 fixed top-10 row science 20k/q200 | `paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv` | `\| science/search 20k/q200 \| 0.8950 \| 0.9267 \| +3.17 pp \|` |  |
| PASS | Appendix H1 row science 20k/q200 | `paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv` | `\| science/search 20k/q200 \| 20,490 \| 200 \| 0.8950 \| 0.9267 \| +3.17 pp \|` |  |
| PASS | Table 2 fixed top-10 row science 100k | `paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv` | `\| science/search 100k \| 0.8926 \| 0.9077 \| +1.51 pp \|` |  |
| PASS | Appendix H1 row science 100k | `paper/experiments/results/task43_lotte_science_geometry_diagnostics.csv` | `\| science/search 100k \| 101,187 \| 596 \| 0.8926 \| 0.9077 \| +1.51 pp \|` |  |
| PASS | Table 2 budget range science 20k/q200 | `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv` | `\| science/search 20k/q200 \|` |  |
| PASS | Table 2 budget saving range science 20k/q200 | `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv` | `13.18-14.31%` |  |
| PASS | Appendix H2 row 20k/q200 seed 13 | `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv` | `\| 20k/q200 \| `token_budget_r0.85_m4` \| 13 \| +2.86 pp \| 13.18% \| True \|` |  |
| PASS | Appendix H2 row 20k/q200 seed 17 | `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv` | `\| 20k/q200 \| `token_budget_r0.85_m4` \| 17 \| +1.43 pp \| 14.31% \| False \|` |  |
| PASS | Appendix H2 row 20k/q200 seed 19 | `paper/experiments/results/task39_lotte_science_20k_q200_calibrated_context_budget.test_paired.csv` | `\| 20k/q200 \| `token_budget_r0.85_m4` \| 19 \| +0.71 pp \| 13.91% \| False \|` |  |
| PASS | Table 2 budget range science 100k | `paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv` | `\| science/search 100k \|` |  |
| PASS | Table 2 budget saving range science 100k | `paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv` | `17.53-20.53%` |  |
| PASS | Appendix H2 row 100k seed 13 | `paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv` | `\| 100k \| `token_budget_r0.85_m4` \| 13 \| -1.20 pp \| 19.21% \| False \|` |  |
| PASS | Appendix H2 row 100k seed 17 | `paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv` | `\| 100k \| `token_budget_r0.85_m4` \| 17 \| +0.00 pp \| 17.53% \| False \|` |  |
| PASS | Appendix H2 row 100k seed 19 | `paper/experiments/results/task39_lotte_science_100k_calibrated_context_budget.test_paired.csv` | `\| 100k \| `token_budget_r0.85_m4` \| 19 \| -0.96 pp \| 20.53% \| False \|` |  |
| PASS | Table 3 row Dense-only | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Dense-only \| Quality floor \| 0.8674 \| 0.7026 \| 1472.39 \| 1.0000 \| - \| - \| - \| - \|` |  |
| PASS | Table 3 row BM25-only | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| BM25-only \| Lexical baseline \| 0.7232 \| 0.5240 \| 1745.12 \| 1.1852 \| - \| - \| - \| - \|` |  |
| PASS | Table 3 row Dense+BM25 hybrid | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Dense+BM25 hybrid \| Static fusion \| 0.8624 \| 0.6848 \| 1705.46 \| 1.1583 \| - \| - \| - \| - \|` |  |
| PASS | Table 3 row No feedback gated | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| No feedback gated \| Full dense fallback, no learning \| 0.8826 \| 0.7246 \| 1561.15 \| 1.0603 \| 1.0000 \| 0.0000 \| 0.1553 \| 0.1516 \|` |  |
| PASS | Table 3 row Equal noisy feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Equal noisy feedback \| No trust weighting \| 0.8641 \| 0.6604 \| 1423.84 \| 0.9670 \| 0.7480 \| 0.2520 \| 0.5979 \| 0.7517 \|` |  |
| PASS | Table 3 row Trust-weighted feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Trust-weighted feedback \| Default trust scoring \| 0.8641 \| 0.6661 \| 1399.51 \| 0.9505 \| 0.6708 \| 0.3292 \| 0.7223 \| 0.8328 \|` |  |
| PASS | Table 3 row Trust-weighted mild noise | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Trust-weighted mild noise \| Best controlled-noise point \| 0.8775 \| 0.6795 \| 1362.68 \| 0.9255 \| 0.5826 \| 0.4174 \| 0.7908 \| 0.8820 \|` |  |
| PASS | Table 3 row Conservative final policy | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Conservative final policy \| Confidence-only baseline \| 0.8652 \| 0.6737 \| 1401.24 \| 0.9517 \| 0.6708 \| 0.3292 \| 0.7223 \| 0.8328 \|` |  |
| PASS | Table 3 row Oracle feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Oracle feedback \| Upper bound \| 0.8758 \| 0.6768 \| 1327.03 \| 0.9013 \| 0.4345 \| 0.5655 \| 0.8386 \| 0.8932 \|` |  |
| PASS | Table 4 row Equal noisy feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Equal noisy feedback \| 0.8641 \| 0.9670 \| 0.7480 \| 0.2520 \| 0.5979 \| 0.7517 \|` |  |
| PASS | Table 4 row Trust-weighted feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Trust-weighted feedback \| 0.8641 \| 0.9505 \| 0.6708 \| 0.3292 \| 0.7223 \| 0.8328 \|` |  |
| PASS | Table 4 row Trust-weighted mild noise | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Trust-weighted mild noise \| 0.8775 \| 0.9255 \| 0.5826 \| 0.4174 \| 0.7908 \| 0.8820 \|` |  |
| PASS | Table 4 row Oracle feedback | `paper/experiments/results/task33_3_clean_ablation_table.csv` | `\| Oracle feedback \| 0.8758 \| 0.9013 \| 0.4345 \| 0.5655 \| 0.8386 \| 0.8932 \|` |  |
| PASS | Table 5 row science/search 100k | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science/search 100k \| 34 \| 14 \| 41.18% \| 5.76% \|` |  |
| PASS | Appendix I1 row science 100k arm boost | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science 100k \| arm boost \| 34 \| 5 \| 14.71% \| 17.40% \|` |  |
| PASS | Appendix I1 row science 100k arm boost + conservative budget | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science 100k \| arm boost + conservative budget \| 34 \| 14 \| 41.18% \| 5.76% \|` |  |
| PASS | Appendix I1 row science 100k full-context fallback | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science 100k \| full-context fallback \| 34 \| 17 \| 50.00% \| -8.07% \|` |  |
| PASS | Appendix I2 row science 100k conservative budget on learned risky arms after calibration | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science 100k \| conservative budget on learned risky arms after calibration \| +0.16 pp \| 16.13% \|` |  |
| PASS | Appendix I2 row science 100k full-context fallback on learned risky arms after calibration | `paper/experiments/results/task40_lotte_science_100k_feedback_recovery.csv` | `\| science 100k \| full-context fallback on learned risky arms after calibration \| +0.48 pp \| 13.09% \|` |  |
| PASS | Table 5 row technology/search 100k | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology/search 100k \| 42 \| 9 \| 21.43% \| 11.75% \|` |  |
| PASS | Appendix I1 row technology 100k arm boost | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology 100k \| arm boost \| 42 \| 8 \| 19.05% \| 13.68% \|` |  |
| PASS | Appendix I1 row technology 100k arm boost + conservative budget | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology 100k \| arm boost + conservative budget \| 42 \| 9 \| 21.43% \| 11.75% \|` |  |
| PASS | Appendix I1 row technology 100k full-context fallback | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology 100k \| full-context fallback \| 42 \| 12 \| 28.57% \| 0.96% \|` |  |
| PASS | Appendix I2 row technology 100k conservative budget on learned risky arms after calibration | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology 100k \| conservative budget on learned risky arms after calibration \| -0.16 pp \| 5.88% \|` |  |
| PASS | Appendix I2 row technology 100k full-context fallback on learned risky arms after calibration | `paper/experiments/results/task40_lotte_technology_100k_feedback_recovery.csv` | `\| technology 100k \| full-context fallback on learned risky arms after calibration \| +0.16 pp \| 4.25% \|` |  |
| PASS | Table 5 pooled row | `task40 pooled same-query recovery` | `\| pooled \| 76 \| 23 \| 30.26% \| - \|` |  |
| PASS | Table 6 geometry row technology/search 100k | `task30/task43 geometry diagnostics` | `\| technology/search 100k \| 182 \| 0.6437 \| 0.8870 \| 0.9033 \| -0.22 pp \|` |  |
| PASS | Table 6 geometry row technology/search 200k | `task30/task43 geometry diagnostics` | `\| technology/search 200k \| 186 \| 0.6292 \| 0.8697 \| 0.8947 \| +2.80 pp \|` |  |
| PASS | Table 6 geometry row technology/search 400k | `task30/task43 geometry diagnostics` | `\| technology/search 400k \| 190 \| 0.6110 \| 0.9016 \| 0.8826 \| +1.01 pp \|` |  |
| PASS | Table 6 geometry row technology/search 638k | `task30/task43 geometry diagnostics` | `\| technology/search 638k \| 196 \| 0.5867 \| 0.9016 \| 0.8571 \| +1.85 pp \|` |  |
| PASS | Table 6 geometry row science/search 20k/q200 | `task30/task43 geometry diagnostics` | `\| science/search 20k/q200 \| 180 \| 0.6377 \| 0.9083 \| 0.8939 \| +3.17 pp \|` |  |
| PASS | Table 6 geometry row science/search 100k | `task30/task43 geometry diagnostics` | `\| science/search 100k \| 177 \| 0.6459 \| 0.8574 \| 0.8628 \| +1.51 pp \|` |  |
| PASS | Figure 3 corpus_chunks technology/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `101311` | actual=101311 |
| PASS | Figure 3 pca_dim90 technology/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `182` | actual=182 |
| PASS | Figure 3 pca_var64 technology/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.6437` | actual=0.6437 |
| PASS | Figure 3 nearest_cluster_hit technology/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8870` | actual=0.8870 |
| PASS | Figure 3 context_retention technology/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.9033` | actual=0.9033 |
| PASS | Figure 3 corpus_chunks technology/search 200k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `201010` | actual=201010 |
| PASS | Figure 3 pca_dim90 technology/search 200k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `186` | actual=186 |
| PASS | Figure 3 pca_var64 technology/search 200k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.6292` | actual=0.6292 |
| PASS | Figure 3 nearest_cluster_hit technology/search 200k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8697` | actual=0.8697 |
| PASS | Figure 3 context_retention technology/search 200k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8947` | actual=0.8947 |
| PASS | Figure 3 corpus_chunks technology/search 400k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `400674` | actual=400674 |
| PASS | Figure 3 pca_dim90 technology/search 400k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `190` | actual=190 |
| PASS | Figure 3 pca_var64 technology/search 400k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.6110` | actual=0.6110 |
| PASS | Figure 3 nearest_cluster_hit technology/search 400k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.9016` | actual=0.9016 |
| PASS | Figure 3 context_retention technology/search 400k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8826` | actual=0.8826 |
| PASS | Figure 3 corpus_chunks technology/search 638k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `638509` | actual=638509 |
| PASS | Figure 3 pca_dim90 technology/search 638k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `196` | actual=196 |
| PASS | Figure 3 pca_var64 technology/search 638k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.5867` | actual=0.5867 |
| PASS | Figure 3 nearest_cluster_hit technology/search 638k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.9016` | actual=0.9016 |
| PASS | Figure 3 context_retention technology/search 638k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8571` | actual=0.8571 |
| PASS | Figure 3 corpus_chunks science/search 20k/q200 | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `20490` | actual=20490 |
| PASS | Figure 3 pca_dim90 science/search 20k/q200 | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `180` | actual=180 |
| PASS | Figure 3 pca_var64 science/search 20k/q200 | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.6377` | actual=0.6377 |
| PASS | Figure 3 nearest_cluster_hit science/search 20k/q200 | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.9083` | actual=0.9083 |
| PASS | Figure 3 context_retention science/search 20k/q200 | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8939` | actual=0.8939 |
| PASS | Figure 3 corpus_chunks science/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `101187` | actual=101187 |
| PASS | Figure 3 pca_dim90 science/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `177` | actual=177 |
| PASS | Figure 3 pca_var64 science/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.6459` | actual=0.6459 |
| PASS | Figure 3 nearest_cluster_hit science/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8574` | actual=0.8574 |
| PASS | Figure 3 context_retention science/search 100k | `paper/full_draft/figures/figure3_geometry_diagnostics_data.csv` | `0.8628` | actual=0.8628 |
| PASS | Figure 2 corpus_chunks technology/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `101311` | actual=101311 |
| PASS | Figure 2 policy_hit_delta_pp technology/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `0.00` | actual=0.00 |
| PASS | Figure 2 policy_saving_pct technology/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `6.18` | actual=6.18 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp technology/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-1.44` | actual=-1.44 |
| PASS | Figure 2 dense_adaptive_saving_pct technology/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `13.83` | actual=13.83 |
| PASS | Figure 2 corpus_chunks technology/search 200k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `201010` | actual=201010 |
| PASS | Figure 2 policy_hit_delta_pp technology/search 200k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `1.20` | actual=1.20 |
| PASS | Figure 2 policy_saving_pct technology/search 200k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `16.00` | actual=16.00 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp technology/search 200k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-2.40` | actual=-2.40 |
| PASS | Figure 2 dense_adaptive_saving_pct technology/search 200k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `21.95` | actual=21.95 |
| PASS | Figure 2 corpus_chunks technology/search 400k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `400674` | actual=400674 |
| PASS | Figure 2 policy_hit_delta_pp technology/search 400k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `2.32` | actual=2.32 |
| PASS | Figure 2 policy_saving_pct technology/search 400k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `6.57` | actual=6.57 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp technology/search 400k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-0.24` | actual=-0.24 |
| PASS | Figure 2 dense_adaptive_saving_pct technology/search 400k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `11.44` | actual=11.44 |
| PASS | Figure 2 corpus_chunks technology/search 638k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `638509` | actual=638509 |
| PASS | Figure 2 policy_hit_delta_pp technology/search 638k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-0.08` | actual=-0.08 |
| PASS | Figure 2 policy_saving_pct technology/search 638k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `17.53` | actual=17.53 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp technology/search 638k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-3.84` | actual=-3.84 |
| PASS | Figure 2 dense_adaptive_saving_pct technology/search 638k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `21.90` | actual=21.90 |
| PASS | Figure 2 corpus_chunks science/search 20k/q200 | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `20490` | actual=20490 |
| PASS | Figure 2 policy_hit_delta_pp science/search 20k/q200 | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `1.67` | actual=1.67 |
| PASS | Figure 2 policy_saving_pct science/search 20k/q200 | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `13.80` | actual=13.80 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp science/search 20k/q200 | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-0.71` | actual=-0.71 |
| PASS | Figure 2 dense_adaptive_saving_pct science/search 20k/q200 | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `22.69` | actual=22.69 |
| PASS | Figure 2 corpus_chunks science/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `101187` | actual=101187 |
| PASS | Figure 2 policy_hit_delta_pp science/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-0.72` | actual=-0.72 |
| PASS | Figure 2 policy_saving_pct science/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `19.09` | actual=19.09 |
| PASS | Figure 2 dense_adaptive_hit_delta_pp science/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `-1.44` | actual=-1.44 |
| PASS | Figure 2 dense_adaptive_saving_pct science/search 100k | `paper/full_draft/figures/figure2_token_quality_frontier_data.csv` | `22.60` | actual=22.60 |
| PASS | Figure 4 corpus_chunks technology/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `101311` | actual=101311 |
| PASS | Figure 4 nearest_cluster_hit_at_3 technology/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8870` | actual=0.8870 |
| PASS | Figure 4 context_retention_at_10 technology/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.9033` | actual=0.9033 |
| PASS | Figure 4 policy_hit_delta_pp technology/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.00` | actual=0.00 |
| PASS | Figure 4 policy_saving_pct technology/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `6.18` | actual=6.18 |
| PASS | Figure 4 corpus_chunks technology/search 200k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `201010` | actual=201010 |
| PASS | Figure 4 nearest_cluster_hit_at_3 technology/search 200k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8697` | actual=0.8697 |
| PASS | Figure 4 context_retention_at_10 technology/search 200k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8947` | actual=0.8947 |
| PASS | Figure 4 policy_hit_delta_pp technology/search 200k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `1.20` | actual=1.20 |
| PASS | Figure 4 policy_saving_pct technology/search 200k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `16.00` | actual=16.00 |
| PASS | Figure 4 corpus_chunks technology/search 400k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `400674` | actual=400674 |
| PASS | Figure 4 nearest_cluster_hit_at_3 technology/search 400k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.9016` | actual=0.9016 |
| PASS | Figure 4 context_retention_at_10 technology/search 400k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8826` | actual=0.8826 |
| PASS | Figure 4 policy_hit_delta_pp technology/search 400k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `2.32` | actual=2.32 |
| PASS | Figure 4 policy_saving_pct technology/search 400k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `6.57` | actual=6.57 |
| PASS | Figure 4 corpus_chunks technology/search 638k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `638509` | actual=638509 |
| PASS | Figure 4 nearest_cluster_hit_at_3 technology/search 638k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.9016` | actual=0.9016 |
| PASS | Figure 4 context_retention_at_10 technology/search 638k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8571` | actual=0.8571 |
| PASS | Figure 4 policy_hit_delta_pp technology/search 638k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `-0.08` | actual=-0.08 |
| PASS | Figure 4 policy_saving_pct technology/search 638k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `17.53` | actual=17.53 |
| PASS | Figure 4 corpus_chunks science/search 20k/q200 | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `20490` | actual=20490 |
| PASS | Figure 4 nearest_cluster_hit_at_3 science/search 20k/q200 | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.9083` | actual=0.9083 |
| PASS | Figure 4 context_retention_at_10 science/search 20k/q200 | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8939` | actual=0.8939 |
| PASS | Figure 4 policy_hit_delta_pp science/search 20k/q200 | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `1.67` | actual=1.67 |
| PASS | Figure 4 policy_saving_pct science/search 20k/q200 | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `13.80` | actual=13.80 |
| PASS | Figure 4 corpus_chunks science/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `101187` | actual=101187 |
| PASS | Figure 4 nearest_cluster_hit_at_3 science/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8574` | actual=0.8574 |
| PASS | Figure 4 context_retention_at_10 science/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `0.8628` | actual=0.8628 |
| PASS | Figure 4 policy_hit_delta_pp science/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `-0.72` | actual=-0.72 |
| PASS | Figure 4 policy_saving_pct science/search 100k | `paper/full_draft/figures/figure4_geometry_to_gain_data.csv` | `19.09` | actual=19.09 |
| PASS | Figure 5 hit_at_10 No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8826` | actual=0.8826 |
| PASS | Figure 5 token_ratio_vs_dense No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `1.0603` | actual=1.0603 |
| PASS | Figure 5 dense_rate No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `1.0000` | actual=1.0000 |
| PASS | Figure 5 linucb_rate No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.0000` | actual=0.0000 |
| PASS | Figure 5 selected_cluster_hit No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.1553` | actual=0.1553 |
| PASS | Figure 5 last_true_reward No feedback gated routing | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.1516` | actual=0.1516 |
| PASS | Figure 5 hit_at_10 Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8641` | actual=0.8641 |
| PASS | Figure 5 token_ratio_vs_dense Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.9670` | actual=0.9670 |
| PASS | Figure 5 dense_rate Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.7480` | actual=0.7480 |
| PASS | Figure 5 linucb_rate Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.2520` | actual=0.2520 |
| PASS | Figure 5 selected_cluster_hit Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.5979` | actual=0.5979 |
| PASS | Figure 5 last_true_reward Equal noisy feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.7517` | actual=0.7517 |
| PASS | Figure 5 hit_at_10 Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8641` | actual=0.8641 |
| PASS | Figure 5 token_ratio_vs_dense Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.9505` | actual=0.9505 |
| PASS | Figure 5 dense_rate Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.6708` | actual=0.6708 |
| PASS | Figure 5 linucb_rate Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.3292` | actual=0.3292 |
| PASS | Figure 5 selected_cluster_hit Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.7223` | actual=0.7223 |
| PASS | Figure 5 last_true_reward Trust-weighted feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8328` | actual=0.8328 |
| PASS | Figure 5 hit_at_10 Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8775` | actual=0.8775 |
| PASS | Figure 5 token_ratio_vs_dense Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.9255` | actual=0.9255 |
| PASS | Figure 5 dense_rate Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.5826` | actual=0.5826 |
| PASS | Figure 5 linucb_rate Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.4174` | actual=0.4174 |
| PASS | Figure 5 selected_cluster_hit Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.7908` | actual=0.7908 |
| PASS | Figure 5 last_true_reward Trust-weighted mild noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8820` | actual=0.8820 |
| PASS | Figure 5 hit_at_10 Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8758` | actual=0.8758 |
| PASS | Figure 5 token_ratio_vs_dense Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.9013` | actual=0.9013 |
| PASS | Figure 5 dense_rate Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.4345` | actual=0.4345 |
| PASS | Figure 5 linucb_rate Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.5655` | actual=0.5655 |
| PASS | Figure 5 selected_cluster_hit Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8386` | actual=0.8386 |
| PASS | Figure 5 last_true_reward Oracle feedback | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8932` | actual=0.8932 |
| PASS | Figure 5 hit_at_10 Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8479` | actual=0.8479 |
| PASS | Figure 5 token_ratio_vs_dense Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.9837` | actual=0.9837 |
| PASS | Figure 5 dense_rate Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.8670` | actual=0.8670 |
| PASS | Figure 5 linucb_rate Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.1330` | actual=0.1330 |
| PASS | Figure 5 selected_cluster_hit Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.4813` | actual=0.4813 |
| PASS | Figure 5 last_true_reward Trust-weighted strong noise | `paper/full_draft/figures/figure5_feedback_adaptation_data.csv` | `0.5912` | actual=0.5912 |
| PASS | Appendix A1 row 100k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 100k \| 0.8674 \| 0.8652 \| 0.0035 \| [0.8565, 0.8739] \| -0.0022 \|` |  |
| PASS | Appendix A2 row 100k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 100k \| 1472.39 \| 1401.24 \| 11.49 \| [1372.70, 1429.79] \| 4.83% \| [2.89%, 6.77%] \|` |  |
| PASS | Appendix A1 row 200k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 200k \| 0.7970 \| 0.8249 \| 0.0079 \| [0.8052, 0.8446] \| +0.0280 \|` |  |
| PASS | Appendix A2 row 200k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 200k \| 1444.12 \| 1376.46 \| 4.61 \| [1365.01, 1387.91] \| 4.69% \| [3.89%, 5.48%] \|` |  |
| PASS | Appendix A1 row 400k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 400k \| 0.7718 \| 0.7819 \| 0.0044 \| [0.7709, 0.7929] \| +0.0101 \|` |  |
| PASS | Appendix A2 row 400k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 400k \| 1482.30 \| 1403.43 \| 31.10 \| [1326.16, 1480.69] \| 5.32% \| [0.11%, 10.53%] \|` |  |
| PASS | Appendix A1 row 638k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 638k \| 0.7282 \| 0.7466 \| 0.0089 \| [0.7246, 0.7687] \| +0.0185 \|` |  |
| PASS | Appendix A2 row 638k | `paper/experiments/results/task29_3_seed_variance_ci.csv` | `\| 638k \| 1525.62 \| 1451.49 \| 3.83 \| [1441.97, 1461.00] \| 4.86% \| [4.24%, 5.48%] \|` |  |
| PASS | Appendix A3 dense row | `paper/experiments/results/task33_6_100k_5seed_context_tokens.csv` | `\| Dense-only \| 1 \| 0.8674 \| 1472.39 \| 1.0000x \| 0.00% \|` |  |
| PASS | Appendix A3 policy row | `paper/experiments/results/task33_6_100k_5seed_context_tokens.csv` | `\| Conservative policy \| 5 \| 0.8708 \| 1399.83 \| 0.9507x \| 4.93% \|` |  |
| PASS | Appendix B1 row 100k | `paper/experiments/results/task23_lotte_scaleup_summary.csv` | `\| 100k \| 101311 \| 0.7232 \| 0.8674 \| 0.8624 \|` |  |
| PASS | Appendix B1 row 200k | `paper/experiments/results/task23_lotte_scaleup_summary.csv` | `\| 200k \| 201010 \| 0.6292 \| 0.7970 \| 0.8003 \|` |  |
| PASS | Appendix B1 row 400k | `paper/experiments/results/task23_lotte_scaleup_summary.csv` | `\| 400k \| 400674 \| 0.5721 \| 0.7718 \| 0.7617 \|` |  |
| PASS | Appendix B1 row 638k | `paper/experiments/results/task23_lotte_scaleup_summary.csv` | `\| 638k \| 638509 \| 0.5084 \| 0.7282 \| 0.7181 \|` |  |
| PASS | Appendix C1 row Banking77 Gated cost-aware routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| Banking77 \| Gated cost-aware routing \| 0.9813 \| 120.82 \| 0.9978x \| 142.51 \|` |  |
| PASS | Appendix C1 row eManual Gated cost-aware routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| eManual \| Gated cost-aware routing \| 0.0116 \| 17.92 \| 0.9829x \| 214.07 \|` |  |
| PASS | Appendix C1 row LoTTE 100k Quality-first routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 100k \| Quality-first routing \| 0.8770 \| 1518.44 \| 1.0313x \| 229.97 \|` |  |
| PASS | Appendix C1 row LoTTE 100k Conditional fallback routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 100k \| Conditional fallback routing \| 0.8747 \| 1516.24 \| 1.0298x \| 227.29 \|` |  |
| PASS | Appendix C1 row LoTTE 100k Cluster-credit routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 100k \| Cluster-credit routing \| 0.8764 \| 1550.65 \| 1.0532x \| 181.47 \|` |  |
| PASS | Appendix C1 row LoTTE 200k Initial gated routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 200k \| Initial gated routing \| 0.8154 \| 1549.39 \| 1.0729x \| 232.01 \|` |  |
| PASS | Appendix C1 row LoTTE 400k Initial gated routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 400k \| Initial gated routing \| 0.7836 \| 1547.66 \| 1.0441x \| 233.22 \|` |  |
| PASS | Appendix C1 row LoTTE 638k Initial gated routing | `paper/experiments/results/task28_1_context_token_backfill_aggregated.csv` | `\| LoTTE 638k \| Initial gated routing \| 0.7343 \| 1599.95 \| 1.0487x \| 236.22 \|` |  |
| PASS | Appendix D PubMedQA dense | `paper/experiments/results/dense_pubmedqa_metrics.json` | `Dense reaches $\mathrm{Hit@10}=0.9930$` |  |
| PASS | Appendix D PubMedQA trust hit | `paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json` | `$\mathrm{Hit@10}=0.9940$` |  |
| PASS | Appendix D PubMedQA reward | `paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json` | `last reward $0.8727$` |  |
| PASS | Appendix D PubMedQA last-epoch cluster | `paper/experiments/results/linucb_trust_pubmedqa_prequential_metrics.json` | `selected-cluster hit
  $0.8860$` |  |
| PASS | Appendix D Banking77 dense | `paper/experiments/results/dense_banking77_metrics.json` | `Dense/reference $\mathrm{Hit@10}$ is $0.9805$` |  |
| PASS | Appendix D Banking77 trust hit | `paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json` | `$\mathrm{Hit@10}=0.9844$` |  |
| PASS | Appendix D Banking77 reward | `paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json` | `last reward $0.9805$` |  |
| PASS | Appendix D Banking77 last-epoch cluster | `paper/experiments/results/linucb_trust_banking77_heldout-test_test_corpus-full_q3080_prequential_metrics.json` | `selected-cluster hit $0.9983$` |  |
| PASS | Appendix D CUAD dense | `paper/experiments/results/dense_cuad_metrics.json` | `$\mathrm{Hit@10}$ is $0.0759$` |  |
| PASS | Appendix D CUAD trust | `paper/experiments/results/linucb_trust_cuad_prequential_metrics.json` | `$\mathrm{Hit@10}=0.0886$` |  |
| PASS | Appendix D1 row BM25 Strict chunk ID | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| BM25 \| Strict chunk ID \| 0.1154 \| 0.0244 \| 0.0256 \|` |  |
| PASS | Appendix D1 row BM25 Text-equivalent | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| BM25 \| Text-equivalent \| 0.3846 \| 0.3059 \| 0.1620 \|` |  |
| PASS | Appendix D1 row Dense Strict chunk ID | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| Dense \| Strict chunk ID \| 0.3231 \| 0.0551 \| 0.0526 \|` |  |
| PASS | Appendix D1 row Dense Text-equivalent | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| Dense \| Text-equivalent \| 0.5615 \| 0.4716 \| 0.2030 \|` |  |
| PASS | Appendix D1 row Static hybrid Strict chunk ID | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| Static hybrid \| Strict chunk ID \| 0.1692 \| 0.0366 \| 0.0287 \|` |  |
| PASS | Appendix D1 row Static hybrid Text-equivalent | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| Static hybrid \| Text-equivalent \| 0.5846 \| 0.4895 \| 0.2263 \|` |  |
| PASS | Appendix D1 row Dense Deduplicated corpus | `paper/experiments/results/emanual_failure_analysis_tables.csv` | `\| Dense \| Deduplicated corpus \| 0.8615 \| 0.5736 \| 0.3807 \|` |  |
| PASS | Appendix E1 dense row | `paper/experiments/results/task33_1a_multiqa_100k_context_tokens.csv` | `\| Dense-only \| 0.8809 \| 0.7220 \| 0.6616 \| 0.7163 \| 1514.51 \| 1.0000x \|` |  |
| PASS | Appendix E1 conservative row | `paper/experiments/results/task33_1a_multiqa_100k_context_tokens.csv` | `\| Conservative policy \| 0.8853 \| 0.7118 \| 0.6291 \| 0.6789 \| 1463.71 \| 0.9665x \|` |  |
| PASS | Appendix F1 dense row | `paper/experiments/results/task33_5_llm_generation_smoke/summary.json` | `\| Dense top-10 \| 4.4000 \| 4.6500 \| 4.6500 \| 14 \| 1.0000x \|` |  |
| PASS | Appendix F1 conservative row | `paper/experiments/results/task33_5_llm_generation_smoke/summary.json` | `\| Conservative policy \| 4.2833 \| 4.6333 \| 4.4500 \| 14 \| 0.9321x \|` |  |
| PASS | Appendix F1 tie row | `paper/experiments/results/task33_5_llm_generation_smoke/summary.json` | `\| Tie \| - \| - \| - \| 32 \| - \|` |  |
