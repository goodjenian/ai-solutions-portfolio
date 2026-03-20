"""
Base Data Provider Interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from data.schemas import Property


class BaseDataProvider(ABC):
    """
    Abstract base class for data providers.

    All data sources (CSV, API, Database) must implement this interface.
    """

    def __init__(self, source: Union[str, Path]):
        self.source = source
        self._cache: Optional[pd.DataFrame] = None

    @abstractmethod
    def validate_source(self) -> bool:
        """Check if the source is valid and accessible."""
        pass

    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """
        Load data from the source into a pandas DataFrame.

        Returns:
            pd.DataFrame: The loaded data.
        """
        pass

    async def aload_data(self) -> pd.DataFrame:
        """
        Asynchronously load data.

        Default implementation wraps synchronous load.
        Subclasses should override for true async support.
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.load_data)

    @abstractmethod
    def get_properties(self) -> List[Property]:
        """
        Get data as a list of Property objects (validated).

        Returns:
            List[Property]: List of validated property objects.
        """
        pass
