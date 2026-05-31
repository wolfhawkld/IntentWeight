# Submission Review Checklist

Updated: 2026-05-31

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
- [ ] Mention the same-resource-class encoder robustness check and remaining
  stronger-encoder limitation.
- [ ] Keep the 60-query LLM generation result framed as a smoke test.
- [ ] Keep PubMedQA and Banking77 as supporting evidence; keep eManual and CUAD
  as boundary cases.

## Venue Migration

- [ ] Select the target venue and page budget.
- [ ] Convert selected Markdown tables into LaTeX.
- [ ] Convert appendix tables into the venue appendix format.
- [ ] Normalize `references.bib` to the target bibliography style.
- [ ] Review draft SVG figures and restyle them for the venue.
