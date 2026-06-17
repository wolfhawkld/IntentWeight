# Human Validation Criteria

Updated: 2026-06-17

This document records the human-side validation criteria for turning the
IntentWeight research artifacts into a publishable paper. The goal is not to
replace human judgment with AI, but to define how AI and humans should divide
work efficiently.

The checklist keeps the original validation dimensions and expands them into a
small number of publication-oriented categories:

1. **claim and manuscript narrative**;
2. **experimental evidence and baseline fairness**;
3. **statistical and analytical rigor**;
4. **presentation, reproducibility, and artifact traceability**;
5. **human-AI workflow and final submission readiness**.

These five categories are intentionally broad. They should be enough to guide a
publishable-paper review without turning the process into an unbounded checklist.
If a new concern cannot fit into one of these categories, it is probably either
too specific for this document or should be treated as a concrete experiment
task elsewhere.

## 0. Validation Principle

AI can help draft, rewrite, compare, audit, and simulate reviewer objections.
Humans must decide whether the paper is scientifically valid, whether the claim
is properly bounded, and whether the final PDF is publishable.

A practical rule:

- AI proposes and checks;
- scripts verify data and build quality;
- humans approve claims, evidence, and final writing.

## 1. Manuscript Text

### 1.1 Claim Boundary

Human checks:

- Does the paper make a clear main claim?
- Is the claim supported by the strongest experimental result, not by the most
  attractive theory label?
- Does the paper avoid claiming that the method universally beats dense
  retrieval?
- Does the text clearly say when dense fallback or dense evidence remains
  necessary?
- Are mixed or negative cases explained instead of hidden?

For the current paper:

- The main claim should preserve the chain:
  **local geometric structure -> adaptive route selection -> feedback correction
  -> quality-efficiency trade-off**.
- Final-context budget control is the measurable efficiency endpoint, not the
  whole research contribution.
- The manifold/local-structure assumption should be used as the design
  hypothesis plus diagnostic support, not as a fully proven theory.
- LinUCB should be described as the adaptive route-confidence learner that
  operationalizes the trade-off, not as a new bandit algorithm.
- Feedback should be described as simulated or controlled feedback validation,
  not real production RLHF.

Failure signs:

- The title or abstract sounds broader than the experiments.
- The paper implies the method replaces dense retrieval in all settings.
- The paper reduces the contribution to cost optimization and loses the
  local-structure / feedback-adaptation research chain.
- The feedback claim sounds like real-user deployment evidence.

### 1.2 Section Role

Human checks:

- Does each section do what a standard paper section should do?
- Does the introduction motivate the problem before describing implementation?
- Does the related work explain what existing methods do and where this paper
  differs?
- Does the method section define the algorithm without task-log language?
- Does the experiment section focus on protocols, baselines, metrics, and
  evidence?
- Does the discussion section state limitations and boundary cases directly?

Failure signs:

- The paper still reads like a project progress log.
- Important experimental evidence appears only in the appendix.
- Section titles are implementation-specific when they should be conceptual.

### 1.3 Redundancy and Information Density

Human checks:

- Are repeated explanations removed or merged?
- Are all paragraphs necessary for the claim?
- Are high-level claims followed by concrete evidence?
- Are long background paragraphs shortened if they do not affect the argument?
- Are key results placed close to the claim they support?

Failure signs:

- The reader has to search across many pages to understand the contribution.
- The appendix contains essential evidence that should be in the main text.
- Tables and figures are referenced but not interpreted.

### 1.4 Language and Tone

Human checks:

- Is the wording precise and conservative?
- Are overclaims removed?
- Are terms used consistently, e.g. context budget, final context, route,
  candidate, token saving, calibration, feedback?
- Are limitations written as scientific boundaries, not as excuses?

Recommended wording style:

- Use "we observe", "we evaluate", "we find", "under this setting".
- Avoid "prove", "guarantee", "universally", "always", "solves".

## 2. Experiments and Evidence

### 2.1 Experimental Assumptions

Human checks:

- Are all baselines compared under consistent preprocessing?
- Are dataset scales, sampled/full settings, and calibration eligibility stated?
- Are train/calibration/test or simulation stages clearly separated?
- Are all metrics defined?
- Are reused artifacts, such as embeddings or BM25 rankings, clearly described
  as shared intermediate artifacts rather than reused final results?

For the current paper:

- `Hit@10` supports the claim that at least one useful evidence chunk is found.
- It does not prove complete evidence collection.
- Final-context token saving should be distinguished from source-corpus
  embedding cost.
- LLM input-token saving should be tied to the final context sent to the model.

### 2.2 Baseline Fairness

Human checks:

- Are dense, BM25, hybrid, and compression-style baselines clearly represented?
- Are baselines given reasonable budgets?
- Are comparisons made at matched or clearly explained context budgets?
- Are strong dense results acknowledged instead of downplayed?
- If a baseline is missing, is it listed as a planned experiment or limitation?

Important baseline risks:

- A reviewer may ask for dense with same-budget truncation or MMR.
- A reviewer may ask for reranker-based same-budget evidence selection.
- A reviewer may ask whether results hold under another embedding model.

### 2.3 Evidence Chain

Human checks:

- Does each major claim map to a table, figure, or artifact?
- Are the strongest results in the main paper?
- Are boundary cases placed in discussion or appendix with clear interpretation?
- Are all numbers traceable to generated CSV/JSON artifacts?
- Are paper tables generated from artifacts rather than manually copied?

Core evidence expected for this paper:

- retrieval quality against dense/hybrid baselines;
- final-context token reduction;
- LLM-answer sanity check showing no obvious answer-quality degradation;
- feedback recovery experiment for harmed or borderline queries;
- scale behavior on large LoTTE settings;
- geometry diagnostics as support for local-structure motivation.

### 2.4 Statistical Validity

Human checks:

- Are query-level comparisons used where possible?
- Are confidence intervals or paired tests included for headline numbers?
- Are seed-level results not over-interpreted?
- Are win/loss/tie or harmed/recovered cases analyzed?
- Are non-inferiority and superiority claims separated?

Useful checks:

- paired bootstrap for quality and token deltas;
- McNemar-style check for query-level hit differences;
- harmed-query recovery rate under feedback;
- confidence intervals for final-context token saving.

### 2.5 Feedback Evidence

Human checks:

- Is simulated feedback clearly labeled?
- Does the paper explain why simulation is acceptable for this stage?
- Does the reward design align with retrieval/context quality?
- Does feedback improve or recover performance on at least some affected cases?
- Does the paper avoid claiming production user behavior validation?

Recommended framing:

- Feedback validates adaptive correction potential.
- It does not replace future real-user studies.
- Recovery is conditional on context quality and feedback signal quality.

## 3. Presentation and Reproducibility

### 3.1 Figures

Human checks:

- Can every figure be understood without reading implementation logs?
- Are axes, legends, captions, and units clear?
- Are figures readable at 100% PDF zoom?
- Does each figure support a specific claim?
- Are multi-panel figures visually balanced?

Failure signs:

- A figure looks like an internal diagnostic rather than paper evidence.
- The caption says more than the plotted data supports.
- Domains, scales, or metrics are mixed without explanation.

### 3.2 Tables

Human checks:

- Are table fonts readable in the final PDF?
- Are wide tables placed as `table*` or split logically?
- Are columns grouped by purpose?
- Are all abbreviations defined?
- Are appendix tables placed near the text that discusses them?

Failure signs:

- Tables are compressed with tiny fonts.
- Many tables are dumped at the end of the appendix.
- Main tables contain too many task-specific labels.

### 3.3 Equations and Notation

Human checks:

- Are equations written in Markdown/LaTeX-compatible syntax?
- Are symbols defined before or immediately after use?
- Are formulas necessary for the paper's own method or metrics?
- Are standard formulas cited rather than re-derived unless needed?
- Is notation consistent across method and experiments?

For this paper:

- Include only formulas that clarify the method, metrics, reward, or token-cost
  calculation.
- Geometry formulas can be included when they help explain diagnostics, but they
  should not make the paper look more theoretical than the evidence supports.

### 3.4 References and Citations

Human checks:

- Does every related-work claim have a real citation?
- Are citations current enough for retrieval, RAG, reranking, contextual
  bandits, feedback optimization, and context compression?
- Are citations used to support the exact sentence where they appear?
- Are AI-assisted writing or simulated evaluation disclosures compatible with
  the target venue?

Failure signs:

- AI added citations that are real but not relevant.
- A method is compared rhetorically but not cited.
- Important baselines are mentioned only in review notes, not in the paper.

### 3.5 Build and Artifact Audit

Human checks:

- Does the LaTeX PDF build cleanly?
- Does the figure/table audit pass?
- Does every main number trace to a CSV/JSON artifact?
- Are generated artifacts and scripts organized enough for another researcher
  to inspect?
- Are private keys, private data, or machine-specific paths absent?

Recommended local checks:

```bash
.venv/bin/python paper/experiments/scripts/task43_audit_manuscript_tables_figures.py
make -C paper/latex audit
git diff --check
```

## 4. AI and Human Work Division

### 4.1 Work AI Should Do

AI is useful for:

- turning rough notes into structured paper text;
- rewriting task-log language into paper-facing language;
- checking claim consistency across abstract, introduction, results, and
  conclusion;
- generating candidate figure/table captions;
- scanning for missing baselines or reviewer objections;
- summarizing experimental artifacts;
- drafting rebuttal-style responses to likely criticisms;
- checking whether a paragraph overclaims relative to available evidence.

### 4.2 Work Scripts Should Do

Scripts should handle:

- metric computation;
- token counting;
- paired comparisons;
- confidence intervals where possible;
- figure/table data generation;
- LaTeX build audit;
- artifact traceability checks;
- deterministic regeneration of paper evidence.

### 4.3 Work Humans Must Do

Humans must decide:

- whether the main contribution is interesting enough;
- whether the claim boundary is honest;
- whether a baseline is fair;
- whether a negative result is a limitation or an invalidating flaw;
- whether the narrative is convincing to the target venue;
- whether the final PDF is readable and professionally presented;
- whether the paper is ready to submit.

### 4.4 Efficient Human-AI Writing Loop

Recommended loop:

1. Human states the intended claim and target venue.
2. AI checks whether current evidence supports the claim.
3. Scripts regenerate or audit the relevant numbers.
4. AI drafts or revises the corresponding section.
5. Human checks claim boundary, readability, and scientific validity.
6. AI simulates reviewer objections.
7. Human decides whether objections require new experiments or only clearer
   writing.
8. Scripts rebuild the PDF and audit figures/tables.
9. Human reads the final PDF at 100% zoom.

## 5. Final Readiness Gate

Before treating the manuscript as publishable, humans should be able to answer
"yes" to these questions:

1. Can the main claim be stated in one sentence?
2. Is that claim supported by main-paper evidence?
3. Are all caveats explicitly stated?
4. Are dense and other obvious baselines treated fairly?
5. Are token savings measured at the correct stage?
6. Are simulated feedback results clearly labeled?
7. Are weak datasets or boundary cases explained honestly?
8. Are all tables and figures readable at normal zoom?
9. Are all headline numbers traceable to artifacts?
10. Would the paper still be coherent if a reviewer challenges the manifold
    interpretation?

If any answer is "no", the paper needs either a writing revision, an additional
experiment, or a narrower claim.
