# Task79 Official LLMLingua-2 Matched-Compressor Summary

Status: local compression and DeepSeek evaluation complete; independent GLM-5.2
and MiniMax-M3 judgments pending

Date: 2026-07-18

## Protocol

Task79 evaluates whether the Dense-versus-IntentRoute token/answer-quality
relationship persists under the official learned LLMLingua-2 compressor. It
reuses the exact 300 Task63 frozen queries, Dense top-10 source pools, Task38
IntentRoute seed-19 pools, answer prompt, answer model, and existing
Sentence-MMR answers. Retrieval and routing are not rerun or retuned.

For each query and upstream method, the LLMLingua-2 target is the already
tracked token count of the corresponding Task63 Sentence-MMR `r=0.85`
endpoint. The target rule was frozen before Task79 answers or judgments. The
official compressor's discrete output is retained without post-hoc adjustment.

The historical artifact label
`intentweight_sent_mmr_r0.85_l0.70_seed19` is preserved only for byte-exact
Task63 provenance; the paper-facing method remains IntentRoute.

## Official Model And ROCm Gate

- Model: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`, approximately
  0.6B parameters.
- Fixed revision: `ebaba9b0e874dadd3003ffcff828e4397e568089`.
- Weight size: 2,235,829,648 bytes (2.236 GB decimal; 2.082 GiB).
- Weight SHA256:
  `a33a153b2493bff6be06af6921e69de9c0d0bb6ff06fe5bbb68670ba8d980ae2`.
- Official code commit:
  `e0e9d99beb94098bbd924aa53c2c112eac41c758`.
- Runtime device: AMD Radeon RX 9070 XT under the local WSL DXG/ROCm path.
- Model load: 5.876 s; peak allocated/reserved VRAM: 2.526/3.398 GiB.
- Fixed short/median/long pilot outputs are repeat-exact and use exact
  `cl100k_base` accounting.
- The full segment audit covers 600 contexts and 6,047 classifier segments.
  Maximum content length is 511 tokens, with zero content tokens dropped at the
  model's 512-token boundary.

## Matched Compression

| Upstream | Queries | Source tokens/query | Frozen target | Actual LLMLingua-2 | Source saving | Mean absolute target error | Within 5% target | Latency/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense | 300 | 1,461.42 | 1,239.80 | 1,259.22 | 13.84% | 20.15 tokens / 1.519% | 293/300 | 1.422 s |
| IntentRoute | 300 | 1,364.48 | 1,157.38 | 1,175.02 | 13.89% | 18.36 tokens / 1.466% | 293/300 | 1.275 s |

The largest per-query relative target deviations are 9.72% for Dense and 9.42%
for IntentRoute. These occur at discrete word thresholds and are reported, not
corrected. There are no empty outputs, dropped chunk IDs, reordered chunks, or
token-accounting mismatches.

## DeepSeek Interim Result

All 600 new answers are valid JSON. DeepSeek provides 1,200/1,200 Task79
judgments after resumable technical retries; empty/truncated provider responses
remain in the failure log and are not interpreted as negative judgments.

| Endpoint | Correct | Faithful | Citations supported | Context tokens | Prompt tokens |
|---|---:|---:|---:|---:|---:|
| Dense + LLMLingua-2 | 88.00% | 89.67% | 88.00% | 1,259.22 | 1,640.31 |
| IntentRoute + LLMLingua-2 | 91.00% | 93.33% | 88.33% | 1,175.02 | 1,529.32 |

For the primary paired comparison, IntentRoute+LLMLingua-2 versus
Dense+LLMLingua-2:

- context-token saving: 6.69%; actual prompt-token saving: 6.77%;
- correctness delta: +3.00 pp, 95% bootstrap CI [-1.00, +7.00] pp,
  exact McNemar p=0.1996;
- faithfulness delta: +3.67 pp, 95% CI [-0.33, +7.67] pp,
  exact McNemar p=0.1081;
- citation-support delta: +0.33 pp.

The point estimates follow the existing Sentence-MMR direction while using
fewer final-context tokens, but the correctness interval includes both a small
loss and a larger gain. This is not strict non-inferiority proof.

## Cross-Compressor Boundary

LLMLingua-2 actual text output exceeds the frozen Sentence-MMR target by about
1.5%, so it uses 1.57% more Dense context tokens and 1.52% more IntentRoute
context tokens than the corresponding Sentence-MMR endpoint. DeepSeek paired
correctness deltas are -1.00 pp for Dense and -0.33 pp for IntentRoute; both
confidence intervals include zero.

Actual prompt-token totals are about 36% lower for LLMLingua-2, but this is not
a pure compressor effect. Sentence-MMR emits many sentence units and therefore
incurs much more per-unit chunk/sentence header metadata, whereas LLMLingua-2
retains 9--10 chunk units. Matched `context_tokens` remain the primary
cross-compressor cost measure; prompt tokens are a secondary engineering
footprint.

## Current Boundary

- The completed DeepSeek result supports, but does not by itself finalize, the
  claim that IntentRoute's token/quality relationship persists under an
  official learned compressor.
- Task79 does not establish a geometry-to-compression causal path, and
  LLMLingua-2 does not validate route geometry.
- Independent GLM-5.2 and MiniMax-M3 judgments for the 600 new answers remain
  required before manuscript integration. Missing provider responses will not
  be imputed.
- The fixed external handoff contains 600 prompts to run once with each model,
  for 1,200 expected external responses.

## Validation

- Task79 local gate: 14/14 checks pass; status
  `PASS_LOCAL_GATE_EXTERNAL_JUDGES_PENDING`.
- Core regression tests: 139 pytest cases plus two standalone download-script
  tests, 141/141 pass.
- `.venv` and `.venv-rocm` both pass `pip check`.
- All Task79 scripts compile, the staging path is idempotent, and no API key or
  `.env` content appears in Task79 artifacts.
- The independent-judge gap is represented as 1,200 pending responses, not as
  a failed local experiment or imputed evidence.

## Artifacts

- `paper/experiments/results/task79_llmlingua2_preflight.{json,md}`
- `paper/experiments/results/task79_llmlingua2_segment_audit.{json,md}`
- `paper/experiments/results/task79_llmlingua2_matched_compressor/`
- `paper/experiments/results/task79_llmlingua2_downstream_evaluation/`
- `paper/experiments/results/task79_llmlingua2_multi_judge_analysis.*`
- `paper/experiments/reproducibility/task79/`
