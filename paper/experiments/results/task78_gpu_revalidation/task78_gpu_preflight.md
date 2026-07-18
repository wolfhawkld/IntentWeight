# Task78 GPU Revalidation

- Mode: `preflight`
- Status: **PASS**
- Git commit: `c382c06b88ce307c1e25672df4064c8db33fd683`
- GPU: `AMD Radeon RX 9070 XT`
- PyTorch/HIP: `2.9.1+rocm7.2.3.gitebc02d69` / `7.2.53211-c2d9476115`

| Case | Corpus cosine min | Query cosine min | Top-10 exact | Metrics exact | Status |
|---|---:|---:|---:|---:|---|
| task47_minilm_technology_100k | 0.99999994 | 1.00000000 | n/a | n/a | PASS |
| task52_bge_technology_100k | 0.99999988 | 1.00000000 | n/a | n/a | PASS |
| task53_e5_technology_100k | 1.00000000 | 0.99999994 | n/a | n/a | PASS |
| task73_minilm_recreation_100k | 0.99999988 | 0.99999994 | n/a | n/a | PASS |
| task73_minilm_writing_100k | 0.99999988 | 0.99999988 | n/a | n/a | PASS |

Formal reruns use isolated local caches. They do not overwrite canonical paper artifacts.
