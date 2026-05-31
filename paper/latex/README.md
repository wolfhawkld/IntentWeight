# IntentWeight ACL-Style LaTeX Draft

Updated: 2026-05-31

This directory contains the formal LaTeX migration of the paper-facing
Markdown draft. It uses the official ACL style files from
`acl-org/acl-style-files`.

## Source Of Truth

Edit chapters under `paper/full_draft/`, then regenerate the LaTeX migration.
The files under `paper/latex/sections/` and `paper/latex/references.bib` are
generated outputs.

## Generate And Validate

From the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_12_migrate_latex.py
.venv/bin/python paper/experiments/scripts/task36_12_generate_latex_figures.py
.venv/bin/python paper/experiments/scripts/task36_12_validate_latex.py
```

Or from this directory:

```bash
make validate
```

## Build PDF

Use a TeX Live environment with `latexmk`, `pdflatex`, and `bibtex`:

```bash
make pdf
```

The current WSL environment does not include a TeX toolchain, so repository
validation is static until the draft is compiled in TeX Live or Overleaf.

## Official ACL Style Files

- `acl.sty`
- `acl_natbib.bst`

Source: https://github.com/acl-org/acl-style-files
