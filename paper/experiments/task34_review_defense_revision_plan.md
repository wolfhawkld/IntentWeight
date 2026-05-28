# Task34 Review Defense Revision Plan

Updated: 2026-05-28

## Purpose

Task34 absorbs the useful points from the Opus academic review into the paper
draft and evidence handoff documents. It does not add new experiments. The goal
is to preempt likely reviewer objections through clearer wording, metric
guardrails, and limitation framing.

## Accepted Review Points

Task34 treats the following points as paper-writing requirements:

1. **400k CI variance.** The LoTTE 400k token-saving interval is wider than the
   other scales and should be acknowledged as seed-level routing/context-budget
   variance.
2. **Task29-C selection rationale.** Task29-C must be described as the
   conservative operating point on the Task29-A/B/C token-quality frontier, not
   as an arbitrary chosen configuration.
3. **Above-dense wording.** The paper should say mean Hit@10 is above dense on
   200k/400k/638k, while avoiding "statistically significant" language except
   where the CI supports it.
4. **Effective compaction rate.** Task29-C's `mid_k=10` retains the full top-10
   context. Only high-confidence `k=8` cases are true context compression.
5. **Multi-epoch disclosure.** Eight-epoch prequential adaptation should be
   disclosed as simulated repeated interaction over the query stream, not IID
   held-out generalization.
6. **Evidence-recall trade-off.** Context compaction optimizes query-level
   usable evidence under `Hit@10`; it can reduce `evidence_recall@10` compared
   with dense when all GT chunks must be recovered.

## Paper-Level Decisions

- Keep Task29-C as the main result because it prioritizes quality preservation
  over maximum token saving.
- Use "mean above dense" rather than "significantly exceeds dense" for
  200k/400k/638k.
- Treat 400k as directionally consistent but higher variance.
- Report effective compaction as the high-confidence compression rate, while
  describing mid-confidence as a safety tier.
- State that multi-epoch adaptation is a controlled simulation of repeated
  interactions. Each query is still ranked before its feedback is applied in
  that pass.
- Add an explicit limitation for complete-evidence tasks such as legal or
  medical review.

## Files Updated

- `paper/draft/abstract.md`
- `paper/draft/introduction.md`
- `paper/draft/method.md`
- `paper/draft/experiments.md`
- `paper/draft/limitations.md`
- `paper/draft/outline.md`
- `paper/draft/README.md`
- `paper/experiments/README.md`
- `paper/experiments/task29_2_token_quality_frontier.md`
- `paper/experiments/task31_paper_evidence_package.md`
- `paper/experiments/task33_7_pre_writing_consistency_audit.md`

## Non-Goals

- No additional 400k seeds are run in Task34.
- No new LLM generation experiments are run.
- No claims are upgraded beyond the existing bounded evidence chain.
