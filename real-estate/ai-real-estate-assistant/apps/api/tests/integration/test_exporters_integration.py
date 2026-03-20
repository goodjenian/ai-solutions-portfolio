from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest

from utils.exporters import ExportFormat, PropertyExporter


class TestExportersIntegration:
    """Integration tests for PropertyExporter."""

    @pytest.fixture
    def sample_properties_df(self):
        """Create a sample DataFrame representing real property data structure."""
        return pd.DataFrame(
            [
                {
                    "id": "prop_1",
                    "title": "Luxury Villa in Bodrum",
                    "price": 500000,
                    "currency": "USD",
                    "city": "Bodrum",
                    "country": "Turkey",
                    "rooms": 4,
                    "area_sqm": 250,
                    "property_type": "Villa",
                    "description": "Beautiful villa with sea view.",
                    "features": ["Pool", "Garden", "Sea View"],
                    "latitude": 37.0344,
                    "longitude": 27.4305,
                    "created_at": datetime.now(),
                    "has_parking": True,
                    "has_garden": True,
                    "has_pool": True,
                    "is_furnished": True,
                    "has_balcony": True,
                    "has_elevator": False,
                    "bathrooms": 3,
                },
                {
                    "id": "prop_2",
                    "title": "Apartment in Istanbul",
                    "price": 200000,
                    "currency": "USD",
                    "city": "Istanbul",
                    "country": "Turkey",
                    "rooms": 2,
                    "area_sqm": 85,
                    "property_type": "Apartment",
                    "description": "Central apartment near metro.",
                    "features": ["Security", "Gym"],
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "created_at": datetime.now(),
                    "has_parking": False,
                    "has_garden": False,
                    "has_pool": False,
                    "is_furnished": False,
                    "has_balcony": True,
                    "has_elevator": True,
                    "bathrooms": 1,
                },
            ]
        )

    def test_pdf_export_integration(self, sample_properties_df):
        """Test PDF export with realistic data structure."""
        exporter = PropertyExporter(sample_properties_df)

        # Execute export
        pdf_buffer = exporter.export(ExportFormat.PDF)

        # Verify output
        assert isinstance(pdf_buffer, BytesIO)
        content = pdf_buffer.getvalue()

        # Check PDF signature
        assert content.startswith(b"%PDF")

        # Verify content size is reasonable (not empty)
        assert len(content) > 1000

    def test_export_all_formats_integration(self, sample_properties_df):
        """Verify all export formats work with the same data source."""
        exporter = PropertyExporter(sample_properties_df)

        formats = [
            ExportFormat.CSV,
            ExportFormat.EXCEL,
            ExportFormat.JSON,
            ExportFormat.MARKDOWN,
            ExportFormat.PDF,
        ]

        for fmt in formats:
            result = exporter.export(fmt)
            assert result is not None
            if fmt in [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.MARKDOWN]:
                assert isinstance(result, str)
                assert len(result) > 0
            else:
                assert isinstance(result, BytesIO)
                assert len(result.getvalue()) > 0
