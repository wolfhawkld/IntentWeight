# IntentWeight Full Draft

Updated: 2026-05-28

This directory contains the first complete paper draft assembled after the
Task31 evidence package, Task33 validation work, and Task34 review-defense
revision.

## Draft Files

- `00_title.md`: working title and short title options.
- `01_abstract.md`: paper abstract.
- `02_introduction.md`: motivation, hypothesis, contributions.
- `03_related_work.md`: related-work skeleton with citation TODOs.
- `04_method.md`: IntentWeight method.
- `05_experimental_setup.md`: datasets, metrics, baselines, protocol.
- `06_results.md`: main results and ablations.
- `07_discussion.md`: interpretation and deployment meaning.
- `08_limitations.md`: limitations and future work.
- `09_conclusion.md`: conclusion.

## Source of Truth

Use the following evidence documents when editing the full draft:

- `paper/experiments/task31_paper_evidence_package.md`
- `paper/experiments/task33_7_pre_writing_consistency_audit.md`
- `paper/experiments/task34_review_defense_revision_plan.md`
- `paper/experiments/task29_2_token_quality_frontier.md`
- `paper/experiments/task33_3_clean_ablation_table.md`
- `paper/experiments/task30_lotte_geometry_scale_validation.md`

## Claim Boundary

The paper should keep the bounded claim:

> IntentWeight is a feedback-guided evidence selection and context-budget
> controller for manifold-structured vertical-domain data, instantiated in a
> retrieval-augmented question-answering setting. It reduces final retrieved
> context tokens by about 4.7-5.3% on LoTTE technology/search 100k-638k while
> preserving dense-level Hit@10. Mean Hit@10 is above dense on 200k, 400k, and
> 638k, but the paper should not claim universal or statistically significant
> dominance, nor should it imply that the current experiments cover every
> possible knowledge-carrier format beyond the tested retrieval setting.
> Broader agent-memory, graph, tree, or tool-context applications should be
> framed as motivation and future work unless separately evaluated.

## Next Editing Pass

The current draft is a complete v1, not a final camera-ready paper. The next
pass should:

- add formal citations and BibTeX entries;
- tighten prose to the target venue style;
- decide which tables go in the main paper versus appendix;
- convert markdown tables into LaTeX once the venue template is chosen;
- add figures for the system diagram, token-quality frontier, and geometry
  diagnostics.
