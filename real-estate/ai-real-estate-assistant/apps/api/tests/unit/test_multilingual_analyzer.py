"""Unit tests for Multilingual Query Analyzer."""

from agents.query_analyzer import QueryIntent, get_query_analyzer


def test_multilingual_query_analyzer():
    analyzer = get_query_analyzer()

    # Russian: "Search apartment with parking and elevator built after 2010"
    # "Поиск квартиры с парковкой и лифтом построенной после 2010 года"
    ru_query = "Поиск квартиры с парковкой и лифтом построенной после 2010 года"
    analysis_ru = analyzer.analyze(ru_query)

    assert analysis_ru.intent == QueryIntent.SIMPLE_RETRIEVAL
    assert analysis_ru.extracted_filters.get("must_have_parking") is True
    assert analysis_ru.extracted_filters.get("must_have_elevator") is True
    assert analysis_ru.extracted_filters.get("year_built_min") == 2010

    # Turkish: "Find apartment with pool and energy class A"
    # "Havuzlu ve enerji sınıfı A olan daire bul"
    tr_query = "Havuzlu ve enerji sınıfı A olan daire bul"
    analysis_tr = analyzer.analyze(tr_query)

    assert analysis_tr.intent == QueryIntent.SIMPLE_RETRIEVAL
    assert analysis_tr.extracted_filters.get("has_pool") is True
    assert analysis_tr.extracted_filters.get("energy_ratings") == ["A"]

    # Russian: "Average price in Warsaw"
    # "Средняя цена в Варшаве"
    ru_analysis_query = "Средняя цена в Варшаве"
    analysis_ru_ana = analyzer.analyze(ru_analysis_query)
    assert analysis_ru_ana.intent == QueryIntent.ANALYSIS
    # Expect normalized city name
    assert analysis_ru_ana.extracted_filters.get("city") == "Warsaw"

    # Turkish: "Compare Istanbul vs Ankara" (Assuming cities are supported in patterns, actually Istanbul/Ankara are not in CITY_PATTERN yet, but intent should be COMPARISON)
    # But wait, CITY_PATTERN only has specific Polish cities.
    # I should check if intent works.
    tr_compare = "İstanbul vs Ankara karşılaştır"
    analysis_tr_comp = analyzer.analyze(tr_compare)
    assert analysis_tr_comp.intent == QueryIntent.COMPARISON
