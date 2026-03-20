from io import BytesIO

import pytest

from data.schemas import Property, PropertyCollection, PropertyType
from utils.exporters import ExportFormat, PropertyExporter


@pytest.fixture
def export_properties():
    """Create sample properties for export testing."""
    properties = [
        Property(
            id="e1",
            city="Krakow",
            rooms=2,
            bathrooms=1,
            price=850,
            area_sqm=52,
            has_parking=True,
            has_garden=False,
            property_type=PropertyType.APARTMENT,
            title="Nice Apartment in Center",
        ),
        Property(
            id="e2",
            city="Warsaw",
            rooms=3,
            bathrooms=2,
            price=1350,
            area_sqm=75,
            has_parking=True,
            has_garden=True,
            property_type=PropertyType.HOUSE,
            title="Spacious House",
        ),
    ]
    return PropertyCollection(properties=properties, total_count=2)


@pytest.fixture
def exporter(export_properties):
    """Create PropertyExporter instance."""
    return PropertyExporter(export_properties)


def test_export_format_enum_has_pdf():
    """Test that ExportFormat has PDF option."""
    assert hasattr(ExportFormat, "PDF")
    assert ExportFormat.PDF.value == "pdf"


def test_export_to_pdf_basic(exporter):
    """Test basic PDF export."""
    pdf_data = exporter.export_to_pdf()

    assert isinstance(pdf_data, BytesIO)
    content = pdf_data.getvalue()
    assert content.startswith(b"%PDF")
    assert len(content) > 0


def test_export_generic_pdf(exporter):
    """Test generic export method with PDF format."""
    pdf_data = exporter.export(ExportFormat.PDF)
    assert isinstance(pdf_data, BytesIO)
    assert pdf_data.getvalue().startswith(b"%PDF")


def test_get_filename_pdf(exporter):
    """Test PDF filename generation."""
    filename = exporter.get_filename(ExportFormat.PDF)
    assert filename.endswith(".pdf")
    assert "properties_" in filename
