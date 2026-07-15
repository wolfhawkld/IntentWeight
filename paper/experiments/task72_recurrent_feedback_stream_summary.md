# Task72 Recurrent Feedback-Stream Summary

Updated: 2026-07-13

## Scope and Validation Status

Task72 tests a deliberately narrow question left open by the frozen-policy
boundary in Task70: can trust-weighted simulated feedback improve routing on a
controlled stream with recurring local intents and an A-to-B-to-A local-intent
distribution shift? It is not a real-user RLHF experiment, a first-pass
unseen-query experiment, or an end-to-end cost study.

The protocol uses the fixed all-MiniLM-L6-v2, exact-score, BM25, and KMeans
artifacts for LoTTE technology/search 100k and science/search 100k. Each domain
has a predeclared 212-event stream (152 unique query IDs); each method executes
the same event stream for seeds 13, 17, and 19. The four controls are
Dense-only, static-nearest multi-route, cold full multi-route without feedback
updates, and trust-weighted learned full multi-route. All methods retain the
same Dense/BM25 rescue and fixed top-10 context policy.

The run produced `5,088 = 2 domains x 212 events x 4 methods x 3 seeds`
event rows. Its validation artifact confirms complete event coverage across all
24 dataset-method-seed runs and declares that no answer or final-context cache
was used. Immutable embeddings, BM25 rankings, and exact query-corpus scores
were the shared retrieval backend; they are not reused final answers or final
contexts.

This summary addresses the project validation categories for experimental
fairness, statistical rigor, artifact traceability, and claim boundaries. It
does not create a new positive manuscript claim.

## Main Result: No Stable Final-Retrieval Feedback Advantage

The table reports the descriptive mean and range across the three controller
seeds for learned-feedback minus cold-no-feedback. It is not a pooled IID
estimate. The corresponding query-ID block-bootstrap intervals, which retain
all repeated occurrences of a query ID, are in `results/task72_recurrent_feedback_stream/paired.csv`.

| Domain | Stream condition | Hit@10 delta | EvidenceRecall@10 delta | Selected-cluster-hit delta | Route-reward delta |
|---|---|---:|---:|---:|---:|
| science/search 100k | repeated | -2.8pp [-5.0, 0.0] | -3.1pp [-3.9, -2.7] | +38.5pp [+5.0, +58.3] | +37.6pp [+4.2, +58.3] |
| science/search 100k | nearby unseen | +0.0pp [-2.1, +2.1] | -0.8pp [-4.0, +1.4] | +38.9pp [+8.3, +60.4] | +38.9pp [+8.3, +60.4] |
| science/search 100k | unseen tail | +0.5pp [0.0, +1.6] | -0.1pp [-1.2, +0.9] | +19.3pp [+10.9, +34.4] | +18.2pp [+7.8, +34.4] |
| technology/search 100k | repeated | +0.0pp [0.0, 0.0] | +0.4pp [0.0, +0.7] | +5.4pp [-12.1, +25.8] | +5.4pp [-12.1, +25.8] |
| technology/search 100k | nearby unseen | +0.7pp [0.0, +2.1] | +0.1pp [-0.5, +0.7] | +22.9pp [+4.2, +35.4] | +22.9pp [+4.2, +35.4] |
| technology/search 100k | unseen tail | -1.0pp [-3.1, 0.0] | +0.1pp [-1.6, +2.1] | +13.0pp [+10.9, +14.1] | +9.4pp [+6.2, +12.5] |

Feedback often changes the selected route relative to the cold controller,
particularly on science/search. That route-level movement does not translate
into a stable improvement in final fused retrieval. Static-nearest routing also
has materially higher selected-cluster hit than learned feedback in both
domains, while the Dense/BM25 rescue path frequently reduces the corresponding
final-quality difference. Thus a higher route diagnostic must not be presented
as a higher final retrieval metric.

The first-to-second region-B exposure after the declared A-to-B shift provides
no stable learned-feedback adaptation advantage. For example, the learned
route-reward change is `0.00, +0.05, 0.00` for science and `+0.05, +0.10,
0.00` for technology across seeds 13/17/19; cold no-feedback also changes
because its stochastic arm choices differ (`+0.05, +0.05, 0.00` and
`-0.10, +0.10, +0.20`, respectively). This is insufficient to attribute a
reliable distribution-shift correction to feedback.

## Recovery Boundary

The final-fused Dense floor leaves few repeated queries with an initial
Hit@10 miss (12 across the six learned domain-seed trajectories), and none is
subsequently recovered in this stream. Route-only recovery is mixed: learned
cluster recovery ranges from 20.6% to 59.1% in science and 5.7% to 25.9% in
technology, with different affected denominators and no superiority result over
the cold control. It is therefore not valid to use Task72 as a final-retrieval
recovery claim.

This does not invalidate the earlier Task40 hard-case recovery analysis, whose
question and intervention differ. It does require that Task40 remain framed as
conditional post-feedback repair evidence, not as a general recurrent-stream or
unseen-query result.

## Interpretation and Paper Use

Task72 establishes a useful negative boundary. Under fixed full multi-route
fusion with final-fused reward attribution, Dense/BM25 rescue can mask the
credit signal required to learn cluster-route improvement. The experiment does
not support a claim that simulated feedback reliably improves final retrieval
for recurring local-intent streams, and it does not change the Task70 boundary
against a frozen first-pass unseen-query advantage.

Use this artifact only as boundary evidence in the project record or, if it is
included in a revision, as a limitation. Do not add it to the main paper as
positive feedback validation. A future credit-assignment ablation would need a
predeclared cluster-route reward objective and a clearly separate claim; it
cannot retroactively turn this full-fusion result into support for production
RLHF.

## Traceability

- Protocol: `task72_recurrent_feedback_stream_plan.md`
- Executable: `scripts/task72_recurrent_feedback_stream.py`
- Stream manifests and coverage: `results/task72_recurrent_feedback_stream/stream_manifests.json`, `validation.json`
- Event metrics: `results/task72_recurrent_feedback_stream/event_rows.csv`, `summary.csv`
- Paired uncertainty: `results/task72_recurrent_feedback_stream/paired.csv`
- Shift and recovery diagnostics: `results/task72_recurrent_feedback_stream/adaptation.csv`, `recovery.csv`
