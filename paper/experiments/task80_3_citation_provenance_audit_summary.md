# Task80.3 Citation Provenance Audit

Status: complete

Date: 2026-07-21

## Objective

Audit whether externally sourced datasets, retrieval components, embedding
backbones, clustering operations, and statistical procedures are cited where
they first enter the paper-facing argument. The goal is source traceability,
not a mechanical increase in citation density.

## Audit Finding

Before this revision, the bibliography contained 32 cited entries, but all
paper-facing citation commands were concentrated in Related Work. This was not
formally invalid, yet it left the Introduction, Method, and Experimental Setup
dependent on readers inferring provenance from a separate section.

After the revision:

- the bibliography contains 50 entries and every entry is cited;
- every cited key resolves in both the venue-neutral and Elsevier CAS builds;
- citation groups are distributed across Introduction (3), Related Work (27),
  Method (5), and Experimental Setup (14);
- Results, Discussion, Limitations, and Conclusion remain primarily
  artifact-backed accounts of this study rather than literature surveys.

## Added Provenance

Primary or canonical sources were added for the following paper-facing facts:

- datasets and benchmark packaging: LoTTE/ColBERTv2, RAGBench, PubMedQA,
  Banking77, and CUAD;
- representation backbones: Sentence-BERT, MiniLM, BGE, and E5;
- corpus and routing operations: KMeans, MiniBatchKMeans, PCA, BM25, dense
  retrieval, reciprocal-rank fusion, and LinUCB;
- comparison methods: maximal marginal relevance and BERT cross-encoder
  reranking;
- evaluation procedures: nDCG, bootstrap confidence intervals, McNemar's test,
  and Cohen's kappa.

The CUAD record follows the NeurIPS Datasets and Benchmarks volume form. No page
range was invented for a source that does not publish one.

## Placement Rule

Citations were inserted at the first local statement that depends on external
work:

- Introduction cites the RAG and dense-retrieval foundations and identifies
  downstream reranking/compression as composable prior work;
- Method cites algorithms at their operational definition;
- Experimental Setup cites the exact dataset, encoder, baseline, and
  statistical-procedure provenance;
- Results and later interpretive sections cite external work only when they
  make an external comparison. Claims based on this project's artifacts are
  not disguised as literature-derived claims.

This avoids both failure modes: a bibliography isolated from the methods it
supports, and citation clutter around original experimental findings.

## Scientific Boundary

Task80.3 changes no experiment, metric, table value, figure datum, or claim.
The existing boundaries remain unchanged:

- geometry is a diagnostic and routing prior, not a proven causal compression
  selector;
- feedback is controlled simulation, not deployed-user RLHF;
- Dense remains the recall floor;
- Hit@10 means at least one ground-truth evidence hit, not complete evidence
  collection;
- savings refer to final evidence-context input tokens, not total system cost.

## Validation

- review-packet validation: PASS (`50/50` citation keys and BibTeX entries);
- venue-neutral LaTeX validation: PASS (`0` uncited bibliography entries);
- venue-neutral PDF audit: PASS (35 pages, `0` critical log lines);
- Elsevier CAS experiment validation: `921/921` PASS;
- table/figure artifact audit: `128/128` PASS;
- paper-evidence audit: PASS;
- Elsevier submission validation: PASS (27-page manuscript, 13-page
  supplement, one-page title file);
- `git diff --check`: PASS before task registration.

## Paper-Use Decision

Use the local citations now present in the manuscript. Do not add citations to
Results, Discussion, or Conclusion merely to make citation counts look more
uniform; add them only when a sentence genuinely imports an external fact,
method comparison, or interpretation.
