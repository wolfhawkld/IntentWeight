# Figure 1 Author Production Specification

Updated: 2026-07-05

The current `figure1_system_diagram.pdf` is a non-final structural placeholder.
The final Figure 1 will be produced manually by the author; automated figure
generation must not overwrite it.

See `figure1_design_blueprint.md` for the recommended three-lane composition,
ready-to-use node text, arrow grammar, palette, and authoring workflow.

## Required Content

The final diagram must preserve the following method semantics:

1. query input and a PCA-projected query controller representation;
2. parallel global dense and BM25 recall routes;
3. geometry-defined cluster arms selected by LinUCB;
4. route confidence controlling route fusion and dense fallback;
5. rank fusion producing the evidence ranking;
6. independently calibrated final-context budgeting after rank fusion;
7. generator consumption of the budgeted evidence context;
8. controlled trust-weighted simulated feedback updating the LinUCB route
   policy for later queries;
9. no arrow implying that route confidence directly predicts per-query
   compression safety;
10. no arrow implying that LinUCB replaces the dense or BM25 recall routes.

## Artwork Requirements

- final format: vector PDF, with an editable author source retained locally;
- physical width: 190 mm full-width artwork at 100% scale;
- normal lettering: 7 pt or larger at final size;
- fonts: embedded Type 1 or TrueType; no Type 3 fonts;
- preferred font family: Arial/Helvetica, Times, Courier, or Symbol;
- line weights: 0.10-1.5 pt;
- color space: RGB with grayscale-distinguishable route groups;
- no title inside the artwork; the manuscript caption supplies the title;
- no clipping, overlapping text, crossing arrowheads, or content outside the
  PDF media box;
- filename: `figure1_system_diagram.pdf`.

## Delivery Location

Replace both synchronized assets only through the canonical publication
workflow:

```text
paper/latex/figures/figure1_system_diagram.pdf
paper/journal_submission/latex/figures/figure1_system_diagram.pdf
```

The Task66 builder copies the first path into the second. Therefore the author
normally needs to replace only the canonical `paper/latex/figures` file and
then run the submission build.

## Acceptance Checks

Task67 will verify physical dimensions, font type and embedding, minimum text
size where machine-readable, vector content, clipping, manuscript rendering,
and semantic agreement with the method section.
