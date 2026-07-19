# Task79 Reproduction Contract

Task79 uses the official LLMLingua-2 implementation only in the optional ROCm
environment. The ordinary CPU experiments and manuscript build remain in
`.venv`.

## Fixed Components

- LLMLingua repository commit:
  `e0e9d99beb94098bbd924aa53c2c112eac41c758`
- Package version: `0.2.2`
- Model: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank`
- Model revision: `ebaba9b0e874dadd3003ffcff828e4397e568089`
- `model.safetensors`: `2,235,829,648` bytes
- Weight SHA256:
  `a33a153b2493bff6be06af6921e69de9c0d0bb6ff06fe5bbb68670ba8d980ae2`
- Complete seven-file model snapshot aggregate SHA256:
  `bc8ffa30f061337d5de7b7b247bab67b2e9967cab786804dfe9f7e0104dae871`
- Code and model license: MIT

The model cache, `.venv-rocm`, local ROCm installation, `.env`, and API keys are
machine-local and are not committed.

## Environment

Activate the existing WSL DXG/ROCm path before any command that imports the
ROCm PyTorch build:

```bash
source .venv-rocm/bin/activate-rocm
```

`requirements-rocm-lock.txt` records the exact successful environment. The
ROCm PyTorch wheel is platform-specific; reproduce it through the same ROCm
wheel channel before installing the remaining lock entries. The LLMLingua line
is pinned to the official Git commit rather than the temporary local clone used
during installation.

## Execution Order

```bash
python paper/experiments/scripts/task79_llmlingua2_preflight.py
python paper/experiments/scripts/task79_llmlingua2_segment_audit.py
python paper/experiments/scripts/task79_llmlingua2_matched_compressor.py
```

After local compression, return to `.venv` and stage the fixed Task63 artifacts:

```bash
python paper/experiments/scripts/task79_stage_downstream_evaluation.py
```

Answer generation is resumable and uses the unchanged Task63 prompt contract.
The offline Task79 analyzer must run only after the fixed 1,200 answers are
present; missing judge responses are reported and never imputed.

