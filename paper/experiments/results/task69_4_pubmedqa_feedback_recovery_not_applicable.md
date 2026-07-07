# Task69.4 PubMedQA Feedback Recovery Endpoint

PubMedQA has no feedback-recovery rate under the frozen five-fold common
protocol because all folds selected `dense_top10_fallback`. Therefore, there is
no compressed budget-induced harmed-query set to recover.

This endpoint is complete as a no-op safety result:

- dataset: `pubmedqa`;
- queries: `1000`;
- eligible IntentRoute folds: `0/5`;
- selected policy: `dense_top10_fallback` in all folds.

This should not be reported as positive feedback recovery evidence. It supports
the narrower claim that the selector can safely avoid compression when the
calibration evidence does not justify it.
