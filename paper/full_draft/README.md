# IntentWeight Full Draft

Updated: 2026-06-11

This directory contains the first complete paper draft assembled after the
paper evidence package, pre-writing validation work, and review-defense
revision.

## Draft Files

- `00_title.md`: working title and short title options.
- `01_abstract.md`: paper abstract.
- `02_introduction.md`: motivation, hypothesis, contributions.
- `03_related_work.md`: related-work framework with provisional citation keys.
- `04_method.md`: IntentWeight method.
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
- LoTTE geometry scale validation.
- calibration/test context-budget validation;
- LoTTE science/search cross-domain validation;
- feedback-driven hard-case recovery.

## Claim Boundary

The paper should keep the bounded claim:

> IntentWeight is a feedback-guided evidence selection and context-budget
> controller motivated by a piecewise relevance-manifold assumption for
> vertical-domain data, instantiated in a retrieval-augmented question-answering
> setting. Under calibration/test budget selection, calibration-eligible
> operating points at 100k, 200k, and 638k reduce final LLM evidence-context
> input tokens by 6-18%; the 400k point is positive on frozen test but remains
> diagnostic pending follow-up calibration. The method avoids the larger
> $\mathrm{Hit@10}$ losses of dense-only adaptive truncation under these bounded
> operating points. A conservative confidence-only policy remains as a stable
> 4.7-5.3% saving baseline. The paper should not claim universal or
> statistically significant dominance, nor should it imply that the current
> experiments cover every possible knowledge-carrier format beyond the tested
> retrieval setting. Broader agent-memory, graph, tree, or tool-context
> applications should be framed as motivation and future work unless separately
> evaluated.

Cross-domain LoTTE science/search results support ranking-side generalization
while exposing domain-specific compression calibration, and simulated feedback
can recover a meaningful fraction of budget-induced tail failures in
post-feedback retry.

## Next Editing Pass

The current draft is a complete v1, not a final camera-ready paper. The next
pass should:

- tighten prose to the target venue style;
- refine draft SVG figures to the selected venue's visual style;
- compile the ACL-style LaTeX migration in TeX Live or Overleaf;
- visually inspect table density, float placement, and page budget;
- select a specific submission cycle before camera-ready formatting.

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
