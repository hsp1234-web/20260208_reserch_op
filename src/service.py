from src.utils import timeout_watchdog
from src.converter import TaifexConverter
from src.downloader import TaifexDownloader
import os

class ProtectedTaifexService:
    def __init__(self, timeout=20):
        self.timeout = timeout
        self.downloader = TaifexDownloader(timeout=timeout)
        self.converter = TaifexConverter()

    @timeout_watchdog(20)
    def safe_download(self, url, save_path, **kwargs):
        return self.downloader.download(url, save_path, **kwargs)

    @timeout_watchdog(20)
    def safe_convert(self, csv_path, parquet_path, **kwargs):
        return self.converter.csv_to_parquet(csv_path, parquet_path, **kwargs)

    def process_day(self, url, raw_path, parquet_path, **kwargs):
        """
        Full pipeline for one file with protections.
        """
        print(f"Downloading {url}...")
        self.safe_download(url, raw_path, **kwargs)

        if raw_path.endswith('.zip'):
            print(f"Unzipping {raw_path}...")
            # Unzip might take time, but let's assume it fits in timeout or we need a larger one.
            # Usually unzipping is fast unless it's huge.
            extracted = self.downloader.unzip(raw_path, os.path.dirname(raw_path))
            for f in extracted:
                if f.endswith('.csv'):
                    target_parquet = os.path.join(os.path.dirname(parquet_path),
                                                 os.path.basename(f).replace('.csv', '.parquet'))
                    print(f"Converting {f} to {target_parquet}...")
                    self.safe_convert(f, target_parquet)
        else:
            print(f"Converting {raw_path} to {parquet_path}...")
            self.safe_convert(raw_path, parquet_path)
