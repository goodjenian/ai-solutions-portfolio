from pathlib import Path

from data.providers.csv_provider import CSVDataProvider
from data.providers.factory import DataProviderFactory
from data.providers.json_provider import JSONDataProvider


class TestDataProviderFactory:
    def test_create_csv_provider(self):
        provider = DataProviderFactory.create_provider("data.csv")
        assert isinstance(provider, CSVDataProvider)
        assert provider.source == "data.csv"

        provider = DataProviderFactory.create_provider(Path("data.xlsx"))
        assert isinstance(provider, CSVDataProvider)

    def test_create_json_provider(self):
        provider = DataProviderFactory.create_provider("data.json")
        assert isinstance(provider, JSONDataProvider)
        assert provider.source == "data.json"

        provider = DataProviderFactory.create_provider("http://example.com/data.json")
        assert isinstance(provider, JSONDataProvider)

    def test_create_default_provider(self):
        # Default fallback to CSV for unknown extensions
        provider = DataProviderFactory.create_provider("data.txt")
        assert isinstance(provider, CSVDataProvider)
