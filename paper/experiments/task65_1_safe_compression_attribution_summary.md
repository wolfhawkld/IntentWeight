# Task65.1 Safe-Compression Attribution Summary

Task65.1 is complete.

## Protocol

The experiment exactly replays the Task37 LoTTE technology/search 100k
configuration with seeds `13,17,19` and exports final-epoch query traces. The
replay matches the original Hit@10, evidence recall, dense rate, route quality,
and candidate cost. On the same fixed top-10 source ranking, it compares learned
confidence, geometry similarity, shuffled confidence, a deterministic random
selector, and budget-only compression. Selector thresholds and budget actions
are selected on 179 calibration queries and frozen for 417 test queries.

## Result

Under the zero-drop calibration gate, budget-only `r0.95/m4` preserves mean test
Hit@10 while saving `6.18%` tokens. Learned confidence saves `11.05%` but loses
`0.88 pp`; random selection saves `11.86%` while losing `0.72 pp`. No selector
passes strict query-bootstrap non-inferiority on any seed.

For a fixed `r0.85/m4` action, mean safe-action AUROC is `0.432` for learned
confidence, `0.298` for geometry similarity, `0.531` for shuffled confidence,
and `0.524` for random selection. Only 7--10 unsafe examples occur per seed, so
intervals are wide and the audit is boundary evidence rather than proof of
inverse prediction.

## Paper Boundary

The direct confidence-conditioned evidence remains the conservative Task29
policy (`4.7-5.3%` saving). The stronger `6-18%` frontier must be attributed to
the confidence-gated evidence pool plus a separately calibrated length budget,
not to demonstrated per-query safe-compression discrimination by confidence or
geometry.
