import pandas as pd
import pytest

from utils.exporters import ExportFormat, InsightsExporter, PropertyExporter


def test_property_exporter_to_dataframe_handles_mixed_inputs():
    class Coll:
        def __init__(self):
            self.properties = [{"city": "Warsaw", "price": 1000, "rooms": 2}, object()]
            self.total_count = 2

    exporter = PropertyExporter(properties=Coll())
    assert not exporter.df.empty
    assert "city" in exporter.df.columns


def test_property_exporter_export_to_markdown_handles_dicts_and_limits():
    props = [
        {
            "city": "Warsaw",
            "title": "Nice flat",
            "price": 1000,
            "rooms": 2,
            "bathrooms": 1,
            "property_type": "apartment",
            "has_parking": True,
            "source_url": "https://example.com/1",
        },
        {
            "city": "Warsaw",
            "title": "Second",
            "price": 1200,
            "rooms": 3,
            "bathrooms": 2,
            "property_type": "apartment",
        },
    ]
    exporter = PropertyExporter(properties=props)
    md = exporter.export_to_markdown(include_summary=True, max_properties=1)
    assert "[View Listing](https://example.com/1)" in md
    assert "Showing 1 of 2 properties" in md


def test_property_exporter_export_raises_for_unsupported_format():
    exporter = PropertyExporter(properties=[{"city": "Warsaw", "price": 1000, "rooms": 2}])
    with pytest.raises(ValueError) as exc:
        exporter.export(format="bad")  # type: ignore[arg-type]
    assert "Unsupported export format" in str(exc.value)


def test_insights_exporter_generates_json_and_markdown():
    class FakeInsights:
        def get_city_price_indices(self, cities=None):
            return pd.DataFrame([{"city": "Warsaw", "index": 1.23}])

        def get_monthly_price_index(self, city=None):
            return pd.DataFrame([{"month": pd.Timestamp("2024-01-01"), "index": 100.0}])

    exp = InsightsExporter(insights=FakeInsights())

    js = exp.export_city_indices_json(pretty=False)
    assert '"indices"' in js

    md = exp.export_city_indices_markdown()
    assert "# City Price Indices" in md
    assert "Warsaw" in md

    csv = exp.export_monthly_index_csv()
    assert "month" in csv

    js2 = exp.export_monthly_index_json(pretty=False)
    assert '"monthly_index"' in js2

    md2 = exp.export_monthly_index_markdown(city="Warsaw")
    assert "Monthly Price Index" in md2
    assert "Warsaw" in md2


def test_property_exporter_get_filename_uses_format_extension():
    exporter = PropertyExporter(properties=[{"city": "Warsaw", "price": 1000, "rooms": 2}])
    name = exporter.get_filename(format=ExportFormat.JSON, prefix="x")
    assert name.startswith("x_")
    assert name.endswith(".json")
