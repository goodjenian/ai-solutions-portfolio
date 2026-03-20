from pathlib import Path
from typing import List, Union

import pandas as pd

from data.csv_loader import DataLoaderCsv
from data.providers.base import BaseDataProvider
from data.schemas import Property


class CSVDataProvider(BaseDataProvider):
    """Data provider for CSV and Excel files."""

    def __init__(self, source: Union[str, Path]):
        super().__init__(source)
        self._loader = DataLoaderCsv(source)

    def validate_source(self) -> bool:
        """Check if the source file or URL exists."""
        return self._loader.csv_path is not None

    def load_data(self) -> pd.DataFrame:
        """Load data from the CSV/Excel source."""
        if self._cache is not None:
            return self._cache

        df = self._loader.load_df()
        # Ensure it is formatted according to our schema rules
        self._cache = self._loader.format_df(df)
        return self._cache

    def get_properties(self) -> List[Property]:
        """Convert loaded data to Property objects."""
        df = self.load_data()
        properties = []

        for _, row in df.iterrows():
            try:
                # Convert row to dict and filter out None/NaN values that might break validation
                # if the schema has strict defaults or optionals.
                # However, Property schema usually handles Optional fields.
                # We need to ensure required fields are present.

                data = row.to_dict()

                # Handle potential NaN values for optional fields if Pydantic expects None
                clean_data = {k: v for k, v in data.items() if pd.notna(v)}

                # Basic mapping if needed, but format_df does most heavy lifting.
                # We might need to handle specific types like 'image_urls' which might be strings in CSV
                if "image_urls" in clean_data and isinstance(clean_data["image_urls"], str):
                    # Simple split if it's a comma-separated string, or keep as is if schema expects list
                    # Assuming simple case for now or that format_df handled it (it doesn't seem to parse lists)
                    clean_data["image_urls"] = [
                        url.strip() for url in clean_data["image_urls"].split(",")
                    ]

                # Create Property object
                # Note: We rely on Pydantic's validation here.
                # If validation fails, we skip the property or log warning.
                # For now, let's skip invalid rows to avoid crashing the whole batch.
                prop = Property(**clean_data)
                properties.append(prop)
            except Exception:
                # In a real scenario, we might want to log this
                continue

        return properties
