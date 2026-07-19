# Task79 LLMLingua-2 Matched Compressor

Status: **COMPLETE**

- Fixed queries: `300`
- Completed compressed contexts: `600/600`
- Device: `AMD Radeon RX 9070 XT`
- Peak allocated VRAM: `2.526 GiB`
- Protocol signature: `85b3461ed3c06e6b0cf7fe37f290d16e402cb1be64b83219fea6cd0fd084e23a`

| Endpoint | Queries | Source tokens | Target tokens | Actual tokens | Saving | Mean abs target error | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| dense_llmlingua2_matched_sent_mmr | 300 | 438426 | 371940 | 377766 | 13.84% | 20.15 | 1.422s |
| intentroute_llmlingua2_matched_sent_mmr_seed19 | 300 | 409345 | 347214 | 352506 | 13.89% | 18.36 | 1.275s |

The matched targets are frozen Task63 Sentence-MMR token counts. No answer or judge API is called here.
