# Task69.6 FinQA Feasibility Probe

Updated: 2026-07-07

## Status

Feasibility probe complete. Full common-protocol evaluation is deferred to the
GPU/overnight queue.

## Download And Preprocessing

FinQA was downloaded from RAGBench parquet splits and processed with the shared
RAGBench sentence-level preprocessing path.

| Split | Rows | Parquet size |
|---|---:|---:|
| train | 12,502 | 58.23 MB |
| validation | 1,766 | 5.67 MB |
| test | 2,294 | 8.52 MB |

The processed dataset validates successfully:

| Field | Value |
|---|---:|
| Corpus chunks | 196,659 |
| Queries | 16,562 |
| Queries with usable GT | 9,051 |
| GT query coverage | 54.65% |
| Missing GT references | 0 |
| Duplicate chunks | 0 |

## Decision

FinQA is useful as an optional finance-domain breadth row, but it is not a good
fit for a CPU interactive session. Its corpus size is close to the LoTTE 200k
setting, while its query count is far larger than the LoTTE runs used in the
current common-protocol matrix. Full Dense, BM25, hybrid, IntentRoute,
cross-fitted calibration, and recovery diagnostics should therefore run on GPU
or overnight infrastructure.

The current CPU contribution is limited to validated preprocessing and task
scoping. FinQA should not be cited as an experimental result until the common
protocol is completed.

## Artifacts

- `data/raw/finqa_train.parquet`
- `data/raw/finqa_validation.parquet`
- `data/raw/finqa_test.parquet`
- `data/processed/finqa_corpus.json`
- `data/processed/finqa_queries.json`
