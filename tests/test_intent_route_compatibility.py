from __future__ import annotations

import importlib
from pathlib import Path


def test_canonical_and_legacy_manager_names_share_implementation() -> None:
    from intent_route import IntentRouteManager
    from intent_weight import IntentRouteManager as legacy_package_new_name
    from intent_weight import IntentWeightManager

    assert IntentRouteManager is legacy_package_new_name
    assert IntentRouteManager is IntentWeightManager
    assert IntentRouteManager.__name__ == "IntentRouteManager"


def test_canonical_and_legacy_stats_names_share_schema() -> None:
    from intent_route import IntentRouteStats, IntentWeightStats
    from intent_weight import IntentWeightStats as legacy_package_stats
    from intent_weight.models import IntentRouteStats as implementation_stats

    assert IntentRouteStats is implementation_stats
    assert IntentRouteStats is IntentWeightStats
    assert IntentRouteStats is legacy_package_stats
    assert IntentRouteStats.__name__ == "IntentRouteStats"
    stats = IntentRouteStats()
    payload = stats.model_dump() if hasattr(stats, "model_dump") else stats.dict()
    assert payload["enabled"] is False


def test_canonical_submodule_paths_resolve_to_legacy_implementation() -> None:
    for name in (
        "clustering",
        "conversation_store",
        "insight_extractor",
        "keyword_prior",
        "linucb",
        "models",
        "persistence",
        "reward",
        "user_credibility",
    ):
        canonical = importlib.import_module(f"intent_route.{name}")
        legacy = importlib.import_module(f"intent_weight.{name}")
        assert canonical is legacy


def test_canonical_manager_initializes_with_new_state_path(tmp_path: Path) -> None:
    from intent_route import IntentRouteManager, IntentRouteStats

    state_dir = tmp_path / "data" / "intent_route"
    manager = IntentRouteManager(state_dir=str(state_dir))
    stats = manager.get_stats()

    assert state_dir.is_dir()
    assert isinstance(stats, IntentRouteStats)
    assert stats.enabled is False
