# Task36.2 Secondary Dataset Evidence

Updated: 2026-05-31

## Status

Complete. This task is a paper-writing integration task, not a new experiment.

## Purpose

The first full draft listed PubMedQA, Banking77, eManual, and CUAD in the
experimental setup but kept the Results section focused almost entirely on
LoTTE. Task36.2 adds a paper-facing secondary dataset section so that the
non-LoTTE datasets have an explicit role in the evidence chain.

## Files Updated

- `paper/full_draft/06_results.md`

## Evidence Roles

| Dataset | Role in paper | Main paper use |
|---|---|---|
| PubMedQA | Supporting proof-of-concept | Shows trust-weighted feedback improves policy internals near a dense ceiling. |
| Banking77 | Intent/domain routing proxy | Shows strong intent structure and feedback self-evolution; not evidence retrieval main claim. |
| eManual | Limitation case | Shows duplicate text and strict chunk-id labels can understate retrieval success. |
| CUAD | Sparse stress/smoke case | Shows sparse legal-domain limitation; not positive full-corpus evidence. |

## Key Guardrails

- Do not mix Banking77 with evidence-retrieval main tables; it is an intent
  proxy.
- Do not use CUAD as positive main evidence; it is GT-anchored sampled smoke.
- Do not interpret eManual strict chunk-id failure as proof that geometry is
  absent; duplicate evidence text is a major confounder.
- Keep LoTTE as the main large-scale evidence benchmark for the token-quality
  frontier.

## Paper-Facing Result

The Results section now includes a `Secondary Dataset Evidence` subsection.
It reports PubMedQA and Banking77 as supporting feedback-policy evidence, and
eManual/CUAD as boundary cases that limit overclaiming.
