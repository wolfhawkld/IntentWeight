# Task77 Occam Display and Narrative Revision Summary

Status: completed 2026-07-17

## Scope

Task77 applies the approved Occam review to the submission-facing manuscript.
It removes duplicate displays and internal workflow prose, raises the
information density of the main evidence, and clarifies the causal boundary
between route control and final-context budgeting. No retrieval result,
experiment artifact, central thesis, negative result, or uncertainty boundary
was deleted.

## Main-Paper Changes

- Replaced the former six-point Figure 3 with a three-panel, source-generated
  figure connecting cross-scale geometry, geometry-versus-random routing, and
  arm-granularity/fallback behavior.
- Promoted the cross-dataset snapshot to main Table 4 as a 15-row evidence
  matrix covering LoTTE scales and domains, QA datasets, and boundary-only
  datasets. Heterogeneous datasets remain separate; no pooled effect is
  reported.
- Moved the five-row arm-count table to Supplementary Table S20 while retaining
  its controller trend in Figure 3 Panel C.
- Replaced implementation-oriented Table 1 labels with journal-facing policy
  descriptions while retaining exact parameters and provenance in prose.
- Consolidated the prequential protocol, Dense/evidence-completeness
  limitations, and repeated defensive qualifications without weakening the
  geometry-guided and feedback-adaptive IntentRoute thesis.

## Scientific Clarifications

- Paper-facing `semantic drift` is now the precisely defined
  `selected-arm centroid mismatch safeguard`; it is not temporal or
  distribution drift.
- Simulated feedback follows outcome observation and updates only future route
  state. It neither uses current-query labels nor directly determines the
  current query's context budget.
- The supported controller order is outcome, later route state, route
  selection/confidence/fallback, and independently calibrated budgeting.
- Geometry remains a reproducible local-route structure and diagnostic signal,
  not a theorem-level manifold proof or a direct compression-safety predictor.
- Dense remains the primary quality baseline, recall floor, and fallback. The
  token-quality frontier is attributed to the complete controller rather than
  to geometry or feedback alone.

## Baseline and Supplement Cleanup

- Related Work now motivates feedback through contextual-bandit, relevance,
  click, and implicit-feedback literature; the unnecessary RLHF analogy and
  its two unused bibliography entries were removed.
- Sentence-MMR remains the shared formal compressor. SelectiveContext-lite and
  the QA-tuned MiniLM-family display were removed from the submission-facing
  evidence set, but their historical code and artifacts were preserved.
- Official open-source LLMLingua-2 is identified as an untested strong learned
  compression baseline, not as completed evidence.
- Duplicate main/supplement tables, the historical fixed-top-10 correction
  display, and author-facing reporting guardrails were removed from the
  scientific supplement. Seed, judge, recovery, calibration, reranker,
  arm-count, mediation, protocol, and domain-expansion evidence was retained.
- Supplementary tables are now sequential S1-S23, down from 30 displays.

## Quantitative Outcome

| Item | Task77 result |
|---|---:|
| Canonical main-manuscript words | 11,925 |
| Reduction from Task75 baseline | 1,721 (12.61%) |
| CAS main manuscript | 25 pages |
| CAS supplement | 12 pages |
| CAS title page | 1 page |
| Main tables | 5 |
| Supplementary tables | 23 |
| Main Table 4 evidence rows | 15 |
| Figure 3 tracked data rows | 13 |
| Figure 3 physical size | 190 x 88 mm |
| Figure 3 minimum text size | 7 pt |

## Validation

- Task77 Occam revision audit: all checks PASS.
- Task43 table/figure source audit: 128/128 PASS.
- Task67 evidence audit: five main tables, two plotted-data files, and 392
  supplementary numeric values, PASS.
- Full-draft citation audit: 32 cited keys and 32 bibliography entries, PASS.
- Task75 terminology and literature audit: PASS.
- Task76 preservation audit: 11,925 words, 12.61% reduction, 52 required
  details, PASS with the earlier section-hash contract superseded by Task77.
- Core unit tests: 132 pytest cases plus two standalone download-script tests,
  134/134 PASS. The Task73 domain-expansion test contract now follows its
  Task77 move from Supplementary Table S30 to S23.
- ACL and CAS builds: PASS. CAS output has no disallowed overfull boxes,
  unresolved final citations/references, missing glyphs, or Type 3 fonts.

## Remaining Author-Owned or Optional Work

- Figure 1 remains an author-owned final artwork task; its specification,
  blueprint, Mermaid source, and placeholder now encode the corrected causal
  structure.
- LLMLingua-2 has not been run. It remains an optional high-value learned
  compression baseline rather than a prerequisite for the current evidence.
- Author metadata, CRediT roles, declarations, archive URLs, license review,
  exact AI-use disclosure, and independent human scientific/language review
  remain outside Task77.
