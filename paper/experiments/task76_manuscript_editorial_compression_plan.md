# Task76 Manuscript Editorial Compression Plan

Status: completed 2026-07-16

## Objective

Reduce avoidable repetition in the canonical main manuscript without weakening
the geometry-guided, feedback-adaptive route-control thesis, deleting evidence,
or changing any experiment result. The target is approximately 10% from the
Task75 main-text baseline, driven by sentence-level consolidation rather than
by removing scientific detail.

## Baseline and Targets

| Canonical section | Task75 words | Target reduction |
|---|---:|---:|
| Abstract | 234 | 0--20 |
| Introduction | 1,447 | 120--180 |
| Related Work | 1,542 | 20--80 |
| Method | 2,268 | 150--250 |
| Experimental Setup | 2,293 | 200--300 |
| Results | 2,448 | 100--150 |
| Discussion | 1,793 | 300--400 |
| Limitations | 1,234 | 150--220 |
| Conclusion | 387 | 0 |
| **Total** | **13,646** | **940--1,300** |

The page count is an output measurement, not an editing target. No text will
be removed solely to force a specific number of pages.

## Content That Must Remain

- the bounded piecewise relevance-manifold motivation and its diagnostic,
  non-theorem status;
- the roles of geometry-defined arms, trust-weighted LinUCB feedback,
  Dense/BM25 rescue, and independently calibrated final-context budgeting;
- all main tables, figures, reported values, uncertainty statements, negative
  findings, and calibration/frozen-test distinctions;
- the separation between route quality, fused retrieval quality, and final
  evidence-context tokens;
- the nine-setting evidence hierarchy and the non-equivalence of those settings;
- the feedback, strict non-inferiority, answer-judge, domain-calibration, and
  direct confidence-to-compression boundaries;
- formulas, algorithm steps, protocol parameters, reproducibility details, and
  links to the supporting supplement;
- the measured input-token scope and the exclusion of unmeasured total-system
  cost, latency, memory, and energy.

## Editing Passes

1. Consolidate repeated result narration and claim boundaries in Introduction,
   Discussion, and Limitations.
2. Review duplicated protocol and method qualifications in Method,
   Experimental Setup, and Results. Preserve those sections unchanged if the
   first pass reaches the whole-manuscript target or further cuts reduce useful
   reproducibility detail.
3. Apply a light language pass to Abstract and Related Work if useful; do not
   further shorten the already compressed Conclusion.
4. Regenerate all derived Markdown/LaTeX artifacts and run full evidence,
   citation, terminology, PDF, anonymity, font, and artwork validation.

## Acceptance Criteria

- 9--12% total main-text reduction unless that range would remove evidence or
  impair readability;
- no changed numerical token, table row, citation key, formula, experiment
  claim, or evidentiary role;
- no new unsupported causal, universal, strict-non-inferiority, or total-cost
  statement;
- canonical Markdown, generated LaTeX, review packet, source manifest, and
  compiled journal PDFs remain synchronized and pass the repository audits.
