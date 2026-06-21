# Task49 Strong-Baseline-Aware Manuscript Reframing

Date: 2026-06-21

## Goal

Task49 integrates the completed strong baseline evidence from Task46, Task47,
and Task48 into the paper narrative. The purpose is to make the manuscript
defensible against two reviewer-facing objections:

- Why not simply compress dense context?
- Why not simply add a cross-encoder reranker?

The revision does not add new experiments. It updates the paper-facing claim,
baseline framing, results interpretation, appendix evidence, and LaTeX build.

## Completed Changes

Updated Markdown source draft:

- `paper/full_draft/01_abstract.md`
- `paper/full_draft/02_introduction.md`
- `paper/full_draft/03_related_work.md`
- `paper/full_draft/05_experimental_setup.md`
- `paper/full_draft/06_results.md`
- `paper/full_draft/09_conclusion.md`
- `paper/full_draft/11_table_figure_plan.md`
- `paper/full_draft/12_appendix.md`
- `paper/full_draft/README.md`

Regenerated LaTeX sections under:

- `paper/latex/sections/`

## Main Reframing

The manuscript now treats the system as a layered pipeline:

1. candidate generation: dense, BM25, and cluster-local routes;
2. optional late ranking: cross-encoder reranking;
3. optional final-context compression: SentMMR;
4. route-and-budget control: IntentWeight.

The key claim is no longer that IntentWeight replaces compression or reranking.
The safer claim is:

> IntentWeight is a lightweight route-and-budget controller that is compatible
> with dense retrieval, cross-encoder reranking, and sentence-level context
> compression.

## Evidence Integrated

Task46:

- Dense+Sentence-MMR preserves dense chunk-support `Hit@10=0.8705` on LoTTE
  technology/search 100k.
- It reduces selected sentence tokens by about `11.4-13.1%`.
- This is now framed as a strong final-context compression baseline.

Task48:

- Applying SentMMR uniformly to dense and IntentWeight evidence pools preserves
  each source pool's chunk-support `Hit@10`.
- IntentWeight+SentMMR reaches larger total token savings because IntentWeight
  starts from a smaller evidence pool.
- This supports the shared-compressor plus upstream-controller framing.

Task47:

- Cross-encoder reranking over dense top-50 improves full top-10 support
  metrics from dense `Hit@10=0.8705` / `EvidenceRecall@10=0.7081` to
  `Hit@10=0.8777` / `EvidenceRecall@10=0.7332`.
- Full reranked top-10 increases final context tokens by about `21.9%`.
- Same-budget reranking does not uniformly dominate calibrated IntentWeight.

## Paper-Facing Outcome

The revised paper now has a stronger defensive position:

- dense retrieval remains the recall floor;
- SentMMR is a useful shared final-context compressor;
- cross-encoder reranking is a useful late ranking layer;
- IntentWeight is the controller that decides when compact evidence and smaller
  budgets are acceptable.

The manuscript should avoid dominance claims over compressors or rerankers.
It can instead claim that IntentWeight keeps the quality-cost frontier explicit
and remains compatible with these stronger post-retrieval components.

## Verification

Completed from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
make -C paper/latex audit
git diff --check
```

Final audit status:

- full draft validation: passed;
- LaTeX validation: passed;
- PDF audit: passed;
- compiled PDF pages: 27;
- critical LaTeX log lines: 0.

## Next Step

The next highest-value work is a venue-specific paper cut: reduce the 27-page
full draft into the target submission length while preserving the stronger
baseline framing. A larger answer-level evaluation remains useful but should
be scheduled separately because it requires a different cost and validation
plan.
