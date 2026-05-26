# Task33.5 LLM Generation Smoke Handoff

Updated: 2026-05-26

Task33.5 is a small downstream sanity check. It verifies whether Task29-C's
compressed retrieved context can still support LLM answer generation compared
with dense top-10 context.

This is not the main experiment. It is a smoke test for the reviewer question:

> If IntentWeight reduces final retrieved context tokens, does answer generation
> remain comparable to dense top-10?

## Script

`paper/experiments/scripts/task33_5_llm_generation_smoke.py`

The script:

1. loads LoTTE 100k corpus / queries;
2. loads dense top-10 rankings;
3. loads Task29-C rankings;
4. samples 60 queries by default;
5. builds paired dense and treatment contexts;
6. optionally calls an LLM to generate answers for both contexts;
7. optionally asks the same LLM to judge dense vs treatment using GT evidence;
8. writes JSONL results and a summary.

The default mode is dry-run. It prepares sample records and prompt previews
without calling any endpoint.

## Azure OpenAI Default Command

Use this on the Opus side after setting Azure credentials:

```bash
export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com"
export AZURE_OPENAI_API_KEY="YOUR_KEY"

.venv/bin/python paper/experiments/scripts/task33_5_llm_generation_smoke.py \
  --provider azure \
  --api-mode responses \
  --azure-endpoint "$AZURE_OPENAI_ENDPOINT" \
  --azure-api-version 2025-04-01-preview \
  --azure-deployment YOUR_GPT_5_1_DEPLOYMENT_NAME \
  --model gpt-5.1 \
  --sample-size 60 \
  --treatment-seed 13 \
  --top-k 10 \
  --temperature 0 \
  --max-output-tokens 512 \
  --reasoning-effort low \
  --output-dir paper/experiments/results/task33_5_llm_generation_smoke \
  --execute
```

If that Azure deployment only supports Chat Completions, switch:

```bash
  --api-mode chat-completions
```

For a no-cost request preview:

```bash
.venv/bin/python paper/experiments/scripts/task33_5_llm_generation_smoke.py \
  --provider azure \
  --azure-deployment YOUR_GPT_5_1_DEPLOYMENT_NAME \
  --sample-size 5 \
  --dry-run
```

## Important Parameters

- `--provider azure`: use Azure OpenAI style client.
- `--azure-endpoint`: Azure resource endpoint.
- `--azure-api-version`: defaults to `2025-04-01-preview`; adjust to the
  version enabled on the Azure resource if needed.
- `--azure-deployment`: Azure deployment name. This is usually not the raw
  model name.
- `--api-mode responses`: uses `client.responses.create`.
- `--api-mode chat-completions`: fallback if the Azure deployment exposes Chat
  Completions only.
- `--sample-size 60`: recommended smoke size. Use 20 first if checking cost.
- `--treatment-seed 13`: fixed Task29-C seed for the smoke. Keep this stable for
  reproducibility.
- `--temperature 0`: deterministic generation.
- `--max-output-tokens 512`: enough for short JSON answers and judgments.

## Outputs

Dry-run outputs:

- `sample_records.jsonl`: selected queries, GT ids, dense context, Task29-C
  context;
- `prompt_preview.jsonl`: first few prompts for inspection;
- `run_config.json`: exact command configuration.

Execution outputs:

- `llm_results.jsonl`: generation and judge outputs per query;
- `summary.json`: aggregate scores and winner counts;
- `summary.md`: compact markdown summary.

## Paper Interpretation

Positive result:

> On a small downstream generation smoke test, Task29-C compressed context
> preserves answer quality comparable to dense top-10 while using fewer
> retrieved context tokens.

Neutral or mixed result:

> The smoke test shows no catastrophic degradation, but full downstream answer
> evaluation remains future work.

Negative result:

> Retrieval-level token savings do not always translate into answer-level
> quality preservation; final generation-aware context selection should be
> treated as future work.

Do not overclaim this task. It is a sanity check, not the main evidence chain.
