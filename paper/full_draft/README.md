# IntentWeight Full Draft

Updated: 2026-05-31

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
- `figures/`: regenerable draft SVG figures and figure source data.

## Internal Evidence Sources

Use the experiment summaries under `paper/experiments/` when editing the full
draft. The most important internal evidence groups are:

- paper evidence package and consistency audit;
- review-defense revision plan;
- token-quality frontier and context-token analyses;
- clean component ablation table;
- LoTTE geometry scale validation.

## Claim Boundary

The paper should keep the bounded claim:

> IntentWeight is a feedback-guided evidence selection and context-budget
> controller for manifold-structured vertical-domain data, instantiated in a
> retrieval-augmented question-answering setting. It reduces final retrieved
> context tokens by about 4.7-5.3% on LoTTE technology/search 100k-638k while
> preserving dense-level $\mathrm{Hit@10}$. Mean $\mathrm{Hit@10}$ is above
> dense on 200k, 400k, and 638k, but the paper should not claim universal or
> statistically significant dominance, nor should it imply that the current
> experiments cover every possible knowledge-carrier format beyond the tested
> retrieval setting.
> Broader agent-memory, graph, tree, or tool-context applications should be
> framed as motivation and future work unless separately evaluated.

## Next Editing Pass

The current draft is a complete v1, not a final camera-ready paper. The next
pass should:

- add formal citations and BibTeX entries;
- normalize provisional citation keys into the target venue bibliography style;
- tighten prose to the target venue style;
- refine draft SVG figures to the selected venue's visual style;
- convert markdown tables into LaTeX once the venue template is chosen;
- convert selected appendix tables into LaTeX once the venue template is chosen.

## Math Style

Formula notation in this draft should use Markdown-compatible LaTeX syntax:
inline math with `$...$` and display math with `$$...$$`. This keeps equations
readable in Markdown while preserving a direct migration path to LaTeX.
