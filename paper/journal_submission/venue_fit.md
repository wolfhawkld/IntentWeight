# Venue Fit

Updated: 2026-06-21

## Primary Target: Information Processing & Management

Official fit anchors:

- IP&M publishes research at the intersection of computing and information
  science.
- It welcomes research manuscripts, methods manuscripts, review manuscripts,
  and critical application manuscripts concerning system design research.
- The journal uses double anonymized peer review.

Fit for IntentWeight:

- Strong fit as an information retrieval and RAG evidence-selection paper.
- The strongest contribution is not a new retriever alone, but a controller
  over dense, lexical, cluster-local, compression, and reranking stages.
- The token-quality frontier, calibration/test protocol, and strong baselines
  map naturally to IR evaluation expectations.

Primary IP&M framing:

IntentWeight is a feedback-adaptive route-and-budget controller for
quality-efficiency trade-offs in retrieval-backed evidence selection.

Keep:

- dense retrieval as the primary quality floor;
- SentMMR as a shared final-context compressor;
- cross-encoder reranking as a late ranking layer;
- the piecewise relevance-manifold assumption as motivation and diagnostic
  support, not as theorem-level proof;
- the main claim on final retrieved-context input tokens, not retrieval-side
  candidate counts.

Main IP&M risks:

- The answer-generation evaluation remains small.
- Feedback is simulated rather than collected from real users.
- Strict seed-level non-inferiority is scale-dependent.
- The 400k scale is diagnostic because it fails the calibration eligibility
  gate.

## Fallback Target: Expert Systems with Applications

Official fit anchors:

- ESWA focuses on expert and intelligent systems applied in industry,
  government, and universities.
- It explicitly includes information retrieval, knowledge management, data
  mining, text mining, and multi-agent systems.
- It discourages superficial metaphor-based algorithm claims and asks authors
  to use standard terminology and explain genuine component adaptation.

Fit for IntentWeight:

- Viable if framed as an intelligent-system engineering method for
  knowledge-augmented applications.
- The manuscript should emphasize system design, implementation, testing,
  operational cost control, and practical deployment guidance.

Primary ESWA framing:

IntentWeight is an intelligent evidence-selection controller that combines
standard retrieval, contextual-bandit routing, and calibrated final-context
budgeting for retrieval-augmented applications.

Main ESWA risks:

- The "manifold" language can look metaphor-heavy unless kept bounded.
- ESWA may expect broader application-level validation.
- The method should be described using standard retrieval, clustering, and
  contextual-bandit terminology rather than branding-first language.

## Deprioritized Target: ACM TOIS

TOIS remains a possible stretch venue, but the current manuscript is better
positioned for IP&M or ESWA. A TOIS attempt should wait for stronger
answer-level evaluation, additional domains, and a sharper theoretical or
methodological contribution for the IR community.
