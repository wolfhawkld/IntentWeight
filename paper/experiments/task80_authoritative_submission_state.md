# Task80 Authoritative Submission State

Status: Task80 complete; repository-controlled state reconciled

Date: 2026-07-21

This is the sole current repository-controlled status snapshot. Older task,
review, and readiness reports remain historical records. Scientific claims
must still be read from the manuscript and source experiment artifacts.

## Claim Boundary

`local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`

Geometry is diagnostic rather than theorem-level proof; feedback is controlled
simulation rather than production RLHF; Dense remains a recall floor; and cost
means final evidence-context input tokens rather than total serving cost.

## Current Evidence Surface

- Dataset/domain settings: `9` across `8` domain areas.
- Cross-dataset display rows: `15`; no pooled effect.
- Main displays: `5` tables and `3` figures.
- Supplement: `23` tables.
- Canonical main-text whitespace word count: `12070`.
- CAS abstract: `245` words.

## Answer-Level State

- Task63: `2100` answers, `6272/6300` valid judgments, `2072` shared keys, `28` MiniMax failures not imputed.
- Task79: `1200` endpoint-answer records and `3600/3600` judgments; missing=`0`.
- LLMLingua-2 primary majority comparison: `6.69%` context saving, correctness delta `+0.67pp`; correctness CI crosses zero.
- Recovered Sentence-MMR comparison: `300` complete pairs; majority faithfulness delta `+3.67pp`, McNemar `p=0.0522`.

## Validation State

- Experiment artifact audit: `921` PASS, `0` WARN, `0` ERROR.
- Table/figure source audit: `128/128` PASS.
- Paper evidence audit: `PASS`; supplementary numeric values=`392`.
- Task79 local gate: `14/14`, status `PASS_COMPLETE`.

## Compiled Packages

| Package | Pages | Type 3 fonts |
|---|---:|---:|
| acl_complete_evidence | 34 | 0 |
| cas_anonymous_manuscript | 26 | 0 |
| cas_supplement | 13 | 0 |
| cas_title_page | 1 | 0 |

## Remaining Human/Release Work

- replace Figure 1 placeholder with author-produced editable vector artwork
- complete author identities, affiliations, ORCIDs, CRediT roles, and declarations
- audit redistribution licenses and prepare a blinded/public reproducibility package
- obtain independent scientific and English/layout review, then freeze the submission

## Machine-Readable Source

`paper/experiments/results/task80_authoritative_submission_state.json`
