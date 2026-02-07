import os
import requests
import zipfile
import time
from tqdm import tqdm

from src.exceptions import DownloaderError, TimeoutError

class TaifexDownloader:
    def __init__(self, timeout=20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'
        })

    def download(self, url, save_path, payload=None, method='GET', headers=None):
        """
        Downloads a file from url to save_path with a hang-protection timeout.
        """
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            if method.upper() == 'GET':
                response = self.session.get(url, stream=True, timeout=self.timeout, headers=request_headers)
            else:
                response = self.session.post(url, data=payload, stream=True, timeout=self.timeout, headers=request_headers)

            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB

            with open(save_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    if not data:
                        break
                    f.write(data)

            return save_path
        except requests.exceptions.Timeout:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise TimeoutError(f"Download timed out after {self.timeout} seconds of inactivity.")
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise DownloaderError(f"Failed to download {url}: {e}")

    def unzip(self, zip_path, extract_to, delete_zip=False):
        """
        Unzips a file to a directory. Handles recursive unzipping.
        """
        if not zipfile.is_zipfile(zip_path):
            return [zip_path]

        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            for file_name in zip_ref.namelist():
                full_path = os.path.join(extract_to, file_name)
                if zipfile.is_zipfile(full_path):
                    # Recursive unzip
                    nested_dir = os.path.join(extract_to, f"{file_name}_extracted")
                    os.makedirs(nested_dir, exist_ok=True)
                    extracted_files.extend(self.unzip(full_path, nested_dir, delete_zip=True))
                else:
                    extracted_files.append(full_path)

        if delete_zip:
            os.remove(zip_path)

        return extracted_files
