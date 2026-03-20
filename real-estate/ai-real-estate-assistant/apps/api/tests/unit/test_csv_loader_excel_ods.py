from types import SimpleNamespace

import pandas as pd

from data.csv_loader import DataLoaderExcel


def test_excel_get_sheet_names_ods_primary(monkeypatch):
    doc = SimpleNamespace(spreadsheets={"ODSMain": object()})

    import odf.opendocument

    monkeypatch.setattr(odf.opendocument, "load", lambda *_args, **_kwargs: doc)
    loader = DataLoaderExcel("fake.ods")
    assert loader.get_sheet_names() == ["ODSMain"]


def test_excel_get_sheet_names_ods_fallback(monkeypatch):
    class ExcelFile:
        sheet_names = ["ODS1"]

        def close(self):
            return None

    import odf.opendocument

    monkeypatch.setattr(
        odf.opendocument, "load", lambda *_args, **_kwargs: (_ for _ in ()).throw(ImportError())
    )
    monkeypatch.setattr(pd, "ExcelFile", lambda *_args, **_kwargs: ExcelFile())
    loader = DataLoaderExcel("fake.ods")
    assert loader.get_sheet_names() == ["ODS1"]
