# Task78 GPU Revalidation

- Mode: `formal`
- Status: **PASS**
- Git commit: `c382c06b88ce307c1e25672df4064c8db33fd683`
- GPU: `AMD Radeon RX 9070 XT`
- PyTorch/HIP: `2.9.1+rocm7.2.3.gitebc02d69` / `7.2.53211-c2d9476115`

| Case | Corpus cosine min | Query cosine min | Top-10 members | Top-10 order | Metrics exact | Status |
|---|---:|---:|---:|---:|---:|---|
| task47_minilm_technology_100k | 0.99999982 | 0.99999988 | 100.00% | 100.00% | yes | PASS |
| task52_bge_technology_100k | 1.00000000 | 1.00000000 | 100.00% | 100.00% | yes | PASS |
| task53_e5_technology_100k | 1.00000000 | 1.00000000 | 100.00% | 100.00% | yes | PASS |
| task73_minilm_recreation_100k | 0.99999976 | 0.99999988 | 100.00% | 100.00% | yes | PASS |
| task73_minilm_writing_100k | 0.99999976 | 0.99999988 | 100.00% | 99.91% | yes | PASS |

Formal reruns use isolated local caches. They do not overwrite canonical paper artifacts.

Ordered top-10 differences investigated: 1. Membership and metrics remain the acceptance boundary; details are retained in JSON.
