# Task72: Recurrent Feedback-Stream Evaluation

## Scope

This controlled prequential experiment evaluates repeated local-intent queries and an A-to-B-to-A local-intent distribution shift. It does not evaluate real-user RLHF, response caching, final-context caching, or frozen first-pass performance on unseen queries. Immutable embedding, BM25, and exact-score artifacts are the fixed offline retrieval backend; every stream event executes route selection, fusion, final-context construction, and ground-truth scoring again.

Task70 remains the binding boundary for frozen unseen-query transfer. A positive Task72 effect only supports conditional adaptation or recovery on the declared recurrent trajectory.

## Fixed Stream

| Dataset | Region-A arm | Region-B arm | Events | Unique queries |
|---|---:|---:|---:|---:|
| lotte_science_search_100k | 21 | 3 | 212 | 152 |
| lotte_technology_search_100k | 14 | 16 | 212 | 152 |

## Event-Level Outcomes

Rows are reported by controller seed and stream condition. `selected_cluster_hit` and `route_true_reward` are route diagnostics; they must not be substituted for final retrieval quality. Dense-only has no cluster diagnostic by construction.

| Dataset | Method | Seed | Condition | Phase | n | Hit@10 | Recall@10 | MRR@10 | nDCG@10 | Cluster hit | Context tokens | Dense rate |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lotte_science_search_100k | cold_no_feedback | 13 | nearby | A_nearby | 24 | 0.833 | 0.726 | 0.708 | 0.651 | 0.083 | 1889.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | nearby | B_nearby | 24 | 1.000 | 0.894 | 0.902 | 0.827 | 0.167 | 2094.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.300 | 1896.8 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.762 | 0.865 | 0.762 | 0.150 | 1848.0 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.787 | 0.864 | 0.775 | 0.100 | 1870.0 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.851 | 0.772 | 0.742 | 0.050 | 2353.3 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.851 | 0.772 | 0.741 | 0.100 | 2384.6 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | unseen | unseen_tail | 64 | 0.938 | 0.811 | 0.792 | 0.739 | 0.078 | 2163.4 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | nearby | A_nearby | 24 | 0.792 | 0.665 | 0.701 | 0.627 | 0.167 | 1893.8 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | nearby | B_nearby | 24 | 1.000 | 0.894 | 0.902 | 0.827 | 0.083 | 2252.8 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.100 | 1984.7 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.787 | 0.865 | 0.775 | 0.000 | 1900.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.799 | 0.865 | 0.782 | 0.050 | 1881.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.851 | 0.772 | 0.742 | 0.100 | 2281.9 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.851 | 0.772 | 0.742 | 0.150 | 2305.6 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | unseen | unseen_tail | 64 | 0.922 | 0.804 | 0.790 | 0.736 | 0.203 | 2152.1 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | nearby | A_nearby | 24 | 0.833 | 0.715 | 0.708 | 0.647 | 0.042 | 1888.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | nearby | B_nearby | 24 | 1.000 | 0.894 | 0.900 | 0.827 | 0.167 | 2260.0 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.787 | 0.865 | 0.776 | 0.100 | 1966.0 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.799 | 0.867 | 0.782 | 0.100 | 1870.5 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.250 | 1955.1 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.843 | 0.772 | 0.737 | 0.200 | 2239.6 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.843 | 0.775 | 0.739 | 0.200 | 2397.1 | 1.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | unseen | unseen_tail | 64 | 0.938 | 0.804 | 0.793 | 0.735 | 0.141 | 2042.0 | 1.000 |
| lotte_science_search_100k | dense | 13 | nearby | A_nearby | 24 | 0.792 | 0.649 | 0.701 | 0.618 | -- | 1751.8 | 1.000 |
| lotte_science_search_100k | dense | 13 | nearby | B_nearby | 24 | 1.000 | 0.882 | 0.902 | 0.824 | -- | 2130.3 | 1.000 |
| lotte_science_search_100k | dense | 13 | repeated | A_recurrent_return | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 13 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 13 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 13 | unseen | unseen_tail | 64 | 0.906 | 0.790 | 0.788 | 0.731 | -- | 1883.6 | 1.000 |
| lotte_science_search_100k | dense | 17 | nearby | A_nearby | 24 | 0.792 | 0.649 | 0.701 | 0.618 | -- | 1751.8 | 1.000 |
| lotte_science_search_100k | dense | 17 | nearby | B_nearby | 24 | 1.000 | 0.882 | 0.902 | 0.824 | -- | 2130.3 | 1.000 |
| lotte_science_search_100k | dense | 17 | repeated | A_recurrent_return | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 17 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 17 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 17 | unseen | unseen_tail | 64 | 0.906 | 0.790 | 0.788 | 0.731 | -- | 1883.6 | 1.000 |
| lotte_science_search_100k | dense | 19 | nearby | A_nearby | 24 | 0.792 | 0.649 | 0.701 | 0.618 | -- | 1751.8 | 1.000 |
| lotte_science_search_100k | dense | 19 | nearby | B_nearby | 24 | 1.000 | 0.882 | 0.902 | 0.824 | -- | 2130.3 | 1.000 |
| lotte_science_search_100k | dense | 19 | repeated | A_recurrent_return | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.735 | 0.857 | 0.749 | -- | 1886.7 | 1.000 |
| lotte_science_search_100k | dense | 19 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 19 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.830 | 0.771 | 0.729 | -- | 2276.2 | 1.000 |
| lotte_science_search_100k | dense | 19 | unseen | unseen_tail | 64 | 0.906 | 0.790 | 0.788 | 0.731 | -- | 1883.6 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | nearby | A_nearby | 24 | 0.792 | 0.659 | 0.701 | 0.623 | 0.625 | 1737.1 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | nearby | B_nearby | 24 | 1.000 | 0.881 | 0.902 | 0.822 | 0.833 | 2241.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | repeated | A_recurrent_return | 20 | 0.900 | 0.735 | 0.856 | 0.750 | 0.700 | 1840.3 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.770 | 0.858 | 0.768 | 0.100 | 1879.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.760 | 0.857 | 0.762 | 0.700 | 1850.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.801 | 0.765 | 0.721 | 0.800 | 2336.8 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.801 | 0.763 | 0.720 | 0.800 | 2320.7 | 1.000 |
| lotte_science_search_100k | learned_feedback | 13 | unseen | unseen_tail | 64 | 0.938 | 0.820 | 0.792 | 0.742 | 0.422 | 2127.1 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | nearby | A_nearby | 24 | 0.792 | 0.684 | 0.701 | 0.637 | 0.542 | 1805.0 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | nearby | B_nearby | 24 | 1.000 | 0.881 | 0.902 | 0.820 | 0.667 | 2166.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.787 | 0.863 | 0.776 | 0.700 | 1804.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.774 | 0.863 | 0.769 | 0.600 | 1808.5 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.787 | 0.863 | 0.776 | 0.700 | 1785.6 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.809 | 0.771 | 0.723 | 0.650 | 2241.3 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.809 | 0.771 | 0.723 | 0.700 | 2319.8 | 1.000 |
| lotte_science_search_100k | learned_feedback | 17 | unseen | unseen_tail | 64 | 0.938 | 0.806 | 0.792 | 0.733 | 0.328 | 2014.9 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | nearby | A_nearby | 24 | 0.875 | 0.742 | 0.713 | 0.651 | 0.167 | 1877.0 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | nearby | B_nearby | 24 | 1.000 | 0.894 | 0.902 | 0.827 | 0.208 | 2299.8 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.789 | 0.865 | 0.777 | 0.300 | 1863.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.789 | 0.865 | 0.776 | 0.050 | 1842.9 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.772 | 0.858 | 0.769 | 0.250 | 1841.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 0.900 | 0.792 | 0.765 | 0.718 | 0.250 | 2202.1 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 0.900 | 0.801 | 0.765 | 0.722 | 0.250 | 2207.2 | 1.000 |
| lotte_science_search_100k | learned_feedback | 19 | unseen | unseen_tail | 64 | 0.938 | 0.792 | 0.792 | 0.729 | 0.250 | 2139.1 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | nearby | A_nearby | 24 | 0.792 | 0.661 | 0.701 | 0.623 | 0.750 | 1743.1 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | nearby | B_nearby | 24 | 1.000 | 0.881 | 0.902 | 0.821 | 0.875 | 2220.8 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.789 | 0.865 | 0.777 | 0.950 | 1893.9 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.789 | 0.865 | 0.777 | 0.950 | 1893.9 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.789 | 0.865 | 0.777 | 0.950 | 1893.9 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.851 | 0.772 | 0.742 | 1.000 | 2464.0 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.851 | 0.772 | 0.742 | 1.000 | 2464.0 | 1.000 |
| lotte_science_search_100k | static_nearest | 13 | unseen | unseen_tail | 64 | 0.938 | 0.810 | 0.793 | 0.738 | 0.844 | 2072.5 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | nearby | A_nearby | 24 | 0.792 | 0.686 | 0.701 | 0.637 | 0.667 | 1862.5 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | nearby | B_nearby | 24 | 1.000 | 0.881 | 0.902 | 0.821 | 0.917 | 2217.4 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.900 | 1909.7 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.900 | 1909.7 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.799 | 0.865 | 0.781 | 0.900 | 1909.7 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.826 | 0.772 | 0.731 | 0.900 | 2256.3 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.826 | 0.772 | 0.731 | 0.900 | 2256.3 | 1.000 |
| lotte_science_search_100k | static_nearest | 17 | unseen | unseen_tail | 64 | 0.922 | 0.812 | 0.790 | 0.739 | 0.875 | 2056.0 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | nearby | A_nearby | 24 | 0.875 | 0.761 | 0.713 | 0.660 | 0.625 | 1801.5 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | nearby | B_nearby | 24 | 0.958 | 0.847 | 0.896 | 0.812 | 0.708 | 2282.7 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | repeated | A_recurrent_return | 20 | 0.900 | 0.772 | 0.858 | 0.769 | 0.800 | 1878.3 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.900 | 0.772 | 0.858 | 0.769 | 0.800 | 1878.3 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.900 | 0.772 | 0.858 | 0.769 | 0.800 | 1878.3 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | repeated | B_recurrent_shift_1 | 20 | 0.950 | 0.818 | 0.771 | 0.728 | 0.900 | 2289.2 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | repeated | B_recurrent_shift_2 | 20 | 0.950 | 0.818 | 0.771 | 0.728 | 0.900 | 2289.2 | 1.000 |
| lotte_science_search_100k | static_nearest | 19 | unseen | unseen_tail | 64 | 0.938 | 0.813 | 0.793 | 0.739 | 0.891 | 2083.7 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | nearby | A_nearby | 24 | 0.958 | 0.809 | 0.851 | 0.801 | 0.208 | 1790.9 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | nearby | B_nearby | 24 | 0.917 | 0.796 | 0.734 | 0.702 | 0.125 | 2162.0 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.802 | 0.852 | 0.753 | 0.250 | 1940.8 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.803 | 0.852 | 0.752 | 0.050 | 1832.7 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.814 | 0.852 | 0.754 | 0.150 | 1910.0 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.811 | 0.875 | 0.778 | 0.300 | 1842.8 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.803 | 0.875 | 0.775 | 0.200 | 1972.4 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | unseen | unseen_tail | 64 | 0.797 | 0.601 | 0.569 | 0.526 | 0.156 | 1435.7 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | nearby | A_nearby | 24 | 0.958 | 0.805 | 0.851 | 0.796 | 0.083 | 1874.9 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | nearby | B_nearby | 24 | 0.917 | 0.796 | 0.736 | 0.703 | 0.167 | 2090.4 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.839 | 0.852 | 0.769 | 0.150 | 1936.7 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.797 | 0.852 | 0.747 | 0.100 | 1764.3 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.839 | 0.852 | 0.769 | 0.050 | 1909.8 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.816 | 0.875 | 0.782 | 0.100 | 1704.3 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.782 | 0.200 | 1721.8 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | unseen | unseen_tail | 64 | 0.797 | 0.589 | 0.570 | 0.521 | 0.094 | 1430.2 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | nearby | A_nearby | 24 | 0.958 | 0.818 | 0.851 | 0.808 | 0.167 | 1909.2 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | nearby | B_nearby | 24 | 0.875 | 0.765 | 0.730 | 0.695 | 0.167 | 2153.4 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.823 | 0.852 | 0.758 | 0.050 | 1959.3 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.823 | 0.852 | 0.758 | 0.150 | 1868.0 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.793 | 0.852 | 0.746 | 0.200 | 1956.2 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.811 | 0.875 | 0.779 | 0.100 | 1758.8 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.782 | 0.300 | 1965.3 | 1.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | unseen | unseen_tail | 64 | 0.797 | 0.587 | 0.569 | 0.520 | 0.109 | 1427.3 | 1.000 |
| lotte_technology_search_100k | dense | 13 | nearby | A_nearby | 24 | 0.958 | 0.812 | 0.851 | 0.804 | -- | 1741.5 | 1.000 |
| lotte_technology_search_100k | dense | 13 | nearby | B_nearby | 24 | 0.917 | 0.766 | 0.737 | 0.692 | -- | 1840.2 | 1.000 |
| lotte_technology_search_100k | dense | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 13 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 13 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 13 | unseen | unseen_tail | 64 | 0.766 | 0.553 | 0.565 | 0.508 | -- | 1354.9 | 1.000 |
| lotte_technology_search_100k | dense | 17 | nearby | A_nearby | 24 | 0.958 | 0.812 | 0.851 | 0.804 | -- | 1741.5 | 1.000 |
| lotte_technology_search_100k | dense | 17 | nearby | B_nearby | 24 | 0.917 | 0.766 | 0.737 | 0.692 | -- | 1840.2 | 1.000 |
| lotte_technology_search_100k | dense | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 17 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 17 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 17 | unseen | unseen_tail | 64 | 0.766 | 0.553 | 0.565 | 0.508 | -- | 1354.9 | 1.000 |
| lotte_technology_search_100k | dense | 19 | nearby | A_nearby | 24 | 0.958 | 0.812 | 0.851 | 0.804 | -- | 1741.5 | 1.000 |
| lotte_technology_search_100k | dense | 19 | nearby | B_nearby | 24 | 0.917 | 0.766 | 0.737 | 0.692 | -- | 1840.2 | 1.000 |
| lotte_technology_search_100k | dense | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.848 | 0.852 | 0.774 | -- | 1964.8 | 1.000 |
| lotte_technology_search_100k | dense | 19 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 19 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | -- | 1894.4 | 1.000 |
| lotte_technology_search_100k | dense | 19 | unseen | unseen_tail | 64 | 0.766 | 0.553 | 0.565 | 0.508 | -- | 1354.9 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | nearby | A_nearby | 24 | 0.958 | 0.811 | 0.851 | 0.802 | 0.250 | 1786.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | nearby | B_nearby | 24 | 0.917 | 0.784 | 0.734 | 0.695 | 0.792 | 2186.6 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.828 | 0.852 | 0.761 | 0.200 | 1910.4 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.823 | 0.852 | 0.759 | 0.000 | 1855.4 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.828 | 0.852 | 0.761 | 0.200 | 1895.4 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.802 | 0.875 | 0.774 | 0.000 | 1782.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.802 | 0.875 | 0.774 | 0.050 | 1686.3 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 13 | unseen | unseen_tail | 64 | 0.797 | 0.585 | 0.570 | 0.520 | 0.297 | 1420.7 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | nearby | A_nearby | 24 | 0.958 | 0.813 | 0.851 | 0.805 | 0.125 | 1730.2 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | nearby | B_nearby | 24 | 0.917 | 0.792 | 0.734 | 0.698 | 0.208 | 2135.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.823 | 0.852 | 0.760 | 0.150 | 1895.0 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.823 | 0.852 | 0.757 | 0.150 | 1965.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.823 | 0.852 | 0.759 | 0.150 | 1902.4 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.824 | 0.875 | 0.788 | 0.100 | 1974.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.837 | 0.875 | 0.794 | 0.200 | 1872.3 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 17 | unseen | unseen_tail | 64 | 0.797 | 0.611 | 0.569 | 0.528 | 0.203 | 1400.0 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | nearby | A_nearby | 24 | 0.958 | 0.818 | 0.851 | 0.805 | 0.667 | 1818.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | nearby | B_nearby | 24 | 0.917 | 0.778 | 0.734 | 0.691 | 0.250 | 1780.7 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.843 | 0.852 | 0.773 | 0.800 | 1938.5 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.797 | 0.852 | 0.751 | 0.500 | 1971.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.818 | 0.852 | 0.764 | 0.800 | 1936.8 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.798 | 0.875 | 0.770 | 0.150 | 1647.2 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.782 | 0.150 | 1679.0 | 1.000 |
| lotte_technology_search_100k | learned_feedback | 19 | unseen | unseen_tail | 64 | 0.766 | 0.583 | 0.566 | 0.518 | 0.250 | 1386.5 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | nearby | A_nearby | 24 | 0.958 | 0.809 | 0.851 | 0.801 | 0.833 | 1837.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | nearby | B_nearby | 24 | 0.917 | 0.765 | 0.736 | 0.690 | 0.958 | 2221.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | repeated | A_recurrent_return | 20 | 0.950 | 0.847 | 0.852 | 0.777 | 0.900 | 1895.0 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.847 | 0.852 | 0.777 | 0.900 | 1895.0 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.847 | 0.852 | 0.777 | 0.900 | 1895.0 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.811 | 0.875 | 0.779 | 0.950 | 1767.3 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.811 | 0.875 | 0.779 | 0.950 | 1767.3 | 1.000 |
| lotte_technology_search_100k | static_nearest | 13 | unseen | unseen_tail | 64 | 0.797 | 0.616 | 0.570 | 0.532 | 0.891 | 1416.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | nearby | A_nearby | 24 | 0.958 | 0.820 | 0.851 | 0.809 | 0.750 | 1794.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | nearby | B_nearby | 24 | 0.917 | 0.765 | 0.734 | 0.689 | 0.958 | 2263.5 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | repeated | A_recurrent_return | 20 | 0.950 | 0.819 | 0.852 | 0.765 | 0.950 | 1938.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.819 | 0.852 | 0.765 | 0.950 | 1938.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.819 | 0.852 | 0.765 | 0.950 | 1938.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | 0.950 | 1783.5 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.816 | 0.875 | 0.783 | 0.950 | 1783.5 | 1.000 |
| lotte_technology_search_100k | static_nearest | 17 | unseen | unseen_tail | 64 | 0.828 | 0.621 | 0.574 | 0.533 | 0.906 | 1392.1 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | nearby | A_nearby | 24 | 0.958 | 0.820 | 0.851 | 0.808 | 0.833 | 1828.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | nearby | B_nearby | 24 | 0.917 | 0.796 | 0.735 | 0.702 | 0.917 | 2235.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | repeated | A_recurrent_return | 20 | 0.950 | 0.857 | 0.852 | 0.782 | 0.950 | 1943.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | repeated | A_recurrent_warmup_1 | 20 | 0.950 | 0.857 | 0.852 | 0.782 | 0.950 | 1943.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | repeated | A_recurrent_warmup_2 | 20 | 0.950 | 0.857 | 0.852 | 0.782 | 0.950 | 1943.8 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | repeated | B_recurrent_shift_1 | 20 | 1.000 | 0.811 | 0.875 | 0.779 | 0.900 | 1766.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | repeated | B_recurrent_shift_2 | 20 | 1.000 | 0.811 | 0.875 | 0.779 | 0.900 | 1766.2 | 1.000 |
| lotte_technology_search_100k | static_nearest | 19 | unseen | unseen_tail | 64 | 0.812 | 0.605 | 0.572 | 0.527 | 0.938 | 1419.6 | 1.000 |

## Paired Trajectory Comparisons

Confidence intervals use a bootstrap over unique query-ID blocks, retaining all repeated occurrences of an ID. They describe the fixed trajectory only and are not pooled as IID evidence across conditions, seeds, or datasets.

| Dataset | Seed | Condition | Comparison | Metric | Query blocks | Delta | 95% CI |
|---|---:|---|---|---|---:|---:|---|
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.005 | [-0.021, 0.036] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | 0.002 | [-0.010, 0.016] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 48.104 | [-66.297, 166.626] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | -0.001 | [-0.016, 0.013] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | 0.000 | [-0.007, 0.008] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.083 | [-0.188, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.083 | [-0.188, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | 7.208 | [-84.652, 95.918] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | -0.021 | [-0.062, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | -0.040 | [-0.093, -0.002] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | -0.003 | [-0.010, 0.000] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | -0.017 | [-0.036, -0.001] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.604 | [0.458, 0.750] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.604 | [0.438, 0.750] |
| lotte_science_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | -2.833 | [-156.005, 161.147] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | -0.025 | [-0.075, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | -0.005 | [-0.065, 0.035] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | -0.003 | [-0.010, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | 0.001 | [-0.022, 0.017] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | 11.262 | [-141.690, 166.773] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | -0.050 | [-0.125, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | -0.042 | [-0.103, -0.004] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | -0.008 | [-0.020, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | -0.019 | [-0.044, -0.002] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.325 | [-0.450, -0.208] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.317 | [-0.434, -0.200] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | -86.287 | [-216.581, 35.637] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | -0.050 | [-0.125, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | -0.039 | [-0.100, -0.002] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | -0.008 | [-0.019, 0.000] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | -0.017 | [-0.041, -0.001] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | 0.521 | [0.379, 0.654] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | 0.504 | [0.358, 0.642] |
| lotte_science_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | -27.617 | [-179.712, 120.307] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.031 | [0.000, 0.078] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.029 | [-0.013, 0.079] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.004 | [0.000, 0.010] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | 0.011 | [-0.007, 0.028] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 243.500 | [101.714, 422.914] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | 0.009 | [-0.018, 0.037] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | -0.001 | [-0.003, 0.000] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | 0.004 | [-0.007, 0.016] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.422 | [-0.578, -0.250] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.406 | [-0.578, -0.234] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | 54.609 | [-101.645, 236.074] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | 0.009 | [-0.013, 0.032] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | -0.001 | [-0.003, 0.001] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | 0.003 | [-0.006, 0.014] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.344 | [0.219, 0.469] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.344 | [0.219, 0.469] |
| lotte_science_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | -36.359 | [-124.766, 51.781] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.017 | [-0.012, 0.050] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | 0.008 | [-0.007, 0.023] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 44.542 | [-65.316, 150.730] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | -0.001 | [-0.016, 0.012] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | -0.000 | [-0.009, 0.007] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.188 | [-0.312, -0.062] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.188 | [-0.312, -0.062] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | -54.312 | [-138.128, 27.544] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | 0.002 | [-0.021, 0.027] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | 0.001 | [-0.011, 0.014] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.479 | [0.292, 0.646] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.479 | [0.312, 0.646] |
| lotte_science_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | -87.708 | [-191.920, 7.356] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | 0.025 | [0.000, 0.075] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | 0.013 | [-0.025, 0.050] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | 0.003 | [-0.001, 0.009] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | 0.009 | [-0.009, 0.025] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | -41.392 | [-207.055, 117.102] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | -0.017 | [-0.040, 0.000] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | -0.002 | [-0.005, 0.001] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | -0.008 | [-0.021, 0.001] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.229 | [-0.367, -0.092] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.229 | [-0.371, -0.092] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | -42.967 | [-154.982, 64.817] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | -0.027 | [-0.060, -0.002] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | -0.002 | [-0.005, 0.001] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | -0.013 | [-0.029, 0.000] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | 0.583 | [0.433, 0.725] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | 0.583 | [0.438, 0.725] |
| lotte_science_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | -67.975 | [-197.305, 58.585] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.031 | [0.000, 0.078] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.016 | [-0.032, 0.070] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.005 | [0.000, 0.010] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | 0.002 | [-0.016, 0.021] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 131.359 | [28.959, 227.877] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | 0.016 | [0.000, 0.047] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | -0.006 | [-0.046, 0.040] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | 0.002 | [0.000, 0.006] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | -0.006 | [-0.022, 0.012] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.547 | [-0.672, -0.422] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.531 | [-0.656, -0.391] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | -41.094 | [-152.130, 59.438] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | 0.016 | [0.000, 0.047] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | 0.001 | [-0.037, 0.047] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | 0.002 | [0.000, 0.006] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | -0.003 | [-0.020, 0.015] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.125 | [-0.016, 0.266] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.125 | [-0.016, 0.281] |
| lotte_science_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | -137.219 | [-322.238, 5.862] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.042 | [0.000, 0.104] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.053 | [0.000, 0.120] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | 0.006 | [0.000, 0.015] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | 0.018 | [-0.002, 0.042] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 147.333 | [-0.897, 309.802] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.021 | [0.000, 0.062] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | 0.014 | [-0.022, 0.067] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | 0.003 | [0.000, 0.009] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | 0.003 | [-0.012, 0.022] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.479 | [-0.625, -0.333] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.479 | [-0.625, -0.333] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | 46.292 | [-90.744, 196.296] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | 0.021 | [0.000, 0.062] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | 0.014 | [-0.021, 0.064] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | 0.003 | [0.000, 0.008] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | 0.002 | [-0.012, 0.019] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.083 | [-0.062, 0.229] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.083 | [-0.062, 0.229] |
| lotte_science_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | 14.146 | [-108.399, 147.126] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | -0.008 | [-0.075, 0.050] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | 0.008 | [-0.040, 0.048] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | 0.000 | [-0.008, 0.007] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | 0.008 | [-0.011, 0.026] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | -54.542 | [-176.454, 62.813] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | -0.008 | [-0.075, 0.050] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | -0.005 | [-0.035, 0.017] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | -0.001 | [-0.008, 0.007] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | -0.001 | [-0.013, 0.008] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.625 | [-0.771, -0.479] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.633 | [-0.771, -0.479] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | -56.917 | [-168.959, 47.547] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | -0.033 | [-0.092, 0.000] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | -0.029 | [-0.070, 0.002] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | -0.005 | [-0.013, 0.000] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | -0.011 | [-0.028, 0.002] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | 0.050 | [-0.067, 0.171] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | 0.042 | [-0.071, 0.158] |
| lotte_science_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | -97.600 | [-195.258, -11.914] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.031 | [0.000, 0.078] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.002 | [-0.035, 0.046] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.004 | [0.000, 0.010] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | -0.002 | [-0.017, 0.014] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 255.562 | [106.947, 435.363] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | -0.021 | [-0.044, -0.005] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | -0.001 | [-0.003, 0.000] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | -0.010 | [-0.020, -0.003] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.641 | [-0.781, -0.500] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.656 | [-0.797, -0.500] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | 55.422 | [-101.301, 245.220] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | -0.012 | [-0.033, 0.008] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | -0.001 | [-0.003, 0.000] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | -0.006 | [-0.016, 0.004] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.109 | [-0.031, 0.250] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.078 | [-0.047, 0.203] |
| lotte_science_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | 97.156 | [-46.441, 275.515] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.000 | [-0.062, 0.062] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.008 | [-0.054, 0.073] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | -0.002 | [-0.011, 0.006] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | 0.001 | [-0.022, 0.022] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 195.833 | [-6.391, 473.147] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | 0.010 | [-0.007, 0.036] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | -0.001 | [-0.002, 0.000] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | 0.003 | [-0.006, 0.013] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.375 | [-0.542, -0.208] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.354 | [-0.501, -0.208] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | -42.812 | [-144.211, 51.110] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | -0.005 | [-0.020, 0.007] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | -0.000 | [-0.001, 0.000] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | -0.003 | [-0.012, 0.005] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.354 | [0.167, 0.542] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.354 | [0.167, 0.542] |
| lotte_technology_search_100k | 13 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | 10.229 | [-80.336, 100.819] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | -0.018 | [-0.045, 0.006] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | -0.011 | [-0.028, 0.004] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | -118.792 | [-361.339, 45.263] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | -0.015 | [-0.040, 0.008] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | -0.010 | [-0.026, 0.004] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.846 | [-0.950, -0.717] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.821 | [-0.933, -0.683] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | -20.367 | [-90.626, 44.253] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | 0.007 | [-0.011, 0.029] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | 0.002 | [-0.007, 0.012] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | -0.121 | [-0.237, -0.008] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | -0.121 | [-0.237, -0.008] |
| lotte_technology_search_100k | 13 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | -90.229 | [-232.122, 1.834] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.031 | [0.000, 0.078] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.031 | [-0.018, 0.091] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.005 | [-0.001, 0.013] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | 0.012 | [-0.010, 0.034] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 65.812 | [-68.111, 172.943] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | -0.031 | [-0.062, -0.006] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | -0.001 | [-0.003, 0.001] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | -0.012 | [-0.025, -0.000] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.594 | [-0.719, -0.469] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.547 | [-0.672, -0.422] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | 3.906 | [-56.145, 52.907] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | -0.016 | [-0.039, 0.002] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | 0.001 | [-0.000, 0.002] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | -0.006 | [-0.017, 0.002] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.141 | [-0.016, 0.281] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.125 | [-0.016, 0.266] |
| lotte_technology_search_100k | 13 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | -15.031 | [-73.627, 32.456] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.000 | [-0.062, 0.062] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.014 | [-0.051, 0.079] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | -0.001 | [-0.010, 0.006] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | 0.003 | [-0.020, 0.026] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 142.167 | [-60.882, 447.464] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | 0.010 | [-0.010, 0.038] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | 0.003 | [-0.007, 0.014] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.688 | [-0.812, -0.542] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.667 | [-0.812, -0.521] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | -95.854 | [-192.398, -5.554] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | 0.002 | [-0.005, 0.011] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | -0.001 | [-0.003, 0.000] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | 0.002 | [-0.004, 0.010] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.042 | [-0.083, 0.167] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.042 | [-0.083, 0.167] |
| lotte_technology_search_100k | 17 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | -49.625 | [-143.669, 29.480] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | -0.005 | [-0.033, 0.020] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | -0.004 | [-0.021, 0.012] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | -7.321 | [-112.699, 98.121] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | 0.009 | [-0.021, 0.045] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | 0.001 | [-0.015, 0.017] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.800 | [-0.912, -0.675] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.800 | [-0.912, -0.675] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | 61.429 | [-106.776, 287.373] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | 0.006 | [-0.011, 0.023] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | 0.003 | [-0.008, 0.012] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | 0.025 | [-0.079, 0.133] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | 0.025 | [-0.079, 0.133] |
| lotte_technology_search_100k | 17 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | 130.629 | [-5.682, 360.397] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.031 | [-0.031, 0.094] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.057 | [-0.002, 0.123] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.004 | [-0.003, 0.013] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | 0.020 | [-0.002, 0.045] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 45.141 | [-92.595, 159.917] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | -0.031 | [-0.094, 0.031] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | -0.010 | [-0.061, 0.041] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | -0.004 | [-0.013, 0.003] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | -0.005 | [-0.023, 0.014] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.703 | [-0.812, -0.594] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.719 | [-0.828, -0.609] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | 7.906 | [-49.610, 65.149] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | 0.000 | [-0.062, 0.062] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | 0.021 | [-0.013, 0.066] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | -0.001 | [-0.008, 0.006] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | 0.007 | [-0.006, 0.023] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.109 | [0.000, 0.219] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.062 | [-0.047, 0.172] |
| lotte_technology_search_100k | 17 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | -30.188 | [-85.484, 19.766] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | hit_at_10 | 48 | 0.000 | [-0.062, 0.062] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | evidence_recall_at_10 | 48 | 0.009 | [-0.054, 0.073] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | mrr_at_10 | 48 | -0.001 | [-0.010, 0.006] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | ndcg_at_10 | 48 | -0.000 | [-0.024, 0.021] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_dense | final_context_tokens | 48 | 8.896 | [-148.521, 143.482] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | hit_at_10 | 48 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 48 | -0.010 | [-0.027, 0.000] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | mrr_at_10 | 48 | -0.000 | [-0.001, 0.000] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | ndcg_at_10 | 48 | -0.007 | [-0.017, -0.000] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | selected_cluster_hit | 48 | -0.417 | [-0.562, -0.292] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | route_true_reward | 48 | -0.396 | [-0.542, -0.250] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_static_nearest | final_context_tokens | 48 | -232.562 | [-659.793, 24.191] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | hit_at_10 | 48 | 0.021 | [0.000, 0.062] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 48 | 0.007 | [-0.031, 0.058] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 48 | 0.002 | [0.000, 0.006] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 48 | -0.003 | [-0.018, 0.014] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 48 | 0.292 | [0.146, 0.438] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | route_true_reward | 48 | 0.292 | [0.146, 0.438] |
| lotte_technology_search_100k | 19 | nearby | learned_feedback_minus_cold_no_feedback | final_context_tokens | 48 | -231.562 | [-641.072, 34.837] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | evidence_recall_at_10 | 40 | -0.019 | [-0.042, 0.002] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | ndcg_at_10 | 40 | -0.009 | [-0.022, 0.002] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_dense | final_context_tokens | 40 | -123.592 | [-371.590, 64.001] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 40 | -0.020 | [-0.042, -0.004] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | ndcg_at_10 | 40 | -0.011 | [-0.022, -0.003] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | selected_cluster_hit | 40 | -0.500 | [-0.650, -0.354] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | route_true_reward | 40 | -0.500 | [-0.646, -0.350] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_static_nearest | final_context_tokens | 40 | -48.942 | [-135.947, 27.674] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | hit_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 40 | 0.000 | [-0.013, 0.013] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 40 | 0.000 | [0.000, 0.000] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 40 | 0.002 | [-0.006, 0.011] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 40 | 0.258 | [0.087, 0.421] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | route_true_reward | 40 | 0.258 | [0.092, 0.425] |
| lotte_technology_search_100k | 19 | repeated | learned_feedback_minus_cold_no_feedback | final_context_tokens | 40 | -88.921 | [-258.424, 40.688] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | hit_at_10 | 64 | 0.000 | [-0.062, 0.062] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | evidence_recall_at_10 | 64 | 0.029 | [-0.023, 0.090] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | mrr_at_10 | 64 | 0.001 | [-0.008, 0.010] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | ndcg_at_10 | 64 | 0.010 | [-0.012, 0.034] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | selected_cluster_hit | 0 | -- | -- |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | route_true_reward | 0 | -- | -- |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_dense | final_context_tokens | 64 | 31.625 | [-71.813, 124.068] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | hit_at_10 | 64 | -0.047 | [-0.109, 0.000] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | evidence_recall_at_10 | 64 | -0.023 | [-0.054, 0.006] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | mrr_at_10 | 64 | -0.006 | [-0.012, -0.000] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | ndcg_at_10 | 64 | -0.009 | [-0.023, 0.004] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | selected_cluster_hit | 64 | -0.688 | [-0.797, -0.578] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | route_true_reward | 64 | -0.656 | [-0.766, -0.531] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_static_nearest | final_context_tokens | 64 | -33.125 | [-165.691, 119.188] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | hit_at_10 | 64 | -0.031 | [-0.078, 0.000] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | evidence_recall_at_10 | 64 | -0.004 | [-0.040, 0.032] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | mrr_at_10 | 64 | -0.003 | [-0.008, 0.000] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | ndcg_at_10 | 64 | -0.003 | [-0.018, 0.012] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | selected_cluster_hit | 64 | 0.141 | [0.016, 0.266] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | route_true_reward | 64 | 0.094 | [-0.016, 0.203] |
| lotte_technology_search_100k | 19 | unseen | learned_feedback_minus_cold_no_feedback | final_context_tokens | 64 | -40.844 | [-175.658, 106.753] |

## Shift Adaptation and Conditional Recovery

The B first-to-second occurrence comparison is a diagnostic for adaptation after the declared A-to-B shift. Recovery is conditional on an earlier selected-cluster miss and is neither an unconditional success rate nor a claim of complete recovery.

| Dataset | Method | Seed | B-shift cluster-hit delta | B-shift route-reward delta | B-shift Hit@10 delta |
|---|---|---:|---:|---:|---:|
| lotte_science_search_100k | dense | 13 | -- | -- | 0.000 |
| lotte_science_search_100k | dense | 17 | -- | -- | 0.000 |
| lotte_science_search_100k | dense | 19 | -- | -- | 0.000 |
| lotte_science_search_100k | static_nearest | 13 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | static_nearest | 17 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | static_nearest | 19 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | 0.050 | 0.050 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | 0.050 | 0.050 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | learned_feedback | 13 | 0.000 | 0.000 | 0.000 |
| lotte_science_search_100k | learned_feedback | 17 | 0.050 | 0.050 | 0.000 |
| lotte_science_search_100k | learned_feedback | 19 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | dense | 13 | -- | -- | 0.000 |
| lotte_technology_search_100k | dense | 17 | -- | -- | 0.000 |
| lotte_technology_search_100k | dense | 19 | -- | -- | 0.000 |
| lotte_technology_search_100k | static_nearest | 13 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | static_nearest | 17 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | static_nearest | 19 | 0.000 | 0.000 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | -0.100 | -0.100 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | 0.100 | 0.100 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | 0.200 | 0.200 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 13 | 0.050 | 0.050 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 17 | 0.100 | 0.100 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 19 | 0.000 | 0.000 | 0.000 |

| Dataset | Method | Seed | Route-affected repeated queries | Cluster recovery | Final-retrieval affected queries | Final Hit@10 recovery |
|---|---|---:|---:|---:|---:|---:|
| lotte_science_search_100k | static_nearest | 13 | 1 | 0.000 | 2 | 0.000 |
| lotte_science_search_100k | static_nearest | 17 | 4 | 0.000 | 2 | 0.000 |
| lotte_science_search_100k | static_nearest | 19 | 6 | 0.000 | 3 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 13 | 36 | 0.222 | 2 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 17 | 38 | 0.132 | 2 | 0.000 |
| lotte_science_search_100k | cold_no_feedback | 19 | 34 | 0.294 | 2 | 0.000 |
| lotte_science_search_100k | learned_feedback | 13 | 22 | 0.591 | 4 | 0.000 |
| lotte_science_search_100k | learned_feedback | 17 | 15 | 0.267 | 2 | 0.000 |
| lotte_science_search_100k | learned_feedback | 19 | 34 | 0.206 | 3 | 0.000 |
| lotte_technology_search_100k | static_nearest | 13 | 3 | 0.000 | 1 | 0.000 |
| lotte_technology_search_100k | static_nearest | 17 | 2 | 0.000 | 1 | 0.000 |
| lotte_technology_search_100k | static_nearest | 19 | 3 | 0.000 | 1 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 13 | 33 | 0.212 | 1 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 17 | 36 | 0.167 | 1 | 0.000 |
| lotte_technology_search_100k | cold_no_feedback | 19 | 35 | 0.200 | 1 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 13 | 40 | 0.150 | 1 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 17 | 35 | 0.057 | 1 | 0.000 |
| lotte_technology_search_100k | learned_feedback | 19 | 27 | 0.259 | 1 | 0.000 |

## Validation

- Event coverage: passed.
- No answer/final-context cache: passed.
- Exact artifact backend declared: passed.

A failure to improve nearby or unseen events is a valid negative result. The final paper may only use a Task72 finding after its condition, controller, and uncertainty are preserved alongside the Task70 frozen-policy boundary.
