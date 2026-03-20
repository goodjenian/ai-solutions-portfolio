"""
Export functionality for property data.

Supports exporting properties to multiple formats:
- CSV: Simple spreadsheet format
- Excel: Formatted spreadsheet with multiple sheets
- JSON: Structured data format
- Markdown: Human-readable report format
"""

import json
from datetime import datetime
from enum import Enum
from io import BytesIO, StringIO
from typing import Any, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from analytics import MarketInsights


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    EXCEL = "xlsx"
    JSON = "json"
    MARKDOWN = "md"
    PDF = "pdf"


class PropertyExporter:
    """
    Exporter for property data to various formats.

    Provides methods to export property collections to CSV, Excel, JSON,
    and Markdown formats with optional filtering and customization.
    """

    def __init__(self, properties: Any) -> None:
        """
        Initialize exporter with property data.

        Args:
            properties: Collection of properties to export (PropertyCollection, DataFrame, or list of dicts)
        """
        self.properties = properties
        self.df = self._to_dataframe()

    def _normalize_columns(self, columns: Optional[List[str]]) -> Optional[List[str]]:
        if columns is None:
            return None
        if not columns:
            raise ValueError("columns must not be empty when provided")
        seen: set[str] = set()
        normalized: List[str] = []
        for col in columns:
            if col in seen:
                raise ValueError(f"Duplicate column: {col}")
            seen.add(col)
            normalized.append(col)
        missing = [c for c in normalized if c not in self.df.columns]
        if missing and not self.df.empty:
            raise ValueError(f"Unknown columns: {', '.join(missing)}")
        return normalized

    def _filtered_df(self, columns: Optional[List[str]]) -> pd.DataFrame:
        normalized = self._normalize_columns(columns)
        return self.df.reindex(columns=normalized) if normalized else self.df

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert properties to pandas DataFrame."""
        if isinstance(self.properties, pd.DataFrame):
            return self.properties.copy()

        if isinstance(self.properties, list):
            return pd.DataFrame(self.properties)

        # Assume PropertyCollection
        data = []
        # Handle case where properties might be a list inside PropertyCollection or just the object
        # itself if it's iterable
        props_list = getattr(self.properties, "properties", self.properties)

        # If it's not iterable (single object), wrap in list
        if not isinstance(props_list, (list, tuple)) and not hasattr(props_list, "__iter__"):
            props_list = [props_list]

        for prop in props_list:
            if hasattr(prop, "dict"):
                prop_dict = prop.dict()
            elif isinstance(prop, dict):
                prop_dict = prop
            else:
                continue  # Skip unknown types

            # Convert enum to string
            if "property_type" in prop_dict:
                prop_type = prop_dict["property_type"]
                prop_dict["property_type"] = (
                    prop_type.value if hasattr(prop_type, "value") else str(prop_type)
                )
            if "listing_type" in prop_dict and prop_dict["listing_type"]:
                lt = prop_dict["listing_type"]
                prop_dict["listing_type"] = lt.value if hasattr(lt, "value") else str(lt)
            if "negotiation_rate" in prop_dict and prop_dict["negotiation_rate"]:
                neg_rate = prop_dict["negotiation_rate"]
                prop_dict["negotiation_rate"] = (
                    neg_rate.value if hasattr(neg_rate, "value") else str(neg_rate)
                )

            # Add POI summary
            if hasattr(prop, "points_of_interest") and prop.points_of_interest:
                prop_dict["poi_count"] = len(prop.points_of_interest)
                prop_dict["closest_poi_distance"] = min(
                    p.distance_meters for p in prop.points_of_interest
                )
                prop_dict["poi_categories"] = ", ".join(
                    sorted(list(set(p.category for p in prop.points_of_interest)))
                )
            else:
                # Keep existing if already in dict, else set default
                if "poi_count" not in prop_dict:
                    prop_dict["poi_count"] = 0
                if "closest_poi_distance" not in prop_dict:
                    prop_dict["closest_poi_distance"] = None
                if "poi_categories" not in prop_dict:
                    prop_dict["poi_categories"] = ""

            data.append(prop_dict)
        return pd.DataFrame(data)

    def export_to_csv(
        self,
        columns: Optional[List[str]] = None,
        include_header: bool = True,
        delimiter: str = ",",
        decimal: str = ".",
    ) -> str:
        """
        Export properties to CSV format.

        Args:
            columns: Optional list of columns to include
            include_header: Whether to include header row

        Returns:
            CSV string
        """
        if len(delimiter) != 1 or delimiter in ("\n", "\r"):
            raise ValueError("delimiter must be a single non-newline character")
        if len(decimal) != 1 or decimal in ("\n", "\r"):
            raise ValueError("decimal must be a single non-newline character")
        df = self._filtered_df(columns)
        return str(
            df.to_csv(
                index=False,
                header=include_header,
                sep=delimiter,
                decimal=decimal,
                lineterminator="\n",
            )
        )

    def export_to_excel(
        self,
        include_summary: bool = True,
        include_statistics: bool = True,
        columns: Optional[List[str]] = None,
    ) -> BytesIO:
        """
        Export properties to Excel format with multiple sheets.

        Args:
            include_summary: Include summary sheet with statistics
            include_statistics: Include detailed statistics sheet

        Returns:
            BytesIO object containing Excel file
        """
        output = BytesIO()
        properties_df = self._filtered_df(columns)
        stats_df = self.df

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Main properties sheet
            properties_df.to_excel(writer, sheet_name="Properties", index=False)

            if include_summary:
                # Summary sheet
                has_price = "price" in stats_df.columns
                has_rooms = "rooms" in stats_df.columns
                has_parking = "has_parking" in stats_df.columns
                has_garden = "has_garden" in stats_df.columns
                has_furnished = "is_furnished" in stats_df.columns
                summary_data = {
                    "Metric": [
                        "Total Properties",
                        "Average Price",
                        "Median Price",
                        "Min Price",
                        "Max Price",
                        "Average Rooms",
                        "Properties with Parking",
                        "Properties with Garden",
                        "Furnished Properties",
                    ],
                    "Value": [
                        len(stats_df),
                        f"${stats_df['price'].mean():.2f}" if has_price else "N/A",
                        f"${stats_df['price'].median():.2f}" if has_price else "N/A",
                        f"${stats_df['price'].min():.2f}" if has_price else "N/A",
                        f"${stats_df['price'].max():.2f}" if has_price else "N/A",
                        f"{stats_df['rooms'].mean():.1f}" if has_rooms else "N/A",
                        (
                            f"{stats_df['has_parking'].sum()} "
                            f"({stats_df['has_parking'].mean() * 100:.1f}%)"
                            if has_parking
                            else "N/A"
                        ),
                        (
                            f"{stats_df['has_garden'].sum()} "
                            f"({stats_df['has_garden'].mean() * 100:.1f}%)"
                            if has_garden
                            else "N/A"
                        ),
                        (
                            f"{stats_df['is_furnished'].sum()} "
                            f"({stats_df['is_furnished'].mean() * 100:.1f}%)"
                            if has_furnished
                            else "N/A"
                        ),
                    ],
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            if include_statistics:
                # Statistics by city
                if {"city", "price"}.issubset(stats_df.columns):
                    city_aggs: dict[str, object] = {
                        "price": ["count", "mean", "median", "min", "max"]
                    }
                    if "rooms" in stats_df.columns:
                        city_aggs["rooms"] = "mean"
                    if "has_parking" in stats_df.columns:
                        city_aggs["has_parking"] = "mean"
                    city_stats = stats_df.groupby("city").agg(city_aggs).round(2)
                    city_stats.to_excel(writer, sheet_name="By City")

                # Statistics by property type
                if {"property_type", "price"}.issubset(stats_df.columns):
                    type_aggs: dict[str, object] = {"price": ["count", "mean", "median"]}
                    if "rooms" in stats_df.columns:
                        type_aggs["rooms"] = "mean"
                    if "area_sqm" in stats_df.columns:
                        type_aggs["area_sqm"] = "mean"
                    type_stats = stats_df.groupby("property_type").agg(type_aggs).round(2)
                    type_stats.to_excel(writer, sheet_name="By Type")

        output.seek(0)
        return output

    def export_to_json(
        self,
        pretty: bool = True,
        include_metadata: bool = True,
        columns: Optional[List[str]] = None,
    ) -> str:
        """
        Export properties to JSON format.

        Args:
            pretty: Use pretty formatting with indentation
            include_metadata: Include export metadata

        Returns:
            JSON string
        """
        df = self._filtered_df(columns)
        props_data = df.to_dict(orient="records")
        total_count = len(df)

        data = {"properties": props_data}

        if include_metadata:
            data["metadata"] = {
                "total_count": total_count,
                "exported_at": datetime.now().isoformat(),
                "export_format": "json",
            }

        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, default=str)

    def export_to_markdown(
        self, include_summary: bool = True, max_properties: Optional[int] = None
    ) -> str:
        """
        Export properties to Markdown report format.

        Args:
            include_summary: Include summary statistics
            max_properties: Maximum number of properties to include (None = all)

        Returns:
            Markdown formatted string
        """
        lines = []

        # Helper to get properties list
        if isinstance(self.properties, pd.DataFrame):
            # Convert to list of named tuples for attribute access
            properties_list = list(self.properties.itertuples(index=False))
            total_count = len(self.properties)
        elif isinstance(self.properties, list):
            # Wrap dicts to allow dot access if needed, or ensure code handles dicts
            # But the code below uses dot access (prop.city).
            # Let's use a simple wrapper class
            class DictObj:
                def __init__(self, d: dict[str, Any]) -> None:
                    for k, v in d.items():
                        setattr(self, k, v)

                def __getattr__(self, name: str) -> Any:
                    return None

            properties_list = [DictObj(p) if isinstance(p, dict) else p for p in self.properties]
            total_count = len(self.properties)
        else:
            properties_list = self.properties.properties
            total_count = self.properties.total_count

        # Header
        lines.append("# Property Listing Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\nTotal Properties: {total_count}")
        lines.append("\n---\n")

        # Summary statistics
        if include_summary:
            has_price = "price" in self.df.columns
            has_rooms = "rooms" in self.df.columns
            lines.append("## Summary Statistics\n")
            lines.append(
                f"- **Average Price**: ${self.df['price'].mean():.2f}"
                if has_price
                else "- **Average Price**: N/A"
            )
            lines.append(
                f"- **Median Price**: ${self.df['price'].median():.2f}"
                if has_price
                else "- **Median Price**: N/A"
            )
            lines.append(
                (
                    f"- **Price Range**: ${self.df['price'].min():.2f} - ${self.df['price'].max():.2f}"
                    if has_price
                    else "- **Price Range**: N/A"
                )
            )
            lines.append(
                f"- **Average Rooms**: {self.df['rooms'].mean():.1f}"
                if has_rooms
                else "- **Average Rooms**: N/A"
            )

            # Check for columns before accessing
            if "has_parking" in self.df.columns:
                lines.append(
                    f"- **Properties with Parking**: {self.df['has_parking'].sum()} "
                    f"({self.df['has_parking'].mean() * 100:.1f}%)"
                )
            if "has_garden" in self.df.columns:
                lines.append(
                    f"- **Properties with Garden**: {self.df['has_garden'].sum()} "
                    f"({self.df['has_garden'].mean() * 100:.1f}%)\n"
                )

            # By city
            lines.append("### By City\n")
            if "city" in self.df.columns and has_price:
                city_counts = self.df["city"].value_counts()
                for city, count in city_counts.items():
                    city_avg = self.df[self.df["city"] == city]["price"].mean()
                    lines.append(f"- **{city}**: {count} properties (avg: ${city_avg:.2f})")
            lines.append("\n---\n")

        # Properties
        lines.append("## Property Listings\n")

        properties_to_show = properties_list[:max_properties] if max_properties else properties_list

        for i, prop in enumerate(properties_to_show, 1):
            city = getattr(prop, "city", "Unknown")
            lines.append(f"### {i}. Property in {city}")

            title = getattr(prop, "title", None)
            if title:
                lines.append(f"**{title}**\n")

            price = getattr(prop, "price", 0)
            lines.append(f"- **Price**: ${price}/month")

            prop_type = getattr(prop, "property_type", "Unknown")
            type_str = prop_type.value if hasattr(prop_type, "value") else str(prop_type)
            lines.append(f"- **Type**: {type_str}")

            rooms = getattr(prop, "rooms", 0)
            bathrooms = getattr(prop, "bathrooms", 0)
            lines.append(f"- **Rooms**: {int(rooms)} bedrooms, {int(bathrooms)} bathrooms")

            area = getattr(prop, "area_sqm", None)
            if area:
                lines.append(f"- **Area**: {area} sqm")

            # Amenities
            amenities = []
            if getattr(prop, "has_parking", False):
                amenities.append("Parking")
            if getattr(prop, "has_garden", False):
                amenities.append("Garden")
            if getattr(prop, "has_pool", False):
                amenities.append("Pool")
            if getattr(prop, "is_furnished", False):
                amenities.append("Furnished")
            if getattr(prop, "has_balcony", False):
                amenities.append("Balcony")
            if getattr(prop, "has_elevator", False):
                amenities.append("Elevator")

            if amenities:
                lines.append(f"- **Amenities**: {', '.join(amenities)}")

            # Points of Interest
            pois = getattr(prop, "points_of_interest", [])
            if pois:
                lines.append("- **Points of Interest**:")
                for poi in pois:
                    # Handle POI if it's object or dict
                    poi_dict = poi if isinstance(poi, dict) else None
                    name = getattr(poi, "name", poi_dict.get("name") if poi_dict else str(poi))
                    category = getattr(
                        poi, "category", poi_dict.get("category") if poi_dict else ""
                    )
                    distance = getattr(
                        poi,
                        "distance_meters",
                        poi_dict.get("distance_meters") if poi_dict else 0,
                    )
                    try:
                        distance_int = int(distance or 0)
                    except Exception:
                        distance_int = 0
                    lines.append(f"  - {name} ({category}): {distance_int}m")

            desc = getattr(prop, "description", None)
            if desc:
                lines.append(f"\n{desc}")

            url = getattr(prop, "source_url", None)
            if url:
                lines.append(f"\n[View Listing]({url})")

            lines.append("\n---\n")

        if max_properties and len(properties_list) > max_properties:
            lines.append(f"\n*Showing {max_properties} of {len(properties_list)} properties*\n")

        return "\n".join(lines)

    def export_to_pdf(self) -> BytesIO:
        """
        Export properties to PDF format.

        Returns:
            BytesIO object containing PDF file
        """
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Property Listing Report", styles["Title"]))
        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]
            )
        )
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph("Summary Statistics", styles["Heading2"]))
        has_price = "price" in self.df.columns
        has_rooms = "rooms" in self.df.columns
        summary_data = [
            ["Metric", "Value"],
            ["Total Properties", str(len(self.df))],
            ["Average Price", f"${self.df['price'].mean():.2f}" if has_price else "N/A"],
            ["Median Price", f"${self.df['price'].median():.2f}" if has_price else "N/A"],
            ["Average Rooms", f"{self.df['rooms'].mean():.1f}" if has_rooms else "N/A"],
        ]
        t_summary = Table(summary_data)
        t_summary.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(t_summary)
        story.append(Spacer(1, 20))

        # Properties Table
        story.append(Paragraph("Property Listings", styles["Heading2"]))

        # Prepare table data
        # Select key columns for the PDF table to fit page width
        table_headers = ["City", "Type", "Price", "Rooms", "Area (sqm)", "Title"]
        table_data = [table_headers]

        for _, row in self.df.iterrows():
            title = str(row.get("title", ""))
            title_display = title[:30] + "..." if len(title) > 30 else title
            table_data.append(
                [
                    str(row.get("city", "")),
                    str(row.get("property_type", "")),
                    f"${row.get('price', 0)}",
                    str(row.get("rooms", "")),
                    str(row.get("area_sqm", "")),
                    title_display,
                ]
            )

        t_props = Table(table_data, colWidths=[60, 60, 50, 40, 50, 180])
        t_props.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (2, 1), (4, -1), "RIGHT"),  # Align numbers right
                ]
            )
        )

        story.append(t_props)

        doc.build(story)
        output.seek(0)
        return output

    def export(self, format: ExportFormat, **kwargs: Any) -> str | BytesIO:
        """
        Export properties to specified format.

        Args:
            format: Export format (CSV, Excel, JSON, Markdown)
            **kwargs: Format-specific options

        Returns:
            Exported data (string or BytesIO depending on format)
        """
        if format == ExportFormat.CSV:
            return self.export_to_csv(**kwargs)
        elif format == ExportFormat.EXCEL:
            return self.export_to_excel(**kwargs)
        elif format == ExportFormat.JSON:
            return self.export_to_json(**kwargs)
        elif format == ExportFormat.MARKDOWN:
            return self.export_to_markdown(**kwargs)
        elif format == ExportFormat.PDF:
            return self.export_to_pdf()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_filename(self, format: ExportFormat, prefix: str = "properties") -> str:
        """
        Generate filename for export.

        Args:
            format: Export format
            prefix: Filename prefix

        Returns:
            Filename with timestamp and extension
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = format.value
        return f"{prefix}_{timestamp}.{extension}"


class InsightsExporter:
    def __init__(self, insights: MarketInsights):
        self.insights = insights

    def export_city_indices_csv(self, cities: List[str] | None = None) -> str:
        df = self.insights.get_city_price_indices(cities)
        return str(df.to_csv(index=False))

    def export_city_indices_json(self, cities: List[str] | None = None, pretty: bool = True) -> str:
        df = self.insights.get_city_price_indices(cities)
        obj = {"indices": df.to_dict(orient="records")}
        return json.dumps(obj, indent=2 if pretty else None)

    def export_city_indices_markdown(self, cities: List[str] | None = None) -> str:
        df = self.insights.get_city_price_indices(cities)
        buf = StringIO()
        buf.write("# City Price Indices\n\n")
        buf.write(df.to_markdown(index=False))
        return buf.getvalue()

    def export_city_indices_excel(self, cities: List[str] | None = None) -> BytesIO:
        df = self.insights.get_city_price_indices(cities)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="CityIndices", index=False)
        output.seek(0)
        return output

    def export_monthly_index_csv(self, city: str | None = None) -> str:
        df = self.insights.get_monthly_price_index(city)
        df = df.copy()
        if "month" in df.columns:
            df["month"] = df["month"].astype(str)
        return str(df.to_csv(index=False))

    def export_monthly_index_json(self, city: str | None = None, pretty: bool = True) -> str:
        df = self.insights.get_monthly_price_index(city)
        df = df.copy()
        if "month" in df.columns:
            df["month"] = df["month"].astype(str)
        obj = {"monthly_index": df.to_dict(orient="records")}
        return json.dumps(obj, indent=2 if pretty else None)

    def export_monthly_index_markdown(self, city: str | None = None) -> str:
        df = self.insights.get_monthly_price_index(city)
        buf = StringIO()
        title = f"# Monthly Price Index{f' — {city}' if city else ''}\n\n"
        buf.write(title)
        buf.write(df.to_markdown(index=False))
        return buf.getvalue()

    def export_monthly_index_excel(self, city: str | None = None) -> BytesIO:
        df = self.insights.get_monthly_price_index(city)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="MonthlyIndex", index=False)
        output.seek(0)
        return output

    def generate_digest_markdown(self, cities: List[str] | None = None) -> str:
        city_idx = self.insights.get_city_price_indices(cities)
        yoy_latest = self.insights.get_cities_yoy(cities)
        top_up = yoy_latest.sort_values("yoy_pct", ascending=False).head(5)
        top_down = yoy_latest.sort_values("yoy_pct", ascending=True).head(5)
        buf = StringIO()
        buf.write("# Expert Digest\n\n")
        buf.write("## City Price Indices\n\n")
        buf.write(city_idx.to_markdown(index=False))
        buf.write("\n\n## YoY — Top Gainers\n\n")
        buf.write(top_up.to_markdown(index=False))
        buf.write("\n\n## YoY — Top Decliners\n\n")
        buf.write(top_down.to_markdown(index=False))
        return buf.getvalue()

    def generate_digest_pdf(self, cities: List[str] | None = None) -> BytesIO:
        city_idx = self.insights.get_city_price_indices(cities)
        yoy_latest = self.insights.get_cities_yoy(cities)
        top_up = yoy_latest.sort_values("yoy_pct", ascending=False).head(5)
        top_down = yoy_latest.sort_values("yoy_pct", ascending=True).head(5)

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Expert Digest", styles["Title"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("City Price Indices", styles["Heading2"]))
        t1 = Table([city_idx.columns.tolist()] + city_idx.values.tolist())
        t1.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ]
            )
        )
        story.append(t1)
        story.append(Spacer(1, 12))

        story.append(Paragraph("YoY — Top Gainers", styles["Heading2"]))
        t2 = Table([top_up.columns.tolist()] + top_up.values.tolist())
        t2.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ]
            )
        )
        story.append(t2)
        story.append(Spacer(1, 12))

        story.append(Paragraph("YoY — Top Decliners", styles["Heading2"]))
        t3 = Table([top_down.columns.tolist()] + top_down.values.tolist())
        t3.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ]
            )
        )
        story.append(t3)

        doc.build(story)
        output.seek(0)
        return output
