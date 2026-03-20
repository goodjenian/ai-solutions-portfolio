from langchain_core.documents import Document

from agents.recommendation_engine import PropertyRecommendationEngine
from data.schemas import UserPreferences


def test_recommend_returns_empty_for_no_documents():
    engine = PropertyRecommendationEngine()
    assert engine.recommend([]) == []


def test_recommend_ranks_and_limits_k():
    engine = PropertyRecommendationEngine()
    docs = [
        Document(page_content="Nice apartment", metadata={"id": "1", "price_per_sqm": 50}),
        Document(
            page_content="Great value apartment" * 30,
            metadata={
                "id": "2",
                "price_per_sqm": 15,
                "has_parking": True,
                "has_garden": True,
                "has_balcony": True,
            },
        ),
    ]

    ranked = engine.recommend(docs, k=1)
    assert len(ranked) == 1
    assert ranked[0][0].metadata["id"] == "2"
    assert ranked[0][2]["premium_amenities"] is True


def test_explicit_score_matches_city_case_insensitive_and_rooms_float():
    engine = PropertyRecommendationEngine()
    prefs = UserPreferences(
        user_id="u1",
        budget_range=(0, 1000),
        preferred_cities=["Krakow"],
        preferred_rooms=[2.0],
        must_have_amenities=["has_parking"],
        preferred_neighborhoods=["Old Town"],
    )

    doc = Document(
        page_content="Apartment",
        metadata={
            "id": "p1",
            "price": 950,
            "city": "KRAKOW",
            "rooms": 2.0,
            "has_parking": True,
            "neighborhood": "old town",
            "price_per_sqm": 25,
        },
    )

    score, explanation = engine._score_property(
        doc, prefs, viewed_properties=None, favorited_properties=None
    )
    assert score > 0
    assert "preference_match" in explanation
    assert explanation["why_recommended"]


def test_generate_reason_defaults_when_no_signals():
    engine = PropertyRecommendationEngine()
    reason = engine._generate_recommendation_reason(
        explicit_score=0.0,
        value_score=0.0,
        implicit_score=0.0,
        metadata={},
    )
    assert reason == "Good match for your search"
