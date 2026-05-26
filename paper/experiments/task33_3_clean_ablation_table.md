# Task33.3 Clean Ablation Table

Updated: 2026-05-26

Task33.3 converts the existing LoTTE 100k evidence into a compact
paper-facing ablation table. It does not introduce a new retrieval algorithm.
The purpose is attribution: identify which parts of IntentWeight provide the
quality floor, routing signal, feedback adaptation, and final token saving.

## Scope

All rows use the LoTTE technology/search 100k held-out test split with 596
queries and 101,311 corpus chunks. The main embedding model is
`sentence-transformers/all-MiniLM-L6-v2`.

Final context token metrics count only the retrieved chunk text placed into the
top-10 context. They do not include system prompts, generation output, reranker
internals, or retrieval-stage candidate counts.

## Clean Ablation Table

| Component | Role | Hit@10 | MRR@10 | nDCG@10 | Evidence recall@10 | Tokens@10 | Token ratio | Dense rate | LinUCB rate | Cluster hit | Last reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense-only | Quality floor / semantic baseline | 0.8674 | 0.7081 | 0.6487 | 0.7026 | 1472.39 | 1.0000 | - | - | - | - |
| BM25-only | Lexical baseline | 0.7232 | 0.5545 | 0.4768 | 0.5240 | 1745.12 | 1.1852 | - | - | - | - |
| Dense+BM25 hybrid | Static multi-route fusion | 0.8624 | 0.6973 | 0.6216 | 0.6848 | 1705.46 | 1.1583 | - | - | - | - |
| Static KMeans geometry | Geometry routing diagnostic | - | - | - | - | - | - | - | - | 0.8809 | - |
| No feedback gated routing | Dense/full fallback control | 0.8826 | 0.7106 | 0.6566 | 0.7246 | 1561.15 | 1.0603 | 1.0000 | 0.0000 | 0.1553 | 0.1516 |
| Equal noisy feedback | Noisy feedback without trust | 0.8641 | 0.7035 | 0.6143 | 0.6604 | 1423.84 | 0.9670 | 0.7480 | 0.2520 | 0.5979 | 0.7517 |
| Trust-weighted feedback | Trust scoring under default noise | 0.8641 | 0.7094 | 0.6212 | 0.6661 | 1399.51 | 0.9505 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Trust-weighted mild noise | Best controlled-noise feedback point | 0.8775 | 0.7130 | 0.6289 | 0.6795 | 1362.68 | 0.9255 | 0.5826 | 0.4174 | 0.7908 | 0.8820 |
| Task29-C final policy | Recommended conservative policy | 0.8652 | 0.7088 | 0.6251 | 0.6737 | 1401.24 | 0.9517 | 0.6708 | 0.3292 | 0.7223 | 0.8328 |
| Oracle feedback | Feedback upper bound | 0.8758 | 0.7149 | 0.6275 | 0.6768 | 1327.03 | 0.9013 | 0.4345 | 0.5655 | 0.8386 | 0.8932 |

CSV version:
`paper/experiments/results/task33_3_clean_ablation_table.csv`.

Seed-level context-token source table:
`paper/experiments/results/task33_3_clean_ablation_context_tokens.csv`.

## Component Attribution

Dense-only is the quality floor. It remains a strong baseline on LoTTE 100k,
with Hit@10 `0.8674` and context tokens normalized to `1.0000x`.

BM25-only is not competitive as a standalone retriever on this dataset. Its
Hit@10 is `0.7232`, and its final retrieved chunks are longer on average
(`1.1852x` dense tokens). Its role is therefore lexical coverage and route
diversity, not direct replacement of dense retrieval.

Static dense+BM25 hybrid is near dense in quality, but it does not solve the
cost problem by itself. It reaches Hit@10 `0.8624`, but token ratio is
`1.1583x`. This supports the design choice that static multi-route fusion alone
is insufficient; an adaptive controller and final context compaction are needed.

Static KMeans geometry provides routing signal rather than a complete ranking
policy. LoTTE 100k has nearest-cluster hit@3 `0.8809`,
context GT recall@10 `0.7836`, and context recall retention@10 `0.9033`.
This supports the piecewise relevance-manifold framing, but the geometry row
should not be compared as a standalone Hit@10 ranking method.

No-feedback gated routing is an important negative control. Its Hit@10 is high
(`0.8826`), but dense rate is `1.0000`, LinUCB primary rate is `0.0000`, and
selected-cluster hit is only `0.1553`. This means the quality comes from
dense/full fallback, not from self-evolution.

Equal noisy feedback demonstrates that feedback can start route learning, but
unweighted noisy feedback is weaker. Compared with no feedback, dense rate
falls from `1.0000` to `0.7480`, LinUCB primary rate rises to `0.2520`, and
selected-cluster hit rises to `0.5979`. However, Hit@10 falls slightly below
dense.

Trust-weighted feedback is the key self-evolution result under controlled
noise. Compared with equal noisy feedback, it keeps the same Hit@10 (`0.8641`)
while improving MRR@10, nDCG@10, selected-cluster hit (`0.5979` to `0.7223`),
last true reward (`0.7517` to `0.8328`), dense rate (`0.7480` to `0.6708`),
and final token ratio (`0.9670x` to `0.9505x`).

Trust-weighted mild noise shows the strongest controlled-noise operating point:
Hit@10 `0.8775`, token ratio `0.9255x`, selected-cluster hit `0.7908`, and
last true reward `0.8820`. This is the clearest row for arguing that cleaner
feedback and trust scoring can unlock higher-quality route learning.

Task29-C remains the recommended conservative paper policy because it is the
multi-scale configuration used by the main 100k-638k evidence chain. On 100k it
is near dense in Hit@10 (`-0.22` percentage points) while reducing final
context tokens to `0.9517x`. The Task33.2 trust-mild row is stronger on 100k,
but Task29-C has the broader scale-up evidence.

Oracle feedback is an upper bound, not a deployable baseline. It shows the
potential of cleaner feedback: Hit@10 `0.8758`, token ratio `0.9013x`, dense
rate `0.4345`, and selected-cluster hit `0.8386`.

## Paper-Facing Conclusion

Task33.3 supports a component-level story:

> Dense retrieval supplies the quality floor; BM25 and KMeans geometry add
> lexical and structural alternatives; LinUCB only becomes useful when feedback
> provides reliable credit; trust-weighting improves that credit assignment;
> final context compaction is the mechanism that converts adaptive routing into
> lower retrieved-context token cost.

This table also prevents overclaiming. IntentWeight should not be described as
BM25 plus clustering automatically beating dense. The defensible claim is that
feedback-driven adaptive routing plus conservative context compaction can
preserve near-dense quality while reducing final context tokens, and that better
feedback quality raises the policy-learning ceiling.

## Artifacts

- `paper/experiments/results/task33_3_clean_ablation_table.csv`
- `paper/experiments/results/task33_3_clean_ablation_context_tokens.csv`
- `paper/experiments/results/task33_3_clean_ablation_context_tokens.json`
- `paper/experiments/results/task33_3_clean_ablation_context_tokens.md`
- `paper/experiments/results/manifold_diagnostics_lotte_technology_search_100k.json`
