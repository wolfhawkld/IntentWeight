# Task65.3 Dynamic-Route Mediation Summary

Task65.3 is complete.

## Protocol

The experiment freezes the exact Task37 `cluster_only` LinUCB trajectory,
including selected arms and confidence for seeds `13,17,19`. Because policy
updates use cluster-only reward, the final fusion weights do not affect this
trajectory. Cached dense, BM25, and selected-arm cluster rankings are then used
to replay five counterfactual evidence pools:

- the original confidence-gated dynamic route;
- fixed full multi-route fusion;
- fixed cluster-primary fusion;
- shuffled confidence tiers preserving each split/seed tier frequency;
- dense top-10.

The replay exactly matches all original Task37 dynamic rankings. Every variant
then receives the same frozen `token_budget_r0.95_m4` action. Query-level paired
bootstrap intervals use the existing 417-query test split.

## Main Result

| Variant | Budgeted Hit@10 | Delta vs dense | Token saving vs dense |
|---|---:|---:|---:|
| Dynamic confidence gating | 0.8705 | -0.00 pp | 6.18% |
| Fixed full fusion | 0.8745 | +0.40 pp | 5.27% |
| Shuffled confidence tiers | 0.8225 | -4.80 pp | 6.54% |
| Fixed cluster-primary | 0.7626 | -10.79 pp | 6.93% |
| Dense budget-only | 0.8561 | -1.44 pp | 13.83% |

Dynamic gating exceeds shuffled tiers by `+4.80 pp` before and after the common
budget; all three seed-level bootstrap intervals exclude zero. Shuffling keeps
the same tier frequencies, so the result supports the query-to-tier assignment,
not merely the overall mixture of route shapes. Dynamic gating also exceeds
always-cluster-primary by `+10.95 pp` before budgeting and `+10.79 pp` after it,
again with 3/3 intervals excluding zero.

Fixed full fusion remains `+0.48 pp` above dynamic gating before budgeting and
`+0.40 pp` after budgeting, while saving about `0.91` percentage points fewer
tokens after the common budget. None of the dynamic-versus-fixed-full hit
intervals excludes zero, and strict seed-level non-inferiority is not
established after budgeting. Dynamic gating should therefore be interpreted as
a cost-aware route assignment, not a quality improvement over full fusion.

## Tier Mechanism

Original high-confidence queries achieve mean source `Hit@10=0.924` under the
cluster-primary route. For hybrid-lite queries, dynamic routing reaches `0.850`
versus `0.748` under always-cluster-primary. For low-confidence fallback
queries, full fallback reaches `0.800`, whereas forcing cluster-primary falls
to `0.240`. This directly supports confidence as a routing/fallback signal.

## Compression Boundary

Dynamic gating does not create more relevant chunks or more compression
headroom than fixed full fusion. Mean relevant chunks in top-10 are `2.121`
versus `2.315`, and mean actual oracle-safe token saving is `53.05%` versus
`55.39%`. Route confidence has mean Spearman correlation `-0.056` with oracle
safe-token headroom; every seed-level interval includes zero.

The supported mediation chain is:

> geometry/feedback -> route confidence -> query-specific route shape ->
> evidence-pool quality.

The unsupported chain remains:

> route confidence -> direct prediction of per-query compression safety.
