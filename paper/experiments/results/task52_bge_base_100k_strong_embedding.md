# Task52 Strong Embedding Baseline

- Model: `BAAI/bge-base-en-v1.5`
- Query prefix: `Represent this sentence for searching relevant passages: `
- Scale: `100k`
- Evaluation split: Task38 frozen test split, `417` queries
- Corpus chunks: `101311`
- Dense ranking depth: `50`

## Summary

| method_label | seed | hit@10 | evidence_recall@10 | avg_context_tokens@10 | hit delta vs MiniLM | hit delta vs BGE | token saving vs MiniLM | token saving vs BGE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| minilm_dense |  | 0.8705 | 0.7081 | 1470 | +0.00 pp | -2.88 pp | 0.00% | 13.93% |
| bge_base_dense |  | 0.8993 | 0.7441 | 1708 | +2.88 pp | +0.00 pp | -16.18% | 0.00% |
| intentweight_target | 13 | 0.8681 | 0.6824 | 1376 | -0.24 pp | -3.12 pp | 6.43% | 19.46% |
| intentweight_target | 17 | 0.8657 | 0.6766 | 1365 | -0.48 pp | -3.36 pp | 7.14% | 20.07% |
| intentweight_target | 19 | 0.8777 | 0.6871 | 1397 | +0.72 pp | -2.16 pp | 4.98% | 18.22% |

## Paired Comparisons

| comparison | method_label | seed | method_hit@10 | baseline_hit@10 | hit_delta | CI low | CI high | token_saving | McNemar p |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bge_vs_minilm_dense | bge_base_dense |  | 0.8993 | 0.8705 | +2.88 pp | +0.48 pp | +5.28 pp | -16.18% | 0.0357 |
| vs_bge_dense | minilm_dense |  | 0.8705 | 0.8993 | -2.88 pp | -5.28 pp | -0.48 pp | 13.93% | 0.0357 |
| vs_bge_dense | intentweight_target | 13 | 0.8681 | 0.8993 | -3.12 pp | -5.76 pp | -0.72 pp | 19.46% | 0.02412 |
| vs_bge_dense | intentweight_target | 17 | 0.8657 | 0.8993 | -3.36 pp | -6.00 pp | -0.72 pp | 20.07% | 0.01612 |
| vs_bge_dense | intentweight_target | 19 | 0.8777 | 0.8993 | -2.16 pp | -4.80 pp | +0.48 pp | 18.22% | 0.1496 |

## Interpretation

- BGE-base raises the dense quality floor on the Task38 held-out split.
- BGE also selects longer chunks on average, so stronger dense retrieval is not automatically a final-context cost reduction.
- The current MiniLM-branch IntentWeight policies remain token-saving relative to BGE dense, but they do not match BGE dense quality on this split.
- This is a claim-tightening result: future strong-encoder experiments should test whether the IntentWeight controller still provides a useful token-quality frontier when its dense branch also uses BGE.
