# Figure Enrichment and 3D Visualization Plan

Updated: 2026-07-05

This document evaluates how to enrich the code-generated figures without
changing the current manuscript claim or turning a diagnostic projection into
visual proof of a manifold. It is a design proposal only; no main-paper figure
should be replaced until the author approves the display set.

## 1. Current Figure Roles

The main manuscript currently has three figures:

1. **Figure 1:** system/controller architecture;
2. **Figure 2:** cross-scale final-context token saving and Hit@10 delta;
3. **Figure 3:** geometry-to-control cross-scale diagnostic.

Figure 1 is being redesigned separately. Figures 2 and 3 are valid and clean,
but they use relatively sparse aggregate displays. Their information density
can be increased with better 2D encodings before considering 3D.

## 2. Data Available for Richer Visuals

The repository already contains enough local data for deterministic,
publication-grade visualizations:

- 101,311 MiniLM, BGE, and E5 corpus embeddings for LoTTE technology 100k;
- 596 query embeddings per complete backbone;
- 64-dimensional controller context projections;
- 32-arm KMeans labels and centroids for seeds 13, 17, and 19;
- per-query route confidence, route tier, source hit, first-relevant rank,
  relevant-chunk counts, and safe-context headroom;
- 3,280-point calibration/frontier grids;
- 9,840 per-seed safe-compression operating points;
- risk-coverage curves, calibration metrics, arm-count controls, split
  sensitivity, and three-judge agreement data.

This means richer plots do not require a new retrieval or LLM experiment. They
require a carefully specified visualization pass and new source-data audits.

## 3. Is 3D Appropriate?

### 3.1 Embedding-space 3D: technically feasible, scientifically bounded

A deterministic exploratory PCA check was run on a fixed 20,000-point sample
with seed 13:

| Representation | Original dimension | Variance in PC1-PC2 | Variance in PC1-PC3 | Decision |
| --- | ---: | ---: | ---: | --- |
| Raw MiniLM corpus embedding | 384 | 8.32% | 11.92% | Do not use as a main-paper manifold picture. |
| Controller context projection | 64 | 12.68% | 18.20% | Possible supplementary projection diagnostic only. |

The third dimension adds visible information, but more than 80% of controller-
context variance still lies outside the first three principal components.
Therefore a 3D PCA plot must be captioned as a low-dimensional projection, not
as evidence that the corpus lies on a three-dimensional manifold.

### 3.2 Cross-scale 3D: not appropriate

The cross-scale geometry/outcome table has only six observations. Mapping
nearest-cluster hit, context retention, and token saving to three axes would
produce an attractive but statistically weak view whose rotation can visually
amplify any pattern. Keep these data in 2D small multiples.

### 3.3 Arm-count 3D: not appropriate

The arm-count study has five K values. A 3D line or surface would imply a
continuous response surface that was not measured. Use a log-K 2D line plot or
a paired slope display.

### 3.4 Frontier-grid 3D: possible but inferior to 2D contours

Task65.1/65.2 contain enough operating points for a surface over budget ratio,
coverage, and Hit loss/token saving. However, a static 3D surface hides points
and is difficult to compare at print size. Faceted 2D contours or Pareto curves
are more readable and more defensible.

## 4. Recommended Figure 2 Redesign

### Proposed title

**Frozen quality-context frontier across domains and corpus scales**

### Recommended two-panel layout

#### Panel A: Paired Pareto arrow map

- x-axis: final context-token saving versus dense top-10;
- y-axis: Hit@10 delta versus dense top-10;
- horizontal zero line: dense-equivalent mean Hit;
- each corpus scale has two points:
  - Dense truncation;
  - IntentRoute;
- connect each same-scale pair with a thin arrow from Dense truncation to
  IntentRoute;
- color encodes method, marker shape encodes domain, point label encodes scale;
- optional point area encodes `log10(corpus chunks)`.

This panel directly shows the paper's claim: IntentRoute usually gives up some
of Dense truncation's maximum saving in exchange for substantially better
retrieval quality. It is more informative than plotting saving and Hit delta
on separate panels against corpus size.

#### Panel B: Frozen-policy stability strip

Two acceptable options:

1. **interval forest plot:** per scale, show Hit-delta mean/CI and token-saving
   mean/CI on aligned axes;
2. **paired dumbbell:** compare IntentRoute and Dense truncation Hit loss for
   each scale, with saving printed as a compact right-side annotation.

Use the interval forest plot when all displayed intervals have a common,
clearly defined source. Use the dumbbell when avoiding mixed interval semantics.

### Rich dimensions without 3D

The Pareto map can display five variables while remaining readable:

- x: token saving;
- y: Hit delta;
- color: method;
- shape: domain;
- size: corpus scale;
- arrow: same-scale method contrast.

This is a better use of visual dimensions than a 3D axis.

## 5. Recommended Figure 3 Redesign

### Proposed title

**From local geometric structure to route-control behavior**

### Recommended three-panel evidence stack

#### Panel A: Cross-scale geometry profile

Use corpus chunks on a log x-axis and plot:

- nearest-cluster Hit@3;
- ContextRetention@10;
- PCA variance retained at 64 dimensions.

Use separate line styles for technology/search and science/search. If combining
metrics on one axis makes interpretation difficult, normalize only for display
and print the original value near each endpoint, or use three vertically
aligned mini-panels with a shared x-axis.

This panel shows that local-route coverage remains high while global projected
variance/retention changes with scale.

#### Panel B: Geometry versus random route control

Use grouped points or bars for:

- route reward;
- selected-cluster hit;
- final fused Hit@10.

Compare static-nearest geometry and uniform-random arms. Add 95% intervals when
available. The visual should emphasize the large route-level difference and
the small final fused difference, making dense/BM25 rescue visible rather than
hiding it.

#### Panel C: Arm granularity and fallback

Use log2(K) on the x-axis with two aligned lines or vertically stacked strips:

- learned route reward / selected-cluster hit;
- gated dense fallback rate;
- optionally gated final Hit delta as a lighter third series.

This panel connects geometry granularity to controller behavior without
claiming K=32 is a theoretical optimum.

### Why this is stronger than the current Figure 3

The current cross-scale scatter uses six points and can invite over-reading of
small-N correlations. The proposed composite presents three independent pieces
of evidence:

1. local structure exists at retrieval scale;
2. geometry is better than random at the route level;
3. arm granularity changes learned routing and dense fallback.

That sequence directly supports the bounded geometry-guided route-control
claim.

## 6. Optional Supplementary Geometry Figure

### Recommended format: 2D projections plus one small 3D inset

Use a deterministic sample of the 64-dimensional controller context, not raw
text embeddings. A three-part figure is preferable to one large 3D cloud:

1. **PC1-PC2 density projection** of sampled corpus contexts;
2. **PC1-PC3 projection** with 32 centroids and selected query points;
3. **small PC1-PC2-PC3 inset** for spatial orientation only.

Suggested visual encoding:

- corpus context: small light-gray points or density contours;
- centroids: numbered amber circles;
- queries: dark-blue stars;
- selected top-3 arms: colored centroid outlines;
- ground-truth chunks for selected queries: green diamonds;
- thin lines from query to selected centroids, not to every retrieved chunk.

Do not use 32 saturated cluster colors. Most corpus points should remain gray;
highlight only the arms relevant to the deterministic query examples.

### Query selection rule

Avoid hand-picked attractive examples. Predefine one of these rules:

- median route-confidence successful query;
- median-confidence fallback query;
- fixed query IDs selected before plotting;
- one representative from each route tier using the median within that tier.

Record query IDs, seed, artifact hash, sample indices, PCA fit scope, and
explained variance in the plot-data manifest.

### Caption boundary

Use wording such as:

> PCA projection of the 64-dimensional controller context for a deterministic
> sample. The view illustrates local arm neighborhoods and query-arm
> assignment; the first three PCs retain 18.2% of sampled variance and are not
> evidence of an intrinsically three-dimensional manifold.

### Better alternative to a static 3D cloud

Three orthogonal 2D projections are usually clearer in print than a single 3D
view because readers cannot rotate a PDF. A 3D inset is justified only as a
secondary orientation aid.

## 7. Other High-Value Supplementary Figures

### S2: Safe-compression risk-coverage curves

Source: Task65.2 `risk_coverage.csv` and discrimination tables.

- x-axis: coverage of compressed queries;
- y-axis: selective risk;
- one curve per selector;
- adjacent compact panel: AUROC/AUPRC/Brier/ECE forest plot.

This shows directly why route confidence is not claimed as a deterministic
compression-safety predictor.

### S3: Calibration/split sensitivity heatmap

Source: Task65.5 and Task65.6.

- rows: scale;
- columns: overlapping split or canonical fold;
- fill: test Hit delta;
- cell annotation: token saving;
- border/hatch: calibration eligibility.

This is more concise than multiple split tables and makes instability visible.

### S4: Multi-judge agreement and effect forest

Source: Task65.7.

- panel A: pairwise Cohen-kappa heatmap for correctness/faithfulness;
- panel B: correctness and faithfulness delta forest plot by comparison and
  judge;
- show majority result as a thicker marker;
- annotate missing MiniMax coverage rather than imputing it.

This would make the answer-level evidence easier to inspect than a wide table.

### S5: Dynamic route mediation

Source: Task65.3.

Use a paired stage plot rather than a Sankey diagram:

- rows: dynamic gated, fixed full, shuffled tiers, cluster-primary, dense;
- x-axis: Hit@10;
- connect source-stage to budgeted-stage values;
- point size or right-side label: token saving.

This preserves quantitative comparability and avoids decorative flow graphics.

## 8. 3D Production Constraints

If the optional 3D inset is produced:

- keep it supplementary, not the sole geometry evidence;
- use an orthographic projection where possible to reduce perspective
  distortion;
- display axis variance percentages;
- fix camera elevation/azimuth in code;
- use at most 2,000-3,000 sampled vector points to avoid a huge PDF;
- render points with sufficient opacity and no depth-shading that changes
  semantic color;
- retain text as embedded vector fonts;
- export a companion 2D projection using identical samples;
- document the artifact hash and random seed.

UMAP is not currently installed in `.venv`. Adding it is feasible, but UMAP can
visually create separated islands and is sensitive to neighborhood parameters.
PCA is preferable for the first paper-facing diagnostic because it is linear,
deterministic, and easier to audit. If UMAP is later added, it should be an
illustrative supplement with a parameter-sensitivity check, not the primary
manifold argument.

## 9. Recommended Priority

1. **Redesign Figure 2 as a paired 2D Pareto arrow map.** Highest immediate
   communication gain with no new experiment.
2. **Redesign Figure 3 as a three-panel geometry-to-control evidence stack.**
   Highest value for defending the central geometry-guided claim.
3. **Add the multi-judge forest/heatmap as a supplement.** Strong practical
   readability gain.
4. **Add split-sensitivity and risk-coverage supplemental figures.** Useful for
   defensive review and evidence compression.
5. **Prototype the PCA geometry projection last.** Use 2D orthogonal panels and
   only a small 3D inset if it materially improves interpretation.

## 10. Approval Gate Before Implementation

Changing Figure 2 or Figure 3 alters the main-paper display set and should be
approved before code changes. The recommended implementation sequence is:

1. generate low-resolution design previews from fixed CSV artifacts;
2. compare old and proposed figures at final 190 mm size;
3. approve the display semantics and captions;
4. generate final vector PDFs and source-data manifests;
5. extend Task67 evidence and artwork validation;
6. rebuild and visually inspect the full manuscript.
