# Task79 Official LLMLingua-2 Matched-Compressor Summary

Status: complete with full three-judge coverage for all four evaluated endpoints

Date: 2026-07-21

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

## Three-Judge Result

All 600 new answers are valid JSON. DeepSeek, GLM-5.2, and MiniMax-M3 each
provide 600/600 judgments for the two new LLMLingua-2 endpoints. Resumable
technical retries recovered outputs whose reasoning exhausted the initial
completion cap; failed attempts remain in the failure log and are not
interpreted as negative judgments. A protocol-identical retry recovered the
seven previously missing MiniMax-M3 Sentence-MMR judgments. Task79 therefore
has 300 complete query pairs for every judge and all four endpoints.

| Judge | Correctness delta | 95% CI | Faithfulness delta | Context-token saving |
|---|---:|---:|---:|---:|
| DeepSeek | +3.00 pp | [-1.00, +7.00] pp | +3.67 pp | 6.69% |
| GLM-5.2 | +0.67 pp | [-3.33, +4.67] pp | +0.33 pp | 6.69% |
| MiniMax-M3 | +0.00 pp | [-3.67, +4.00] pp | -1.33 pp | 6.69% |
| Three-judge majority | +0.67 pp | [-3.00, +4.33] pp | +0.00 pp | 6.69% |

For the primary paired comparison, IntentRoute+LLMLingua-2 uses 1,175.02 mean
context tokens versus 1,259.22 for Dense+LLMLingua-2. The paired 6.69% saving
has a 95% bootstrap interval of [4.32%, 9.03%]. Actual prompt-token saving is
6.77%. Across the three judges, correctness point estimates range from 0.00 to
+3.00 pp and every confidence interval includes zero. The majority estimate is
+0.67 pp with exact McNemar p=0.8642.

The cross-judge result supports persistence of the lower-context relationship
under an official learned compressor without a detected correctness loss. It
does not establish strict non-inferiority or significant answer improvement.

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

- The complete three-judge result supports the bounded claim that IntentRoute's
  token/quality relationship persists under an official learned compressor in
  this frozen 300-query setting.
- Task79 does not establish a geometry-to-compression causal path, and
  LLMLingua-2 does not validate route geometry.
- The finding is one-domain, one-generator, automated-judge evidence. It is not
  a human evaluation or a universal compressor result.
- All reused and new endpoints have complete three-judge coverage. Historical
  failed attempts remain available as retry provenance.

## Validation

- Task79 local gate: 14/14 checks pass; status `PASS_COMPLETE`.
- Core regression tests: 139 pytest cases plus two standalone download-script
  tests, 141/141 pass.
- `.venv` and `.venv-rocm` both pass `pip check`.
- All Task79 scripts compile, the staging path is idempotent, and no API key or
  `.env` content appears in Task79 artifacts.
- All four endpoints have 1,200/1,200 judgments from each judge; credentials
  are absent from all tracked artifacts.

## Artifacts

- `paper/experiments/results/task79_llmlingua2_preflight.{json,md}`
- `paper/experiments/results/task79_llmlingua2_segment_audit.{json,md}`
- `paper/experiments/results/task79_llmlingua2_matched_compressor/`
- `paper/experiments/results/task79_llmlingua2_downstream_evaluation/`
- `paper/experiments/results/task79_llmlingua2_multi_judge_analysis.*`
- `paper/experiments/reproducibility/task79/`
