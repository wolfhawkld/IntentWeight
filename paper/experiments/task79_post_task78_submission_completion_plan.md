# Task79 and Post-Task78 Submission Completion Plan

Status: planned

Date: 2026-07-17

## Current Baseline

The repository-controlled scientific and editorial work through Task77 is
complete at commit `c382c06`. The canonical manuscript contains 11,925 words;
the CAS package contains a 25-page main manuscript, a 12-page supplement, and a
one-page title page. Five main tables, 23 supplementary tables, and three main
figures are source-audited. The 921 experiment checks, 128 table/figure checks,
134 unit tests, citation audit, ACL build, and CAS submission audit pass.

The central claim is now bounded and stable: IntentRoute is a
geometry-guided, feedback-adaptive route controller with Dense/BM25 rescue and
independently calibrated final-context budgeting. Geometry and feedback improve
route control; neither is presented as a direct per-query compression-safety
oracle. No further ordinary dataset, seed, or embedding-backbone expansion is
planned by default.

## Ordering

1. Task79: formal LLMLingua-2 matched-compressor evaluation.
2. Task80: final evidence integration and submission-state reconciliation.
3. Task81: author-owned artwork, metadata, and declarations.
4. Task82: public reproducibility and license package.
5. Task83: independent review, final freeze, and submission package.

Task79 follows the Task78 reproduction and GPU revalidation gate. It is a high-value upper-bound
strengthening experiment, not a prerequisite for the validity of the current
paper. Tasks81 and 82 may proceed in parallel after Task79's display footprint
is known. Task83 is strictly last.

## Task79: Formal LLMLingua-2 Matched-Compressor Evaluation

Priority: P1, recommended before final freeze.

### Question

Does the Dense-versus-IntentRoute token-quality relationship persist when both
systems use the same official learned token-level compressor, rather than only
the deterministic Sentence-MMR compressor?

This task tests complementarity. It must not claim that IntentRoute replaces
LLMLingua-2, that LLMLingua-2 validates route geometry, or that retrieval
Hit@10 alone proves answer sufficiency after token-level compression.

### Preflight Gate

- Use the official open-source LLMLingua-2 implementation and record repository
  commit, model revision, license, tokenizer revision, and model checksum.
- Install it in `.venv-rocm` only when GPU inference is required; keep the
  ordinary experiment and document toolchain in `.venv`.
- Verify ROCm execution, deterministic output under fixed settings, exact token
  accounting with the existing tokenizer contract, peak VRAM, and wall time.
- Run a small fixed pilot to detect unsupported sequence lengths, truncation,
  malformed context, or AMD-specific incompatibility before any API calls.
- Keep API credentials only in ignored local environment files.

Failure of this gate is a documented compatibility boundary, not a reason to
substitute a weaker homemade compressor or silently change the evaluation
standard.

### Formal Design

- Reuse the exact 300-query subset of the 417-query frozen Task63 test split.
- Reuse the existing Dense and IntentRoute ranked evidence pools; do not rerun
  retrieval or retune the route controller.
- Compare four matched endpoints:
  Dense+Sentence-MMR, IntentRoute+Sentence-MMR, Dense+LLMLingua-2, and
  IntentRoute+LLMLingua-2.
- Reuse the two existing Sentence-MMR answer artifacts. Generate only the 600
  new LLMLingua-2 answers, using the same answer model and prompt contract.
- Judge the new answers with the same three-judge protocol used by Task65.7.
  Existing judgments remain fixed; rejected provider responses are reported,
  not imputed.
- Select compression settings only on a calibration partition. The frozen test
  labels, generated answers, and judge outputs must not guide target-rate
  selection.
- Report both a matched-token comparison and a quality-first calibrated point.
  Per-query target matching must be defined before the formal run and applied
  identically to Dense and IntentRoute.
- Preserve query-level pairing. Report context tokens, correctness,
  faithfulness, relevance, citation support, paired bootstrap confidence
  intervals, exact McNemar tests, judge agreement, latency, and peak VRAM.
- Include qualitative failure categories for evidence deletion, answer drift,
  citation loss, and compressor truncation.

### Acceptance and Reporting

- Integrate the result regardless of direction; do not search test-time target
  rates for a favorable point.
- Promote it to the main paper only if it materially changes the current
  compressor conclusion. Otherwise place the compact matched result in the
  supplement and mention it once in Results/Limitations.
- If LLMLingua-2 improves both methods similarly, report it as complementary
  evidence. If it changes their ordering, report the interaction explicitly.
- If the formal run is infeasible or unstable after the fixed preflight, retain
  Sentence-MMR as the completed baseline and document LLMLingua-2 as an
  unresolved implementation boundary.

## Task80: Evidence Integration and State Reconciliation

Priority: P0 after Task79.

- Integrate Task79 without expanding the central causal claim.
- Refresh all generated Markdown, ACL, and CAS packages and source manifests.
- Update stale Task67/checklist counts from the pre-Task77 state: 12 supplement
  pages, 23 supplementary tables, 11,925 canonical words, and Figure 3 at
  190 x 88 mm.
- Reconcile every task-status, paper-use, review-response, and readiness file
  against the final displayed evidence.
- Re-run the full experiment, provenance, citation, terminology, unit, PDF,
  artwork, and anonymity audit suite.
- Produce one authoritative remaining-work checklist; older task reports remain
  historical records and must not be treated as current submission state.

## Task81: Author-Owned Artwork, Metadata, and Declarations

Priority: P0 before submission.

- Replace the Figure 1 placeholder with an author-produced editable vector
  source and 190 mm PDF following `figure1_author_spec.md`.
- Verify minimum 7 pt finished lettering, embedded non-Type-3 fonts, no raster
  objects, no clipping, and correct 100% layout.
- Supply author order, affiliations, ORCIDs, corresponding-author details, and
  CRediT roles in the non-anonymized title-page workflow.
- Finalize funding, competing-interest, acknowledgements, data/code
  availability, and exact generative-AI disclosure statements.
- Keep all identity-bearing fields out of the anonymized manuscript and
  supplement.

Figure 1 remains human-authored. Repository tools may validate, convert, and
integrate it, but should not generate the submitted architecture artwork with a
generative-image model.

## Task82: Public Reproducibility and License Package

Priority: P0 before artifact release or submission when a repository link is
required.

- Build a clean release from tracked source, scripts, result summaries, figure
  data, environment lock files, model revisions, and checksums.
- Exclude `.env`, API keys, `.venv*`, ROCm machine state, local model caches,
  ignored Task69/70 caches, raw restricted data, and absolute machine paths.
- Audit dataset, model, generated-answer, judge-output, and included-text
  licenses. Publish download scripts and source revisions instead of raw data
  where redistribution is not permitted.
- Decide blinded-review artifact handling and preprint timing before exposing
  identity-bearing GitHub or archive links.
- Create an immutable archive/DOI only after the public payload and anonymity
  strategy are approved.

## Task83: Independent Review and Final Freeze

Priority: final P0 gate.

- Obtain an independent domain-expert scientific review and a native-level
  English/layout review; resolve findings in a tracked response ledger.
- Strongly consider a small stratified human correctness/faithfulness/citation
  audit. It raises the answer-level evidence ceiling but does not replace the
  existing multi-judge analysis.
- Run the complete cold final build and visually inspect every main and
  supplementary page at 100% size.
- Verify author anonymity, PDF metadata, archive links, declarations,
  submission-system fields, and file naming.
- Freeze checksums, create the release tag, and record the exact submitted
  commit and artifact versions.

## Deferred Unless New Evidence Requires Them

- More LoTTE domains, ordinary QA datasets, seeds, or embedding backbones.
- Real-user or non-stationary feedback studies.
- Full cold-start systems profiling across hardware platforms.
- New rerankers or route algorithms.

These may support a later extension or reviewer response, but currently have
lower marginal value than the learned-compressor comparison, author-owned
submission assets, release hygiene, and independent review.

## Completion Definition

The project is submission-ready only when Tasks80-83 are complete and Task79 is
either completed or closed with a documented preflight/decision outcome. The
current manuscript remains scientifically usable while Task79 is pending; no
central claim depends on a favorable LLMLingua-2 result.
