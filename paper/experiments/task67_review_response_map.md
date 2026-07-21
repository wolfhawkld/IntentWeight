# Task67 Review-Response Map

> **Historical checkpoint:** This document preserves the state at its stated
> date. Do not use its counts or remaining-work list as current status; use
> `paper/experiments/task80_authoritative_submission_state.md` and
> `paper/experiments/task80_remaining_work_checklist.md`.

Updated: 2026-07-05

This map records how the recent Metis/GLM review concerns were handled without
replacing the IntentRoute thesis.

| Review concern | Decision | Evidence or manuscript action |
| --- | --- | --- |
| Geometry/manifold wording may imply theorem-level structure | Accept boundary, retain motivation | Geometry is described as manifold-inspired local relevance structure and a diagnostic control signal, not proof of a global manifold or a deterministic gain law. |
| Route reward may be confused with final fused Hit@10 | Accept | Tasks58/59 and main Table 3 separate route reward, selected-cluster hit, dense rate, final Hit delta, and token saving. |
| Dense rescue and budget control may explain final robustness | Accept and test directly | Tasks65.1/65.2 compare geometry/feedback/random/no-feedback and dense-budget controls on fixed pools; Task65.4 independently calibrates matched frontiers. |
| Route confidence directly predicts compression safety | Reject as unsupported causal claim | Task65.3 shows the relationship is feature- and stage-dependent. The method and Figure 1 specification now separate route confidence from post-ranking budget calibration. |
| IntentRoute may be uniformly better than dense at equal quality | Reject universal claim, retain bounded trade-off claim | Task65.4 reports matched-frontier results; Tasks65.5/65.6 expose split and cross-scale instability instead of hiding it. |
| Frozen calibration may have selected a lucky split | Accept | Task65.5 evaluates overlapping split sensitivity; Task65.6 adds normalized cross-fitted calibration across scales. |
| One LLM judge is insufficient | Accept | Task65.7 adds DeepSeek, GLM-5.2, MiniMax-M3, agreement, majority-vote CIs, and missingness analysis over the fixed 2,100 answers. |
| Strong compression/reranking baselines are missing | Accept | SentMMR, Selective Context-lite, prompt-pruning, and cross-encoder controls are retained in Supplementary Section S10. |
| Larger seed counts are needed regardless of cost | Decline as unnecessary for the stated design | Seeds 13/17/19 are fixed independent runs, paired bootstrap/CIs and sensitivity analyses are reported, and prior timing tests showed sharply increasing CPU cost without changing the inferential target. |
| LinUCB and geometry should be removed because dense rescue is strong | Decline | The experiments bound their role rather than erase it: geometry/feedback shape route construction and hard-case diagnosis, while dense/BM25 rescue and independent budgeting provide the quality floor. |

## Resulting Claim

The retained thesis is a bounded systems claim: local geometric structure can
organize route candidates; feedback-adaptive LinUCB can revise route
preferences; dense/BM25 rescue protects fused retrieval; and a separately
calibrated final-context controller exposes a measurable quality-efficiency
trade-off. The paper does not claim that geometry alone causes token savings or
that route confidence alone predicts compression safety.
