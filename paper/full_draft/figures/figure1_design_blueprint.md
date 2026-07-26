# Figure 1 Design Blueprint

Updated: 2026-07-26

This document is a production concept for the author-created IntentRoute system
diagram. It complements `figure1_author_spec.md`: the author specification is
the acceptance contract, while this blueprint focuses on clarity, information
hierarchy, and visual composition.

## 1. Communication Goal

The reader should understand four points within five seconds:

1. IntentRoute retains global dense and BM25 recall rather than replacing them.
2. Geometry and feedback drive the LinUCB cluster-local route controller.
3. Route confidence controls route use and dense fallback.
4. Final-context budgeting is calibrated separately after rank fusion.

The figure should look like a systems/controller diagram, not a neural-network
architecture and not a causal graph claiming that geometry directly produces
token savings.

The final composition must also make two implementation boundaries explicit:

- the original query branches into the global Dense, lexical BM25, and
  controller paths; the PCA-projected context is used only by LinUCB and is not
  an input to Dense or BM25;
- simulated feedback is derived from an observed evidence outcome and updates
  the LinUCB arm state for later queries only; it is not a same-query loop from
  the generator.

## 2. Recommended Composition: Three Horizontal Lanes

Use a left-to-right online pipeline with two thinner supporting lanes. This is
the recommended option because it separates data flow from control and
adaptation while preserving one obvious reading direction.

```text
┌──────────────────────────── OFFLINE / CONTROL PLANE ────────────────────────────┐
│ Corpus chunks -> Embeddings + KMeans -> Fixed local arms (K=32)                 │
│                                      -> LinUCB arm state                         │
│ Calibration split -> Frozen budget policy (r,m) ---------------------------┐    │
└─────────────────────────────────────────────────────────────────────────────│────┘
                                                                              │
┌──────────────────────────── ONLINE DATA PLANE ───────────────────────────────│────┐
│         ┌-> Global dense: semantic recall floor ----------------------------┐│    │
│ Query ->├-> BM25: lexical anchors -----------------------------------------┼┤    │
│         └-> PCA context -> LinUCB selects arms -> Cluster-local dense ------┤│    │
│                              │                                               ││    │
│                  Confidence + centroid mismatch                              ││    │
│                  -> route gate / dense fallback ---------------------------->│    │
│                                                                              v    │
│            Weighted fusion -> Ranked R_t -> Final-context budget -> C_t -> LLM    │
└───────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────── FEEDBACK / ADAPTATION ────────────────────────────────┐
│ Evidence outcome -> simulated trust-weighted feedback -> LinUCB arm state         │
│                                       -- updates later queries only (t+1) ------┐ │
│                                                                                └─┘
└───────────────────────────────────────────────────────────────────────────────────┘
```

The ASCII layout indicates information hierarchy only. Do not reproduce its
box proportions literally.

## 3. Detailed Layout

### 3.1 Online data plane: dominant visual layer

Allocate about 62% of the figure height to this lane. It carries the main
left-to-right reading path and should use the strongest contrast.

Recommended node sequence:

1. **Query + session context**
2. Three aligned query branches:
   - **Global dense** — `semantic recall floor`
   - **BM25** — `lexical anchors`
   - **PCA query context -> LinUCB arm policy -> Cluster-local dense** —
     `select arms, then search selected arms`
3. **Confidence + centroid mismatch** — `route gate / dense fallback`
4. **Weighted rank fusion** — `dense + BM25 + local`
5. **Ranked evidence** — a short visual stack labeled `R_t`
6. **Calibrated final-context budget** — `frozen (r,m) policy`
7. **Budgeted evidence context** — a shorter stack labeled `C_t`
8. **LLM / downstream generator**

Dense and BM25 should enter rank fusion directly. The cluster-local card should
be preceded by the LinUCB selector or receive a clear control arrow from it.
This prevents the visual impression that LinUCB is itself a fourth retriever.

The query must split before the PCA node. Use the original query embedding for
the global Dense branch, the query text for BM25, and the corpus-fitted
PCA-projected context only for LinUCB. Do not place a generic `feature builder`
or PCA node upstream of all three routes.

### 3.2 Offline/control plane: geometry and calibration

Allocate about 20% of the height. Use a pale neutral background and a small
`OFFLINE / CONTROL` label.

Place two independent control chains in this lane:

- **Corpus chunks -> embeddings + KMeans -> fixed local arms (K=32)**
  - feed the fixed arms into both the LinUCB selector and the cluster-local
    search index;
- **Calibration queries -> policy selection -> frozen budget policy (r,m)**
  - feed this policy only into the final-context budget node.

The second chain is visually important. It demonstrates that the budget is
selected separately and must not be connected to route confidence.

### 3.3 Route controller: a compact control module

Place the controller immediately above or below the three route cards, centered
on the cluster-local route. It may be a two-part module:

- **LinUCB arm policy** — `score and select local arms`
- **Confidence + centroid mismatch** — `gate route use; keep dense fallback`

Use control arrows from this module to:

- the cluster-local dense route: `selected arms`;
- a small gate immediately before rank fusion: `route weights / fallback`.

Do not draw an arrow from route confidence to the final-context budget. If a
reader can visually trace such a path, the figure overstates the current
evidence.

### 3.4 Feedback/adaptation lane

Allocate about 18% of the height. Use a dashed return path and lower visual
weight than the online pipeline.

Recommended labels:

- **Outcome signal** — `observed evidence reward`
- **Trust weighting** — `weighted policy update`
- **Attribution** — `declared per result family`
- return label: **`updates later queries only`**

The return arrow should terminate at **LinUCB arm state**, not at the current
ranking, not at the generator, and not directly at the budget controller. A
small clock/next-query glyph can reinforce the prequential order without adding
another explanatory paragraph.

The feedback chain should originate from an evidence-outcome node associated
with retrieval evaluation, not from the LLM response box. This matches the
tested simulated-feedback protocol and avoids implying that real users or an
answer-level reward were observed in the reported experiments.

Optional, only if space remains: add a small side note beside feedback,
`optional safer retry / later-query fallback`. Keep this subordinate so it does
not look like the primary first-pass path.

## 4. Node Text: Ready-to-Use Copy

Keep node titles to one line and subtitles to one short line. The following
copy is recommended.

| Node | Title | Subtitle |
| --- | --- | --- |
| Input | Query + session context | current request |
| Controller features | PCA query context | LinUCB representation only |
| Dense | Global dense | semantic recall floor |
| Lexical | BM25 | lexical anchors |
| Geometry | Fixed local arms | KMeans, K=32 |
| Bandit | LinUCB arm policy | score and select local arms |
| Confidence | Confidence + centroid mismatch | gate route use; keep dense fallback |
| Local retrieval | Cluster-local dense | search selected arms |
| Fusion | Weighted rank fusion | dense + BM25 + local |
| Calibration | Frozen budget policy | selected on calibration queries |
| Budget | Final-context budget | ordered budgeted subset under (r,m) |
| Context | Budgeted evidence | generator input context |
| Generator | LLM / downstream agent | evidence-grounded response |
| Feedback | Simulated trust-weighted feedback | evidence reward; update q(t+1) route state |

Avoid placing formulas inside the figure except for compact symbols such as
`K=32`, `(r,m)`, and `τ`. Detailed equations belong in the method section.

## 5. Arrow Grammar

Use shape and line style consistently so the diagram remains understandable in
grayscale.

| Meaning | Style | Example |
| --- | --- | --- |
| Online evidence/data flow | solid dark line, filled arrowhead | query -> routes -> fusion -> context |
| Controller signal | thin blue or amber line, open arrowhead | LinUCB -> selected arms; confidence -> gate |
| Offline configuration | dotted purple/gray line | frozen policy -> final-context budget |
| Feedback update | dashed muted red line | outcome -> LinUCB state |

Include a compact three-item legend only if the styles are not self-evident.
Do not label every arrow; label only `selected arms`, `route weights/fallback`,
`frozen (r,m)`, and `later queries only`.

## 6. Color System

Use restrained colors with distinct lightness values. A suggested accessible
palette is:

| Semantic group | Stroke | Fill |
| --- | --- | --- |
| Input and global recall | `#2F6B9A` | `#EAF2F8` |
| Geometry and LinUCB | `#A66A16` | `#FFF4E5` |
| Fusion and evidence flow | `#287A6A` | `#EAF7F3` |
| Calibrated budget | `#6657A5` | `#F1EEFA` |
| Feedback/adaptation | `#A33D3D` | `#FCEBEC` |
| Offline containers and secondary text | `#667085` | `#F7F8FA` |

Use white or near-white as the page background. Avoid gradients, shadows,
glows, saturated rainbow palettes, and decorative icons. Meaning must remain
visible through lane position, node labels, and line style when printed in
grayscale.

## 7. Geometry, Spacing, and Typography

Recommended finished page size:

- width: exactly 190 mm;
- height: 86-92 mm; start with 190 x 90 mm;
- outer margin inside the PDF: 4-5 mm;
- lane gap: 3-4 mm;
- node corner radius: 1.5-2.0 mm;
- main flow line: 1.0-1.2 pt;
- control/feedback line: 0.8-1.0 pt;
- node title: 8.0-8.5 pt semibold;
- node subtitle: 7.0-7.3 pt regular;
- lane label and arrow annotation: 7.0 pt minimum.

Use one sans-serif family throughout. Arial or Helvetica is preferred;
Liberation Sans is a practical metrically compatible fallback. Avoid condensed
fonts, all-caps node titles, and text smaller than 7 pt.

Align route cards to a common grid. Use equal widths for dense, BM25, and
cluster-local cards. Keep at least 3 mm between text and box edges and at least
4 mm between parallel arrows.

## 8. Information-Rich Details That Do Not Add Clutter

The following small visual devices can increase information density safely:

- put `GLOBAL` badges on Dense and BM25 and a `LOCAL` badge on Cluster-local;
- show three small cluster cells inside the fixed-arm card rather than drawing
  all 32 arms;
- place a small shield/floor marker beside dense fallback, with the text
  `recall floor`;
- depict the output of fusion as a short ranked stack of chunks, then depict
  the budgeted context as a shorter stack;
- use a lock icon or `FROZEN` badge on the calibrated budget policy;
- use a small `t+1` marker on the feedback return arrow.

Use at most three of these devices. More than three will compete with the main
architecture.

## 9. What Not to Draw

- Do not connect route confidence directly to token ratio or context length.
- Do not route the global Dense or BM25 branches through the PCA controller
  context.
- Do not merge LinUCB and cluster-local dense search into one ambiguous box.
- Do not show dense as an optional weak baseline outside the system boundary.
- Do not route feedback into the same query's ranking.
- Do not originate the tested feedback path from the LLM response.
- Do not label simulated feedback simply as `user feedback` without a
  qualifier.
- Do not use `compact if safe`; the frozen policy controls the reported budget,
  and route confidence is not a validated per-query compression-safety
  predictor.
- Do not show geometry as a single global manifold proven by the method.
- Do not place experimental results, percentages, or ablation values in this
  architecture figure.
- Do not place the figure title or a long explanatory footer inside the PDF.

## 10. Alternative Composition

If the three-lane version feels too technical, use a simpler two-plane design:

- upper plane: **Route controller** containing geometry, LinUCB, confidence,
  and feedback state;
- lower plane: **Evidence pipeline** containing query, three routes, fusion,
  budget, context, and generator.

This alternative is visually cleaner but conveys offline calibration and
prequential timing less explicitly. It is preferable for a broad audience;
the three-lane version is preferable for IP&M reviewers because it makes the
claim boundaries inspectable.

## 11. Recommended Production Workflow

The safest final-size workflow is:

1. Draw in Inkscape on a page set to exactly `190 mm x 90 mm`.
2. Enable a 1 mm grid and build reusable node, badge, and arrow styles.
3. Complete a grayscale pass before adding color.
4. Check the figure at 100% size and at 50% zoom; every subtitle must remain
   legible at 100% print size.
5. Export directly to PDF without rasterizing text or converting text to paths.
6. Keep the editable SVG source locally.
7. Replace only `paper/latex/figures/figure1_system_diagram.pdf` and run the
   repository submission build; it synchronizes the journal copy.

PowerPoint, Figma, or diagrams.net can be used for an initial layout, but the
final page size and PDF font embedding should be normalized in Inkscape before
delivery.

## 12. Final Visual Review Questions

Before export, ask five people-independent questions:

1. Can the online path be followed without reading the caption?
2. Is dense visibly part of the method and the fallback quality floor?
3. Is LinUCB visibly selecting local arms rather than replacing retrieval?
4. Is the budget visibly separate from route confidence?
5. Does the dashed feedback path clearly update later queries only?

If any answer is no, simplify the arrows before adding more labels.

## 13. GPT-Image-2 Concept Mockup

The raster concept mockup generated on 2026-07-26 is:

`figure1_concept_gpt_image2.png`

It is a composition, hierarchy, and palette reference only. It is not a
submission asset and must not replace the author-created editable vector source.
The final artwork should correct any generated typography, spacing, arrow
alignment, or semantic ambiguity while preserving the architecture defined in
this blueprint and the acceptance contract in `figure1_author_spec.md`.

The mockup usefully demonstrates three visual devices that may be retained in
the manual vector version:

1. a compact cluster-cell motif for geometry-defined local arms;
2. a `RECALL FLOOR` badge on the global Dense route;
3. visibly longer and shorter evidence stacks before and after budgeting.

## 14. Reproducible Concept Prompt

The following prompt produced the 2026-07-26 concept mockup with the Codex
built-in `image_gen` tool backed by `gpt-image-2`.

```text
Use case: infographic-diagram
Asset type: visual concept mockup for a peer-reviewed journal's Figure 1 system architecture
Primary request: Create a clean, publication-style, ultra-wide scientific systems diagram for "IntentRoute", showing a geometry-guided and feedback-adaptive evidence-selection controller. This is a visual concept only, not final submitted artwork.
Scene/backdrop: pure white page, no title inside the artwork, three clearly separated horizontal lanes with very pale lane backgrounds.
Style/medium: flat vector-like editorial infographic, crisp geometric shapes, restrained professional academic design, no gradients, no shadows, no 3D, no neural-network decoration.
Composition/framing: ultra-wide landscape approximately 2.1:1. Main reading direction left to right. Top lane is thin and labeled exactly "OFFLINE SETUP & CALIBRATION". Middle lane is largest and labeled exactly "ONLINE EVIDENCE SELECTION". Bottom lane is thin and labeled exactly "PREQUENTIAL FEEDBACK". Use orthogonal connectors, generous whitespace, aligned boxes, and absolutely no crossing arrows.

Top lane:
On the left, show the exact sequence "Corpus chunks" -> "Embeddings + PCA + KMeans" -> "Geometry-defined local arms (K=32)". Inside the local-arms box, include a small abstract 2D cluster motif with four point clusters, with two clusters subtly highlighted.
On the right, independently show "Calibration queries" -> "FROZEN budget policy (r,m)", with a small lock badge. A purple dotted configuration arrow must descend only from this frozen policy to the "Final-context budget" box in the middle lane.

Middle lane:
At far left show "Query q_t". Split it into three parallel retrieval branches.
Top branch: blue box "Global dense", subtitle exactly "semantic recall floor", plus a small shield-like RECALL FLOOR badge.
Middle branch: blue box "BM25", subtitle exactly "lexical anchors".
Bottom branch: small amber box "PCA context x_t" -> amber box "LinUCB arm policy", subtitle exactly "select local arms" -> amber box "Cluster-local dense", subtitle exactly "search selected arms".
The geometry-defined local arms in the top lane send a thin amber control arrow to both "LinUCB arm policy" and "Cluster-local dense".
Below or immediately beside LinUCB, place a compact amber controller box "Confidence + centroid mismatch", subtitle exactly "gate route use; keep dense fallback". Send a thin amber control arrow from this box to "Route gate / dense fallback".
All three retrieval outputs flow into "Route gate / dense fallback", then into a green box "Weighted rank fusion".
After fusion, depict a vertical ranked stack of ten small document cards labeled "Ranked evidence R_t".
Then show a purple box "Final-context budget", subtitle exactly "ordered subset under frozen (r,m)".
After it, depict a visibly shorter stack of document cards labeled "Budgeted evidence C_t".
At far right show a small neutral gray box "LLM / downstream agent", subtitle exactly "evidence-grounded response".
Do not draw any arrow from route confidence to the final-context budget.

Bottom lane:
Show "Evidence outcome" -> "Simulated trust-weighted feedback" -> "LinUCB arm state theta_(t+1)".
Use a muted red dashed return path labeled exactly "updates later queries only" that returns to the LinUCB controller. Make it visually clear that feedback does not alter the current query. Do not originate feedback from the LLM output.

Arrow grammar:
Solid dark filled arrows = online evidence flow.
Thin amber open arrows = controller signals.
Purple dotted arrows = frozen offline configuration.
Muted red dashed arrows = later-query feedback update.

Color palette:
Blue strokes #2F6B9A, pale blue fill #EAF2F8 for query and global recall.
Amber strokes #A66A16, pale amber fill #FFF4E5 for geometry and LinUCB.
Green strokes #287A6A, pale green fill #EAF7F3 for fusion and evidence flow.
Purple strokes #6657A5, pale purple fill #F1EEFA for calibrated budget.
Muted red #A33D3D with pale red #FCEBEC for feedback.
Neutral gray #667085 and #F7F8FA for lane containers and downstream generator.

Typography: one clean sans-serif family, dark charcoal titles, small gray subtitles, high legibility, consistent capitalization.
Constraints: no percentages, no experimental scores, no embedding model names, no LLMLingua, no Sentence-MMR, no 3D manifold surface, no long footer, no figure number, no watermark. The architecture must make four boundaries immediately clear: Dense and BM25 remain global routes; LinUCB selects cluster-local arms; route confidence controls gating and fallback; final context budgeting is independently calibrated after fusion.
```
