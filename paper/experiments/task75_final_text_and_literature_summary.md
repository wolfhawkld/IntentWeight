# Task75 Final Text and Literature Closure Summary

Status: completed 2026-07-16

## Scope

Task75 closes the repository-controlled P0 text issues identified by the
pre-submission audit. It changes no method implementation, ranking, experiment
value, statistical result, or central geometry-guided and feedback-adaptive
route-control thesis.

## Manuscript Changes

- Replaced formal preregistration language with `prospectively specified` in
  the paper and `predeclared` in Task73/74 records. The protocol remains frozen
  before data download and outcome inspection, without claiming public
  immutable registration.
- Limited the monetary interpretation to the generation-stage evidence-input
  token component under a declared provider price. Total serving cost, latency,
  memory, energy, output tokens, retrieval, routing, and cache construction are
  explicitly outside the measured endpoint.
- Renamed the overstrong discussion heading to `Feedback Updates Route State
  under Controlled Credit` and aligned the text with the Task70/72 boundary:
  controlled adaptation and conditional recovery, not universal unseen-query
  or full-fusion superiority.
- Added primary-source positioning for R3AG, QuDAR, Budget-Aware Routing for
  Long Clinical Text, and RouteRAG. IntentRoute is positioned by its
  geometry-defined local arms, controlled repeated feedback, Dense/BM25 rescue,
  independent budget calibration, and route/fusion/context attribution rather
  than by a first-adaptive-RAG claim.
- Reduced the conclusion from 624 to 387 words while retaining the headline
  scale, backbone, answer-level, cross-domain, mechanism, and failure-boundary
  evidence.

## CAS Typography Correction

The final audit exposed a pre-existing font-stack defect: `cas-sc` loads STIX,
but the manuscript and supplement then loaded `lmodern`, leaving STIX math-slot
definitions mapped to incompatible Latin Modern fonts. The PDFs compiled, but
set membership, set delimiters, sums, and `@K` metric notation rendered
incorrectly and emitted `Missing character` messages.

Task75 removes the post-class `lmodern` load from the main manuscript and
supplement, keeps the CAS-native STIX stack, and makes missing-character output
a hard validation failure. The corrected package has:

- 26-page anonymous main manuscript;
- 15-page supplement;
- one-page title page;
- no missing mathematical glyphs;
- no Type 3 fonts;
- no undefined citations or references;
- no non-template overfull boxes.

## Validation

- Task75 terminology/literature audit: 44 files, four required 2026 citations,
  PASS.
- Canonical bibliography: 34 cited keys, 34 entries, zero uncited entries,
  PASS.
- Task73 source audit: 104/104 PASS; numerical results unchanged.
- Task74 integration audit: PASS.
- Task51 experiment artifacts: 921 PASS.
- Task43 manuscript tables/figures: 139/139 PASS.
- Task67 evidence audit: five main tables, two plotted-data files, and 482
  supplementary numeric values PASS.
- IP&M CAS package: compile, manifest, cross-reference, anonymity, artwork,
  font, and PDF validation PASS.

## Remaining Author-Owned Work

- final author-produced Figure 1 and editable source;
- author order, affiliations, ORCIDs, CRediT, funding, conflicts, and
  acknowledgements;
- public data/code archive URLs and license review;
- exact AI-use disclosure and submission-system metadata;
- independent human scientific and language review before release freeze.
