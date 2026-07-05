# Submission Review Checklist

Updated: 2026-07-05

## Claim Boundary

- [ ] Keep the central claim on adaptive evidence selection and final
  retrieved-context token control.
- [ ] Describe the geometry framing as a piecewise relevance-manifold
  assumption supported by diagnostics, not as theorem-level proof.
- [ ] State that the evaluated implementation is retrieval-backed QA over LoTTE
  technology/search, not every possible knowledge-carrier format.
- [ ] Keep dense retrieval visible as a strong baseline, recall floor, and
  fallback route.
- [ ] Avoid universal or statistically significant dense-dominance wording.

## Experimental Disclosure

- [ ] Disclose that feedback is controlled simulation derived from ground
  truth under noise and trust settings.
- [ ] Describe multi-epoch prequential adaptation as repeated simulated
  interaction, not IID held-out generalization.
- [ ] Keep query-level `Hit@10` separate from complete-evidence
  `EvidenceRecall@10`.
- [ ] Use final retrieved context tokens for the headline token-efficiency
  claim.
- [ ] Label source candidate cost and dense invocation rate as retrieval-stage
  diagnostics.

## Reviewer-Risk Disclosure

- [ ] Mention the limited three-seed scale-up diagnostics and the wider 400k
  token-saving interval.
- [ ] Mention the five-seed LoTTE 100k extension without claiming statistical
  superiority.
- [ ] Report the matched MiniLM, BGE-base, and E5-base comparisons against
  their own dense baselines.
- [ ] Keep the 300-query downstream evaluation framed as single-generator,
  three-model judge support rather than human evaluation.
- [ ] Keep PubMedQA and Banking77 as supporting evidence; keep eManual and CUAD
  as boundary cases.

## Venue Migration

- [x] Use Information Processing & Management as the primary target.
- [ ] Convert selected Markdown tables into LaTeX.
- [x] Separate complete supporting evidence into a standalone supplement.
- [ ] Normalize `references.bib` to the target bibliography style.
- [x] Size deterministic data figures at the 190 mm Elsevier full-width target.
- [ ] Replace Figure 1 with author-produced vector artwork that follows the
  sizing and typography specification.
