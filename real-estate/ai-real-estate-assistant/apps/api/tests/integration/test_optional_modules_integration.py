import builtins
import importlib

import pandas as pd
import pytest

from agents.recommendation_engine import PropertyRecommendationEngine
from data.schemas import UserPreferences


def test_recommendation_engine_explicit_matching_case_insensitive_and_float_rooms():
    engine = PropertyRecommendationEngine()
    prefs = UserPreferences(
        user_id="u1",
        budget_range=(0, 1000),
        preferred_cities=["Krakow"],
        preferred_rooms=[2.0],
        preferred_neighborhoods=["Old Town"],
        must_have_amenities=["has_parking"],
    )

    metadata = {
        "price": 950,
        "city": "KRAKOW",
        "rooms": 2.0,
        "neighborhood": "old town",
        "has_parking": True,
    }

    score = engine._calculate_explicit_score(metadata, prefs)
    assert score > 0.0


def test_ai_agent_optional_import_sets_none_when_dependency_missing(monkeypatch):
    from ai import agent as agent_module

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("langchain_experimental"):
            raise ImportError("missing optional dependency")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(agent_module)
    assert agent_module.create_pandas_dataframe_agent is None

    monkeypatch.setattr(builtins, "__import__", real_import)
    importlib.reload(agent_module)


def test_ai_agent_clear_error_when_optional_dependency_missing(monkeypatch):
    from ai import agent as agent_module

    monkeypatch.setattr(agent_module, "create_pandas_dataframe_agent", None)

    with pytest.raises(ImportError, match="langchain-experimental"):
        agent_module.RealEstateGPT(pd.DataFrame({"x": [1]}), key="test-key")
