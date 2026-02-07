import pytest
import os
import pandas as pd
import numpy as np
import time
from src.exceptions import TimeoutError
from src.downloader import TaifexDownloader
from src.converter import TaifexConverter
from src.utils import timeout_watchdog
from src.service import ProtectedTaifexService

def test_timeout_watchdog():
    @timeout_watchdog(seconds=1)
    def slow_func():
        time.sleep(2)
        return "done"

    with pytest.raises(TimeoutError, match="Operation slow_func hung"):
        slow_func()

def test_converter_basic(tmp_path):
    csv_file = tmp_path / "test.csv"
    parquet_file = tmp_path / "test.parquet"

    df = pd.DataFrame({
        'Date': ['2024/01/01', '2024/01/02'],
        'Price': [100.5, 101.2],
        'Volume': [10, 20]
    })
    df.to_csv(csv_file, index=False, encoding='ms950')

    conv = TaifexConverter(chunksize=1)
    conv.csv_to_parquet(str(csv_file), str(parquet_file))

    assert os.path.exists(parquet_file)
    df_res = pd.read_parquet(parquet_file)
    assert len(df_res) == 2
    assert 'Price' in df_res.columns
    assert df_res['Price'].iloc[0] == 100.5

def test_converter_large_simulation(tmp_path):
    # Create a "large" CSV with 10k rows (small enough for test, but uses chunks)
    csv_file = tmp_path / "large_test.csv"
    parquet_file = tmp_path / "large_test.parquet"

    df = pd.DataFrame({
        'ID': range(10000),
        'Val': np.random.randn(10000)
    })
    df.to_csv(csv_file, index=False)

    conv = TaifexConverter(chunksize=1000)
    conv.csv_to_parquet(str(csv_file), str(parquet_file))

    assert os.path.exists(parquet_file)
    df_res = pd.read_parquet(parquet_file)
    assert len(df_res) == 10000

def test_downloader_timeout_mock(monkeypatch):
    from requests.exceptions import Timeout

    def mock_get(*args, **kwargs):
        raise Timeout("Mocked timeout")

    import requests
    monkeypatch.setattr(requests.Session, "get", mock_get)

    dl = TaifexDownloader(timeout=0.1)
    with pytest.raises(TimeoutError):
        dl.download("http://example.com", "dummy.zip")

def test_recursive_unzip(tmp_path):
    import zipfile

    # Create nested zip
    inner_csv = tmp_path / "inner.csv"
    inner_csv.write_text("col1,col2\n1,2")

    inner_zip = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip, 'w') as z:
        z.write(inner_csv, arcname="inner.csv")

    outer_zip = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer_zip, 'w') as z:
        z.write(inner_zip, arcname="inner.zip")

    dl = TaifexDownloader()
    extract_dir = tmp_path / "extracted"
    os.makedirs(extract_dir)

    files = dl.unzip(str(outer_zip), str(extract_dir))

    # Should find inner.csv
    found_csv = any("inner.csv" in f for f in files)
    assert found_csv
