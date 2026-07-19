# Task79 LLMLingua-2 ROCm Preflight

Status: **PASS**

- Official repository commit: `e0e9d99beb94098bbd924aa53c2c112eac41c758`
- Model revision: `ebaba9b0e874dadd3003ffcff828e4397e568089`
- Model aggregate SHA256: `bc8ffa30f061337d5de7b7b247bab67b2e9967cab786804dfe9f7e0104dae871`
- Device: `AMD Radeon RX 9070 XT`
- PyTorch / HIP: `2.9.1+rocm7.2.3.gitebc02d69` / `7.2.53211-c2d9476115`
- Model load time: `5.450s`
- Peak allocated VRAM: `2.526 GiB`

| Query | Source tokens | Compressed tokens | Saving | First run | Repeat exact |
|---|---:|---:|---:|---:|---:|
| lotte_technology_search_100k_q113 | 314 | 262 | 16.56% | 2.454s | yes |
| lotte_technology_search_100k_q387 | 1358 | 1185 | 12.74% | 1.361s | yes |
| lotte_technology_search_100k_q506 | 4595 | 3947 | 14.10% | 2.337s | yes |

No answer generation or LLM judging is performed by this preflight.
