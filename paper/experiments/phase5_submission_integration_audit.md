# Phase 5 Submission Integration Audit

Updated: 2026-07-13

## Scope

This audit closes the automated integration part of Phase 5. It checks claim
and manuscript narrative, experimental evidence and baseline fairness,
statistical and analytical rigor, and reproducibility/traceability against
`docs/human_validation_criteria.md`. It does not replace the author-owned
visual and submission review.

## Integrated P0 Evidence

| Required item | Paper-facing location | Audit result |
|---|---|---|
| Method/code alignment | Method Sections 3.5--3.9 | The text now limits LinUCB input to normalized PCA-projected query embeddings; route confidence/drift are separate gates; feedback reward has no unimplemented cost penalty; final context budgeting is separately calibrated. |
| Frozen unseen-query boundary | Results Section 5.3, Conclusion, Limitations Section 7.1, and Supplementary frozen-policy audit | The manuscript states that learned full routing does not exceed matched cold/static full controls on unseen queries and that learned gating is unsafe in the tested frozen first-pass setting. Feedback is bounded to controlled repeated-query adaptation and conditional recovery. |
| Current adaptive-retrieval and compression positioning | Related Work Sections 2.3 and 2.5 | SeaKR, LLM-Independent Adaptive RAG, AttnComp, and ACC-RAG are cited from primary 2025 sources. The contribution is positioned as route-control composition and evidence attribution, not first use of adaptive retrieval, bandits, or context budgets. |
| Statistical framing | Experimental Setup Section 4.7 and Limitations Section 7.5 | The `1pp` threshold is an engineering guardrail, not equivalence. Frozen and normalized five-fold conditions are primary evidence; mechanism, robustness, and boundary analyses are explicitly not pooled as IID replication. |
| Systems-claim boundary | Method, Results, Limitations, and Task71.2 paper-use status | Final-context input tokens are reported as the measured efficiency endpoint. The single-device Task71.2 timing profile is excluded from the manuscript, supplement, and any end-to-end latency, memory, throughput, energy, or total-cost claim. |
| Traceable displays and numerical evidence | Generated ACL/journal packages and paper-evidence validator | Five main tables, two figure-data artifacts, and 446 supplementary numeric values remain traceable to generated artifacts. |

## Automated Validation Record

Completed after the final abstract boundary update:

- full draft/BibTeX validation: passed (11 manuscript files, 30 citations, 30
  bibliography entries, no uncited bibliography entries);
- ACL LaTeX validation: passed (10 inputs and 37 resolved cross-references);
- ACL PDF build and visual audit: passed (35 pages; no critical log lines);
- journal-submission validation: passed (250-word abstract, 27-page manuscript,
  14-page supplement, and 37 display cross-references); all three journal PDF
  entry points were recompiled after synchronization;
- paper-evidence validation: passed (five main tables, two figure-data
  artifacts, and 446 supplementary numeric values); and
- `git diff --check`: passed.

The ACL build emits non-fatal underfull-box warnings. The CAS anonymous build
also emits one template-level overfull-box warning at `\maketitle`, where the
class draws its title/abstract separator. The rendered first page has no visible
text, table, or figure clipping. These are layout-quality items for the final
typography pass, not missing references, failed builds, or evidence errors.

## Remaining Author-Owned Submission Gate

The following are intentionally not marked complete by this automated audit:

1. Replace the structural Figure 1 placeholder with the author-produced vector
   PDF specified in `paper/full_draft/figures/figure1_author_spec.md`.
2. Fill author identities, affiliations, CRediT roles, funding, competing
   interests, acknowledgements, data/code availability, and final AI-use
   disclosure in the journal title page.
3. Perform a final human PDF read for narrative coherence, table/figure
   readability, journal fit, and claim approval.
4. Obtain an independent final review only after the final figure and metadata
   are frozen.

## Decision

The automated manuscript integration gate is complete. No further Task71.2
systems profiling is needed for the current claim boundary. Optional Task72
recurrent-feedback and Task73 domain-expansion studies remain research
strengthening work rather than submission blockers.
