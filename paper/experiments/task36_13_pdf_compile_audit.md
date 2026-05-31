# Task36.13 PDF Compile And Layout Audit

Updated: 2026-05-31

## Purpose

Compile the ACL review-mode LaTeX migration locally, resolve real TeX
dependencies and errors, and inspect the generated PDF before submission-cut
editing.

## Lightweight TeX Environment

TinyTeX was installed into the user home directory:

```bash
curl -sL "https://yihui.org/tinytex/install-unx.sh" | sh
```

Default TinyTeX size after the required additions:

```text
202M  ~/.TinyTeX
```

The ACL review draft required four incremental packages:

```bash
tlmgr install lineno caption microtype upquote
```

## Compile Fixes

Real PDF compilation exposed issues that static validation could not detect:

- removed a duplicate `\bibliographystyle{acl_natbib}` declaration because
  `acl.sty` already configures it;
- changed migrated inline code from unbreakable `\texttt{...}` to breakable
  `\nolinkurl{...}` for long model identifiers;
- split two wide geometry diagnostic equations with `aligned`;
- corrected appendix heading migration so `D.1` becomes a `subsection` rather
  than a bookmark-level-skipping `subsubsection`.

## Build And Audit Commands

From `paper/latex/`:

```bash
make pdf
make audit
```

The optional audit renderer uses:

```bash
../../.venv/bin/python -m pip install -r audit-requirements.txt
```

## Compile Result

```text
Output written on main.pdf (19 pages, 345574 bytes).
critical_log_lines=0
pdf_audit=passed
```

All citations and cross-references resolve. The final compile log has no
`Overfull \hbox`, unresolved citation, unresolved reference, or fatal-error
lines. Remaining `Underfull` warnings are nonfatal and should be reconsidered
during the submission cut.

## Visual Audit

All 19 pages render as nonblank pages. The three paper figures are visible and
the appendix tables render correctly.

Page-budget observations:

- body text continues into page 14;
- `References` starts partway through page 14;
- appendix A starts near the end of page 15;
- appendix floating tables continue through page 19;
- pages 18 and 19 have visible whitespace because several appendix tables float
  after the appendix prose.

The compiled document is a correct complete draft, but it is not yet an
ACL-length submission cut. The next editing task must compress the main text
and move lower-priority detail into the appendix.

## Generated Audit Artifacts

The audit script writes temporary renderings under:

```text
/tmp/intentweight_pdf_audit/
```

These images are intentionally not committed.
