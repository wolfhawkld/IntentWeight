# Task68 Multi-Dataset Narrative Alignment Summary

Updated: 2026-07-06

## Objective

Correct the manuscript-level impression that the study is based only on one
LoTTE setting. The revision presents all six domain-specific evaluation
settings while preserving their different evidentiary strengths.

## Evidence Hierarchy

1. **Full-stack evidence:** LoTTE technology/search supplies nested 100k-638k
   scale, matched baselines, calibrated context budgets, robustness controls,
   and downstream answer evaluation.
2. **Cross-domain evidence:** LoTTE science/search tests ranking and budget
   transfer at 20k and 100k corpus scales under domain-specific calibration.
3. **Mechanism-transfer evidence:** PubMedQA and Banking77 test trust-weighted
   feedback adaptation in biomedical evidence retrieval and intent routing.
4. **Boundary evidence:** eManual exposes duplicate-text and strict chunk-ID
   effects; the GT-anchored CUAD sample exposes sparse-label limitations.

The metrics from these settings are not pooled because the retrieval tasks,
ground-truth semantics, corpus scales, and protocol completeness differ.

## Manuscript Changes

- rewrote the abstract to 218 words and named the six domain-specific settings;
- expanded the introduction and contributions to state the tiered evidence
  design;
- strengthened the dataset protocol in Experimental Setup;
- promoted key PubMedQA, Banking77, eManual, and CUAD observations into the
  main Results section;
- added the multi-dataset interpretation to Discussion, Limitations, and
  Conclusion;
- extended the claim-to-artifact ledger with the secondary-dataset sources.

## Claim Boundary

The broader presentation does not claim six equivalent replications. The
6-18% final-context headline remains scoped to calibration-eligible LoTTE
technology/search operating points. Simulated feedback remains controlled
mechanism evidence, Banking77 remains an intent-routing proxy, and CUAD remains
a sampled legal stress case rather than full-corpus positive evidence.

## Validation

- full-draft structure, citation, and terminology validation: passed;
- source/display and experiment-artifact validation: passed;
- review-packet and LaTeX regeneration: passed;
- abstract length: 218 words, below the IP&M 250-word limit;
- remaining PDF blockers: pre-existing Figure 1 artwork and local Type 3 font
  environment only.
