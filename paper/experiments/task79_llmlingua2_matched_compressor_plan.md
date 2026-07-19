# Task79 Official LLMLingua-2 Matched-Compressor Plan

Status: local formal compression and DeepSeek evaluation complete; GLM/MiniMax external judging pending

Date: 2026-07-18

## Scientific Question

Does the Dense-versus-IntentRoute answer-quality and final-context-cost
relationship persist when both source pools use the same official learned
token-level compressor?

This is a complementarity test. It does not test whether IntentRoute replaces
LLMLingua-2, and LLMLingua-2 output does not validate route geometry.

## Frozen Inputs

- Dataset: LoTTE technology/search 100k.
- Queries: the exact 300-query Task63 subset of the 417-query Task38 frozen
  test split. Query membership and order come from the tracked Task63
  `sample_records.jsonl`.
- Dense source pool: tracked MiniLM Dense top-10 contexts.
- IntentRoute source pool: the tracked Task38
  `task37_source:gated_cost_aware:seed19:token_budget_r0.95_m4` ranking.
- Existing endpoints and answers: Dense+Sentence-MMR and
  IntentRoute+Sentence-MMR at `r=0.85`, `lambda=0.70`.
- Answer generator and prompt contract: unchanged from Task63.
- Judge schema: unchanged from Task63/Task65.7.

No retrieval ranking, route controller, query split, existing answer, or
existing judgment is regenerated.

## Official Compressor Provenance

- Repository: `https://github.com/microsoft/LLMLingua`
- Repository commit: `e0e9d99beb94098bbd924aa53c2c112eac41c758`
- Package version at that commit: `0.2.2`
- Model: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`
- Model revision: `ebaba9b0e874dadd3003ffcff828e4397e568089`
- Code and model license: MIT
- Runtime: `.venv-rocm` on the local RX 9070 XT path.

The formal call uses official `compress_prompt_llmlingua2` token-level
compression with context-level filtering disabled. Source chunk order and
membership remain fixed. Newline and sentence punctuation use the official
force-token recommendation; digits are preserved. Chunk identifiers are
reattached as prompt metadata after text compression and are never passed
through the token classifier.

## Matched-Token Operating Point

The Task63 Sentence-MMR `r=0.85` endpoints are the quality-first operating
points frozen before Task79. For each query and each upstream source pool, the
LLMLingua-2 `target_token` is the exact tracked context-token count of the
corresponding Sentence-MMR endpoint:

- Dense+LLMLingua-2 target = Dense+Sentence-MMR tokens for the same query.
- IntentRoute+LLMLingua-2 target = IntentRoute+Sentence-MMR tokens for the same
  query.

This per-query rule is identical across upstream methods and is fixed before
any Task79 compressed answer or judgment exists. It uses no Task79 test label,
answer, judge output, or rate search. Actual output-token deviations caused by
the official compressor's discrete word threshold are reported rather than
silently post-processed.

## Four Endpoints

1. Dense+Sentence-MMR, existing fixed artifact.
2. IntentRoute+Sentence-MMR, existing fixed artifact.
3. Dense+LLMLingua-2, 300 new compressed contexts and answers.
4. IntentRoute+LLMLingua-2, 300 new compressed contexts and answers.

Only endpoints 3 and 4 generate new answers, for exactly 600 new answer calls.
Existing Sentence-MMR answers and judgments are copied byte-for-byte into the
Task79 result set.

## Primary Comparisons

- IntentRoute+LLMLingua-2 versus Dense+LLMLingua-2: primary route/compressor
  composition comparison.
- Dense+LLMLingua-2 versus Dense+Sentence-MMR: compressor comparison under the
  Dense source.
- IntentRoute+LLMLingua-2 versus IntentRoute+Sentence-MMR: compressor
  comparison under the IntentRoute source.
- IntentRoute+Sentence-MMR versus Dense+Sentence-MMR: fixed Task63 reference.

All comparisons preserve query pairing. Report actual context tokens,
target-token error, correctness, faithfulness, relevance, citation support,
paired bootstrap intervals, exact McNemar tests, judge agreement, compression
latency, and peak VRAM.

## Failure Categories

Qualitative review uses predeclared categories:

- answer-bearing evidence deletion;
- semantic or numeric drift;
- citation loss or unsupported citation;
- compressor truncation/empty output;
- upstream source-pool insufficiency;
- judge disagreement.

## Acceptance Rule

The result is integrated regardless of direction. No target-token policy is
changed after formal answer generation starts. A positive result supports
complementarity; equal improvement supports compressor independence; an
ordering reversal or quality loss is reported as an interaction boundary.
