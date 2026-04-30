# Trust-Weighted Feedback LinUCB Tables

| dataset | feedback_mode | scope | query_split | corpus_scope | num_queries | epochs | recall@10_mean | last_epoch_true_reward_mean | epoch_true_reward_gain_mean | last_epoch_selected_cluster_hit_rate_mean | epoch_selected_cluster_hit_gain_mean | feedback_alignment_rate_mean | avg_user_trust_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| banking77 | equal_noisy | heldout_test | test | full | 3080 | 3 | 0.9839 | 0.9667 | 0.1669 | 0.9930 | 0.0859 | 0.7963 | 0.7764 |
| banking77 | equal_noisy | sample | test | full | 1000 | 3 | 0.9843 | 0.8187 | 0.2400 | 0.8917 | 0.1603 | 0.7958 | 0.7772 |
| banking77 | none | heldout_test | test | full | 3080 | 3 | 0.9855 | 0.1660 | -0.0005 | 0.4390 | 0.0043 | 1.0000 | 0.0000 |
| banking77 | none | sample | test | full | 1000 | 3 | 0.9840 | 0.1773 | -0.0123 | 0.4387 | -0.0077 | 1.0000 | 0.0000 |
| banking77 | oracle | heldout_test | test | full | 3080 | 3 | 0.9846 | 0.9819 | 0.0545 | 0.9989 | 0.0192 | 1.0000 | 1.0000 |
| banking77 | oracle | sample | test | full | 1000 | 3 | 0.9857 | 0.9807 | 0.0910 | 0.9977 | 0.0413 | 1.0000 | 1.0000 |
| banking77 | trust_weighted | heldout_test | test | full | 3080 | 3 | 0.9844 | 0.9805 | 0.1317 | 0.9983 | 0.0627 | 0.7963 | 0.7764 |
| banking77 | trust_weighted | sample | test | full | 1000 | 3 | 0.9863 | 0.9583 | 0.2863 | 0.9843 | 0.1957 | 0.7958 | 0.7772 |
| cuad | equal_noisy | smoke_only | test | gt_anchored_10000 | 79 | 3 | 0.0802 | 0.0067 | -0.0033 | 0.2400 | 0.0400 | 0.7922 | 0.7744 |
| cuad | none | smoke_only | test | gt_anchored_10000 | 79 | 3 | 0.0675 | 0.0133 | 0.0067 | 0.2433 | 0.0167 | 1.0000 | 0.0000 |
| cuad | oracle | smoke_only | test | gt_anchored_10000 | 79 | 3 | 0.0970 | 0.0333 | 0.0167 | 0.2600 | -0.0333 | 1.0000 | 1.0000 |
| cuad | trust_weighted | smoke_only | test | gt_anchored_10000 | 79 | 3 | 0.0886 | 0.0233 | 0.0167 | 0.2900 | 0.0400 | 0.7922 | 0.7744 |
| emanual | equal_noisy | heldout_test | test | full | 130 | 3 | 0.1538 | 0.0530 | 0.0379 | 0.2273 | 0.0429 | 0.8025 | 0.7868 |
| emanual | none | heldout_test | test | full | 130 | 3 | 0.1436 | 0.0152 | -0.0227 | 0.2121 | -0.0581 | 1.0000 | 0.0000 |
| emanual | oracle | heldout_test | test | full | 130 | 3 | 0.1564 | 0.1035 | 0.0707 | 0.3384 | 0.0783 | 1.0000 | 1.0000 |
| emanual | trust_weighted | heldout_test | test | full | 130 | 3 | 0.1487 | 0.0556 | 0.0152 | 0.2652 | 0.0429 | 0.8025 | 0.7868 |
| pubmedqa | equal_noisy | full | train | full | 1000 | 3 | 0.9940 | 0.7793 | 0.4293 | 0.7963 | 0.4250 | 0.7958 | 0.7772 |
| pubmedqa | none | full | train | full | 1000 | 3 | 0.9933 | 0.1383 | -0.0063 | 0.1623 | -0.0060 | 1.0000 | 0.0000 |
| pubmedqa | oracle | full | train | full | 1000 | 3 | 0.9940 | 0.9513 | 0.2917 | 0.9570 | 0.2753 | 1.0000 | 1.0000 |
| pubmedqa | trust_weighted | full | train | full | 1000 | 3 | 0.9940 | 0.8727 | 0.4030 | 0.8860 | 0.3950 | 0.7958 | 0.7772 |

## Notes

- Protocol is repeated prequential feedback: each interaction is evaluated before its simulated feedback update.
- `none` is the no-feedback control; `oracle` uses clean GT-derived feedback; `equal_noisy` and `trust_weighted` use simulated noisy user feedback.
- Trust weighting scales both LinUCB updates and local feedback memory by simulated user trust.
