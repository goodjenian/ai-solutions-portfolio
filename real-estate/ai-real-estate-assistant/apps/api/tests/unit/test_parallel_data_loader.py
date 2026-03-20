from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from utils.data_loader import ParallelDataLoader


class TestParallelDataLoader:
    @pytest.fixture
    def mock_loader_csv(self):
        with patch("utils.data_loader.DataLoaderCsv") as MockClass:
            yield MockClass

    @pytest.fixture
    def mock_property_collection(self):
        with patch("utils.data_loader.PropertyCollection") as MockClass:
            yield MockClass

    def test_load_files_parallel(self, mock_loader_csv, mock_property_collection):
        # Setup mocks
        file1 = MagicMock()
        file1.name = "file1.csv"
        file2 = MagicMock()
        file2.name = "file2.csv"

        # Mock pandas read_csv
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame({"col": [1]})
            mock_read_csv.return_value = mock_df

            mock_loader_csv.format_df.return_value = mock_df

            mock_collection = MagicMock()
            mock_property_collection.from_dataframe.return_value = mock_collection

            loader = ParallelDataLoader(max_workers=2)
            results = loader.load_files([file1, file2])

            assert len(results) == 2
            assert mock_read_csv.call_count == 2
            assert mock_loader_csv.format_df.call_count == 2
            assert mock_property_collection.from_dataframe.call_count == 2

    def test_load_files_error_handling(self, mock_loader_csv):
        # Setup mocks to fail for one file
        file1 = MagicMock()
        file1.name = "file1.csv"

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = Exception("Read error")

            loader = ParallelDataLoader(max_workers=1)
            results = loader.load_files([file1])

            # Should not crash, just return empty list or partial results
            assert len(results) == 0

    def test_process_single_file_excel(self, mock_loader_csv):
        file = MagicMock()
        file.name = "test.xlsx"

        with patch("pandas.read_excel") as mock_read_excel:
            loader = ParallelDataLoader()
            loader._process_single_file(file)
            mock_read_excel.assert_called_once()

    def test_load_files_calls_progress_callback(self, mock_loader_csv, mock_property_collection):
        file1 = MagicMock()
        file1.name = "file1.csv"
        file2 = MagicMock()
        file2.name = "file2.csv"

        progress_updates = []

        def cb(progress: float, message: str) -> None:
            progress_updates.append((progress, message))

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame({"col": [1]})
            mock_read_csv.return_value = mock_df
            mock_loader_csv.format_df.return_value = mock_df

            mock_collection = MagicMock()
            mock_property_collection.from_dataframe.return_value = mock_collection

            loader = ParallelDataLoader(max_workers=2)
            loader.load_files([file1, file2], progress_callback=cb)

        assert len(progress_updates) == 2
        assert progress_updates[-1][0] == 1.0
        assert "Processed" in progress_updates[-1][1]

    def test_process_single_file_seeks_before_reading(self, mock_loader_csv):
        file = MagicMock()
        file.name = "test.csv"

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"col": [1]})
            loader = ParallelDataLoader()
            loader._process_single_file(file)

        file.seek.assert_called_once_with(0)
