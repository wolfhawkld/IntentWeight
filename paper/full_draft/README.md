# IntentRoute Full Draft

Updated: 2026-06-28

This directory contains the first complete paper draft assembled after the
paper evidence package, pre-writing validation work, and review-defense
revision.

## Draft Files

- `00_title.md`: working title and short title options.
- `01_abstract.md`: paper abstract.
- `02_introduction.md`: motivation, hypothesis, contributions.
- `03_related_work.md`: related-work framework with provisional citation keys.
- `04_method.md`: IntentRoute method.
- `05_experimental_setup.md`: datasets, metrics, baselines, protocol.
- `06_results.md`: main results and ablations.
- `07_discussion.md`: interpretation and deployment meaning.
- `08_limitations.md`: limitations and future work.
- `09_conclusion.md`: conclusion.
- `10_reference_seed.md`: provisional citation keys and source links.
- `11_table_figure_plan.md`: main-paper versus appendix placement plan.
- `12_appendix.md`: paper-facing appendix draft with supporting diagnostics.
- `references.bib`: provisional BibTeX bibliography for the current draft.
- `figures/`: regenerable draft SVG figures and figure source data.
- `../latex/`: generated ACL-style LaTeX migration with PDF figure assets.

## Internal Evidence Sources

Use the experiment summaries under `paper/experiments/` when editing the full
draft. The most important internal evidence groups are:

- paper evidence package and consistency audit;
- review-defense revision plan;
- token-quality frontier and context-token analyses;
- clean component ablation table;
- LoTTE geometry scale validation;
- calibration/test context-budget validation;
- LoTTE science/search cross-domain validation;
- feedback-driven hard-case recovery;
- matched BGE/E5 backbone validation and BGE quality-first tunability;
- geometry/random, feedback/no-feedback, and arm-count controls;
- strong post-retrieval baselines: Dense+Sentence-MMR, compressor-normalized
  SentMMR, SelectiveContext-lite, and cross-encoder reranking;
- 300-query downstream answer-level evaluation.
- fixed-dense-pool factorial safe-compression attribution separating route
  confidence from the calibrated length budget.
- frozen-trajectory route mediation testing query-specific confidence-tier
  assignment against shuffled and fixed-route controls.
- independently calibrated Dense/IntentRoute matched frontiers and multi-split
  calibration sensitivity diagnostics.

## Claim Boundary

The paper should keep the bounded claim:

> IntentRoute is a route-control and budget-calibration controller instantiated in
> retrieval-augmented question answering. Local geometry defines reproducible
> route structure, trust-weighted LinUCB feedback adapts route confidence, and
> dense retrieval remains a recall floor. Under calibration/test budget selection, calibration-eligible
> operating points at 100k, 200k, and 638k reduce final LLM evidence-context
> input tokens by 6-18%; the 400k point is positive on frozen test but remains
> diagnostic pending follow-up calibration. The method avoids the larger
> $\mathrm{Hit@10}$ losses of dense-only adaptive truncation under these bounded
> operating points. A conservative confidence-only policy remains as a stable
> 4.7-5.3% saving baseline. The paper should not claim universal or
> statistically significant dominance, nor should it imply that the current
> experiments cover every possible knowledge-carrier format beyond the tested
> retrieval setting. BGE/E5 and the 300-query downstream run support
> backbone- and answer-level robustness without establishing significant answer
> improvement. Geometry is motivation and diagnostic support, not theorem-level
> proof. SentMMR and SelectiveContext-lite are downstream compressors,
> cross-encoder reranking is a late ranking layer, and IntentRoute can be
> composed with all three. Broader agent-memory, graph, tree,
> or tool-context applications should be framed as motivation and future work
> unless separately evaluated.

Cross-domain LoTTE science/search results support ranking-side generalization
while exposing domain-specific compression calibration, and simulated feedback
can recover a meaningful fraction of budget-induced tail failures in
post-feedback retry.

## Current Display Pass

Task65 reduced the main Results display from eight tables and five figures to
five tables and three figures. Detailed cross-domain, recovery, compressor,
reranker, and control results remain in the appendix. After adding the
Task65.3-65.5 reviewer-defense evidence, the regenerated ACL-style working PDF
is 30 pages with zero critical LaTeX warnings.

## Next Editing Pass

The current draft is a complete venue-neutral paper, not a final camera-ready
submission. Task66 should:

- use `paper/journal_submission/` as the journal-first preparation package;
- treat IP&M as the primary target and ESWA as the fallback target;
- migrate the current ACL-style LaTeX draft to Elsevier `elsarticle` before
  formal submission;
- tighten prose to the selected journal style;
- refine draft SVG figures to the selected venue's visual style;
- build separate anonymized manuscript and title-page files for double
  anonymized review;
- visually inspect table density, float placement, and page budget;
- fill real author, affiliation, funding, competing-interest, data/code, and
  AI-use declarations before submission.

## Draft Validation

Run the full-draft consistency check from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
```

## Review Packet

Build the venue-neutral independent-review packet from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_10_build_review_packet.py
```

The generated review entry point is `paper/review_packet/`.

## ACL-Style LaTeX Migration

Generate and statically validate the formal LaTeX migration from the repository
root:

```bash
.venv/bin/python paper/experiments/scripts/task36_12_migrate_latex.py
.venv/bin/python paper/experiments/scripts/task36_12_generate_latex_figures.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
```

The LaTeX entry point is `paper/latex/main.tex`. TinyTeX is installed in the
current WSL environment, so the ACL review PDF can be compiled and audited
locally:

```bash
make -C paper/latex audit
```

## Math Style

Formula notation in this draft should use Markdown-compatible LaTeX syntax:
inline math with `$...$` and display math with `$$...$$`. This keeps equations
readable in Markdown while preserving a direct migration path to LaTeX.
