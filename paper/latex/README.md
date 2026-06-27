# IntentRoute ACL-Style LaTeX Draft

Updated: 2026-06-27

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

## Lightweight TeX Environment

The current WSL environment uses TinyTeX, a lightweight TeX Live distribution:

```bash
curl -sL "https://yihui.org/tinytex/install-unx.sh" | sh
tlmgr install lineno caption microtype upquote sttools
```

TinyTeX installs into the user home directory and adds command links under
`~/bin`. The extra packages are the packages that were missing from the default
TinyTeX profile for this ACL-style draft. `sttools` provides `stfloats`, which
is used for safer two-column wide-table placement.

The current local reading build uses `\usepackage[preprint]{acl}` to remove
line numbers while retaining page numbers. Before formal anonymous review
submission, restore `\usepackage[review]{acl}` if the target venue requires
ACL review formatting.

## Build PDF

Build the PDF:

```bash
make pdf
```

The generated `main.pdf` and LaTeX intermediate files are intentionally
gitignored.

## Audit PDF

Install the optional rendering audit dependencies in the project virtual
environment:

```bash
../../.venv/bin/python -m pip install -r audit-requirements.txt
```

Then compile and render the PDF audit:

```bash
make audit
```

The audit checks page rendering, nonblank pages, references and appendix
locations, and critical LaTeX log warnings. Contact sheets are written under
`/tmp/intentroute_pdf_audit/`.

## Official ACL Style Files

- `acl.sty`
- `acl_natbib.bst`

Source: https://github.com/acl-org/acl-style-files
