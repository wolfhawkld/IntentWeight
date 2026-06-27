# IntentRoute Production Module

`intent_route` is the canonical Python import path for the geometry-guided and
feedback-adaptive evidence-routing controller.

```python
from intent_route import IntentRouteManager, IntentRouteStats

manager = IntentRouteManager(state_dir="data/intent_route")
```

The legacy `intent_weight` package and `IntentWeightManager` /
`IntentWeightStats` names remain compatible. Existing deployments may continue
to use `data/intent_weight/`; state files and serialized fields are unchanged.

Historical experiment paths and machine-readable labels are not renamed. New
code, reports, and experiments should use `IntentRoute` for human-facing names.
