# Journal Submission Prep

Updated: 2026-06-21

This directory tracks the journal-oriented submission package for the current
IntentRoute manuscript.

## Recommended Route

Primary target: Information Processing & Management (IP&M).

Reason: the paper is strongest as an information retrieval and RAG evidence
selection study at the intersection of computing and information science. The
current claim is about adaptive route control, final evidence-context token
budgeting, and strong retrieval baselines, which fits IP&M better than a pure
AI-system application framing.

Fallback target: Expert Systems with Applications (ESWA).

Reason: ESWA is viable if the paper is framed as an intelligent-system
engineering contribution for knowledge-augmented applications. It will require
clearer practical system guidance and careful avoidance of metaphor-heavy
method claims.

Stretch target: ACM TOIS.

Reason: TOIS is stronger and harder. It should be considered only after adding
more answer-level evaluation, deeper statistical evidence, or a more general
IR contribution beyond the current engineering frontier.

## Current State

- The manuscript has a complete venue-neutral full draft under
  `paper/full_draft/`.
- The current LaTeX build under `paper/latex/` is ACL-style and useful for
  review, but it is not the final Elsevier submission format.
- The abstract has been shortened to comply with the 250-word Elsevier abstract
  limit used by both IP&M and ESWA.
- The manuscript still needs an Elsevier `elsarticle` migration before formal
  submission.
- Author identity, affiliation, address, acknowledgements, and declarations are
  intentionally left as placeholders in this directory.

## Files

- `venue_fit.md`: target-journal fit, risks, and framing choices.
- `keywords.md`: 1-7 candidate keywords for Elsevier submission.
- `highlights.md`: short article highlights for submission metadata.
- `title_page_template.md`: separate non-anonymous title page template.
- `declarations.md`: funding, competing interest, data/code, and AI-use text.
- `cover_letter_ipm.md`: draft cover letter for IP&M.
- `submission_checklist.md`: double-anonymous and package readiness checklist.
- `task50_journal_prep_summary.md`: concise local record of this preparation
  pass.

## Next Required Work

1. Migrate the manuscript from ACL-style LaTeX to Elsevier `elsarticle`.
2. Produce separate title-page and anonymized-manuscript files.
3. Fill in real author, affiliation, corresponding-author, and declaration
   details.
4. Recheck references, figure files, table captions, and supplementary
   artifacts against the selected journal's upload system.
5. Decide whether to add a larger answer-level evaluation before first
   submission.
