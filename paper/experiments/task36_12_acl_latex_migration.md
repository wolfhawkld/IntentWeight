# Task36.12 ACL-Style LaTeX Migration

Updated: 2026-05-31

## Purpose

Initialize a formal, modular LaTeX paper project from the paper-facing Markdown
draft while preserving the Markdown files as the readable source of truth.

## ACL Template Source

The migration vendors the official ACL style files from:

https://github.com/acl-org/acl-style-files

Vendored files:

- `paper/latex/acl.sty`
- `paper/latex/acl_natbib.bst`

SHA-256 checksums at migration time:

```text
19dfeddc2c0e448f3926a0bef048a9db3f3611b46265b760caabd7ada4f361de  acl.sty
e332fd51dcea48e2a8a89754892c3cb99674a1cd70b527b661e9aaffc235e83c  acl_natbib.bst
```

## Generated Project

Entry point:

```text
paper/latex/main.tex
```

The project contains:

- ACL review-mode document structure;
- modular generated chapter files under `paper/latex/sections/`;
- a synchronized `paper/latex/references.bib`;
- three `pdflatex`-compatible PDF figures;
- deterministic figure generation with PDF timestamp metadata removed;
- a `Makefile` for generation, validation, and PDF compilation;
- a static LaTeX validator for citations, labels, inputs, assets, and
  unconverted Markdown residue.

## Generation Commands

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_12_migrate_latex.py
.venv/bin/python paper/experiments/scripts/task36_12_generate_latex_figures.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
```

## Validation Result

```text
latex_inputs=10
citation_keys=26
bib_entries=26
uncited_bib_entries=0
cross_references=3
pdf_compile=skipped_no_tex_toolchain
latex_validation=passed
```

The current WSL environment does not contain `pdflatex`, `latexmk`, `bibtex`,
`xelatex`, or `lualatex`. Static validation passes, but PDF compilation and
visual page-budget inspection remain required in TeX Live or Overleaf.

## Source-Of-Truth Rule

Edit paper prose under `paper/full_draft/`, then regenerate the LaTeX sections.
Do not manually diverge generated files under `paper/latex/sections/` unless
the migration strategy is intentionally changed.
