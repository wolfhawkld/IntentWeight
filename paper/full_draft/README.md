# IntentRoute Full Draft

Updated: 2026-07-16

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
- `11_table_figure_plan.md`: main-paper versus supplementary placement plan.
- `12_appendix.md`: canonical supplementary-material source with supporting diagnostics.
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
- prospectively specified LoTTE recreation/search and writing/search 100k domain
  expansion;
- PubMedQA and CovidQA-RAG biomedical transfer evidence;
- Banking77 feedback-adaptation evidence;
- eManual duplicate-text analysis and CUAD sparse-GT boundary evidence;
- feedback-driven hard-case recovery;
- matched BGE/E5 backbone validation and BGE quality-first tunability;
- geometry/random, feedback/no-feedback, and arm-count controls;
- strong post-retrieval baselines: Dense+Sentence-MMR, compressor-normalized
  SentMMR, and cross-encoder reranking;
- 300-query, three-judge downstream answer-level evaluation.
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
> input tokens by 6-18%; the original 400k point is positive on frozen test but
> calibration-ineligible. A normalized five-fold follow-up yields 14.50% mean
> saving with no mean Hit change at 400k, while retaining policy instability
> and no strict seed-level non-inferiority. The method avoids the larger
> $\mathrm{Hit@10}$ losses of dense-only adaptive truncation under these bounded
> operating points. A conservative confidence-only policy remains as a stable
> 4.7-5.3% saving baseline. The paper should not claim universal or
> statistically significant dominance, nor should it imply that the current
> experiments cover every possible knowledge-carrier format beyond the tested
> retrieval setting. BGE/E5 and the 300-query, three-judge downstream run
> support bounded backbone and correctness robustness without establishing
> strict non-inferiority, uniform faithfulness preservation, or significant
> answer improvement. Geometry is motivation and diagnostic support, not theorem-level
> proof. SentMMR is a shared downstream compressor, cross-encoder reranking is
> a late ranking layer, and both are composable with IntentRoute. Official
> LLMLingua-2 compression remains untested. Broader agent-memory, graph, tree,
> or tool-context applications should be framed as motivation and future work
> unless separately evaluated.

Cross-domain LoTTE science/search results support ranking-side generalization
while exposing domain-specific compression calibration, and simulated feedback
can recover a meaningful fraction of budget-induced tail failures in
post-feedback retry.

The prospectively specified recreation/search and writing/search expansion adds matched
100k evidence of usable cluster-local route signal and heterogeneous calibrated
frontiers. Writing/search supplies a useful 10.09% saving point with a +0.12pp
mean Hit change, while recreation/search is a 5.42%/-0.76pp boundary and
trust-weighted calibration falls back to Dense in both. This evidence must not
be rewritten as universal strict non-inferiority or as a direct causal effect
of geometry on compression safety.

The complete evaluation spans nine dataset settings across eight domain areas. LoTTE
technology/search provides the full 100k-638k multi-scale quality-efficiency
evidence; science/search tests domain and scale transfer; recreation/search and
writing/search test matched 100k frontier heterogeneity;
PubMedQA and CovidQA-RAG test biomedical transfer; Banking77 tests mechanism
transfer; and eManual and CUAD expose data and evaluation boundaries. These
roles must remain visible but must not be pooled as equivalent replications.

## Current Display Pass

Task65 reduced the main Results display from eight tables and five figures to
five tables and three figures. Detailed cross-domain, recovery, compressor,
reranker, and control results remain in the separately compiled supplement.
After Task74, the complete ACL-style working PDF is 37 pages including
references and the evidence appendix, with zero critical LaTeX warnings. The
IP&M package separates the evidence appendix into a 15-page supplement. Task76
reduces the anonymous main manuscript from 26 to 25 pages by removing 10.53% of
repeated main-text wording without deleting evidence.

## Journal Submission Pass

Task66 is complete as the technical IP&M conversion. The current official
journal guidance points to Elsevier CAS single-column rather than the older
`elsarticle` plan. The self-contained package under
`paper/journal_submission/latex/` includes a CAS `doubleblind` manuscript,
separate one-page title page, three vector figures, editable tables, references,
highlights, keywords, and a reproducibility manifest.

Task67 completed the repository-controlled submission-readiness pass. Task68
aligned the abstract and main narrative with the pre-Task69 evidence
hierarchy; Task69.7 updates the paper-facing hierarchy to include the
CovidQA-RAG native-full biomedical transfer row.
Task74 integrates the Task73 recreation/search and writing/search
external-validity evidence without changing the five-table, three-figure main
display.
Task75 closes the remaining repository-controlled terminology, cost-scope, and
2026 literature issues, shortens the conclusion, and restores the CAS class's
native STIX font stack so mathematical symbols render correctly.
Task76 completes the full-manuscript editorial compression pass. It consolidates
Introduction, Discussion, and Limitations while leaving the evidence-dense
Abstract, Related Work, Method, Experimental Setup, Results, and Conclusion
unchanged from Task75 and preserving all automated evidence checks.
Human authors must still fill author identity, affiliations, CRediT roles,
funding, competing interests, acknowledgements, public data/code URLs, and the
final AI-use disclosure.

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
