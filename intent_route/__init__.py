# -*- coding: utf-8 -*-
"""Canonical public API for the IntentRoute controller.

The implementation remains in :mod:`intent_weight` so existing deployments,
state paths, and serialized artifacts keep working. New integrations should use
``intent_route`` and the ``IntentRoute*`` class names.
"""
from __future__ import annotations

import importlib
import sys

from intent_weight import (
    FeedbackRequest,
    IntentRouteManager,
    IntentRouteStats,
    IntentWeightManager,
)
from intent_weight.models import IntentWeightStats


_COMPATIBLE_SUBMODULES = (
    "clustering",
    "conversation_store",
    "insight_extractor",
    "keyword_prior",
    "linucb",
    "models",
    "persistence",
    "reward",
    "user_credibility",
)

for _name in _COMPATIBLE_SUBMODULES:
    _module = importlib.import_module(f"intent_weight.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module


__all__ = [
    "FeedbackRequest",
    "IntentRouteManager",
    "IntentRouteStats",
    # Deprecated compatibility names are exported during the migration window.
    "IntentWeightManager",
    "IntentWeightStats",
]
