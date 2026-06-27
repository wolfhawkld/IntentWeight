# Draft Cover Letter: Information Processing & Management

Dear Editor,

We submit the manuscript "IntentRoute: Geometry-Guided and Feedback-Adaptive
Route Confidence for Efficient Evidence Selection" for
consideration as an original research article in Information Processing &
Management.

The manuscript studies evidence selection for retrieval-augmented question
answering under a practical quality-efficiency constraint: systems must provide
enough evidence for answer support while limiting the final retrieved context
sent to a language model. We propose IntentRoute, a geometry-guided and
feedback-adaptive route-confidence controller that combines dense semantic retrieval, BM25
lexical recall, cluster-local routing, trust-weighted contextual-bandit
feedback, and calibrated final-context compaction.

The paper's central contribution is a bounded systems and information retrieval
claim rather than a universal replacement for dense retrieval. Dense retrieval
is retained as the primary quality floor. Sentence-level MMR is treated as a
shared final-context compressor, and cross-encoder reranking is evaluated as a
late ranking layer. Under a frozen calibration/test protocol on LoTTE
technology/search from 100k to 638k corpus chunks, calibration-eligible
IntentRoute policies reduce final evidence-context input tokens by 6-18% at
100k, 200k, and 638k while avoiding the larger Hit@10 losses observed under
dense-only adaptive truncation. Additional LoTTE science/search, strong
post-retrieval baseline, and simulated-feedback recovery experiments bound the
claim and document when the method should be used conservatively.

We believe the manuscript fits IP&M because it addresses adaptive information
retrieval, evidence selection, and system design at the intersection of
computing and information science. The experiments emphasize reproducible
retrieval metrics, calibration/test separation, final context token accounting,
and reviewer-facing baseline controls.

The manuscript is original, is not under consideration elsewhere, and all
authors have approved the submission.

Sincerely,

TODO: Corresponding author name and contact details
