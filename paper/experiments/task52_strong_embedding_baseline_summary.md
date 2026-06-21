# Task52 Strong Embedding Baseline Summary

Updated: 2026-06-22

## Objective

Test whether the current paper claim is robust to a stronger dense embedding
baseline. The immediate reviewer question is whether IntentWeight's frontier is
partly explained by using `sentence-transformers/all-MiniLM-L6-v2` as the dense
floor.

## Model And Runtime

- Strong dense model: `BAAI/bge-base-en-v1.5`
- Query instruction: `Represent this sentence for searching relevant passages: `
- Device: AMD Radeon RX 9070 XT via ROCm in `.venv-rocm`
- Corpus: LoTTE technology/search 100k, 101,311 chunks
- Query stream: 596 LoTTE technology/search queries
- Ranking depth: top-50
- First full embedding/ranking run elapsed time: 1273.344 seconds
- Embedding cache is now available under `paper/experiments/data/embeddings/`
  and should not be committed.

## Artifacts

- Dense metrics:
  `paper/experiments/results/task52_bge_base_100k_dense/dense_lotte_technology_search_100k_metrics.json`
- Dense rankings:
  `paper/experiments/results/task52_bge_base_100k_dense/dense_lotte_technology_search_100k_rankings.json`
- Held-out comparison:
  `paper/experiments/results/task52_bge_base_100k_strong_embedding.md`
- Paired statistics:
  `paper/experiments/results/task52_bge_base_100k_strong_embedding.paired.csv`

## Main Held-Out Result

Evaluation uses the same Task38 frozen held-out split: 417 queries selected by
the `task38_lotte_calibration_v1:100k` hash split.

| Method | Hit@10 | EvidenceRecall@10 | Avg context tokens@10 | Hit delta vs MiniLM | Hit delta vs BGE |
| --- | ---: | ---: | ---: | ---: | ---: |
| MiniLM dense | 0.8705 | 0.7081 | 1470 | +0.00 pp | -2.88 pp |
| BGE-base dense | 0.8993 | 0.7441 | 1708 | +2.88 pp | +0.00 pp |
| IntentWeight seed13 | 0.8681 | 0.6824 | 1376 | -0.24 pp | -3.12 pp |
| IntentWeight seed17 | 0.8657 | 0.6766 | 1365 | -0.48 pp | -3.36 pp |
| IntentWeight seed19 | 0.8777 | 0.6871 | 1397 | +0.72 pp | -2.16 pp |

Paired BGE-vs-MiniLM comparison:

- BGE improves Hit@10 by +2.88 pp.
- 95% bootstrap CI: +0.48 pp to +5.28 pp.
- McNemar p-value: 0.0357.
- BGE increases average final top-10 context tokens by 16.18% relative to
  MiniLM dense.

## Interpretation

BGE-base is a materially stronger dense floor on the Task38 held-out split.
This is useful because it directly addresses the strong-embedding reviewer
risk. It also tightens the paper claim: the current MiniLM-branch IntentWeight
policies remain token-saving relative to BGE dense, but they do not match BGE
dense quality on this split.

The correct conclusion is not that IntentWeight dominates stronger dense
retrieval. The defensible conclusion is:

- stronger dense retrieval improves quality but can increase final evidence
  context tokens;
- the existing IntentWeight controller still provides a lower-token operating
  point relative to both MiniLM dense and BGE dense;
- the next strong experiment should replace IntentWeight's dense branch with
  BGE and then rerun the route-and-budget comparison under the same Task51
  validation gate.

## Paper-Use Guidance

Do not use Task52 as a positive dominance claim. Use it as strong-baseline
evidence and as motivation for the next experiment:

1. dense retrieval strength matters;
2. final context cost remains a separate axis;
3. the route-and-budget controller should be retested with the stronger dense
   branch before making stronger journal claims.

The handoff plan is recorded in
`paper/experiments/task53_embedding_backbone_generalization_plan.md`: rerun
IntentWeight under the same embedding backbone as its dense baseline, first for
BGE and then for `intfloat/e5-base-v2`, so the paper can discuss
matched-backbone robustness rather than a MiniLM-specific comparison.
