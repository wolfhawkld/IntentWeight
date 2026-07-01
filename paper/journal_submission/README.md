# Journal Submission Prep

Updated: 2026-07-01

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
- The venue-neutral LaTeX build under `paper/latex/` remains available for
  independent review.
- Task66 provides a self-contained Elsevier CAS single-column package under
  `paper/journal_submission/latex/`, following the current IP&M template link.
- The anonymous manuscript uses CAS `doubleblind`, and the non-anonymous title
  page is a separate file.
- The abstract is 240 words, within the 250-word IP&M limit.
- Three cited vector-PDF figures, editable LaTeX tables, bibliography sources,
  highlights, keywords, and a source-hash manifest are included.
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
- `task66_elsevier_ipm_conversion_summary.md`: CAS conversion and validation
  record.
- `latex/anonymous_manuscript.tex`: double-anonymized CAS manuscript source.
- `latex/title_page.tex`: separate non-anonymous title-page template.
- `latex/Makefile`: reproducible `sync`, `all`, `validate`, and `audit` targets.

## Reproducible Build

The local build uses TinyTeX with the Elsevier CAS package and its table/float
dependencies:

```bash
tlmgr install els-cas-templates makecell xstring footmisc multirow colortbl moreverb wrapfig
cd paper/journal_submission/latex
make audit
```

All project Python entry points invoked by the Makefile use the repository
`.venv`.

## Next Required Work

1. Fill in real author, affiliation, corresponding-author, and declaration
   details.
2. Replace placeholder data/code availability text with release URLs.
3. Decide whether to post a preprint before or after journal review.
4. Recheck the current IP&M upload fields immediately before submission.

## Official Format Basis

Checked on 2026-07-01:

- [IP&M Guide for Authors](https://www.sciencedirect.com/journal/information-processing-and-management/publish/guide-for-authors):
  double-anonymized review, separate title page and anonymized manuscript,
  abstract up to 250 words, and 1-7 keywords;
- [Elsevier LaTeX instructions](https://www.elsevier.com/en-gb/researcher/author/policies-and-guidelines/latex-instructions):
  journal-specific link to the CAS single-column template;
- Elsevier CAS class used locally: `cas-sc` 2.4 (2024-05-04).

The old Task50 reference to `elsarticle` has therefore been superseded by the
current CAS single-column package.
