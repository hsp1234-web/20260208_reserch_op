import os
import requests
import zipfile
import time
import random
import threading
import chardet
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from src.exceptions import DownloaderError, TimeoutError

class TaifexDownloader:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    ]

    def __init__(self, timeout=120, max_workers=8, min_delay=0.1, max_delay=1.0):
        self.timeout = timeout
        self.max_workers = max_workers
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        self.log_lock = threading.Lock()

    def _get_headers(self, referer=None):
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        if referer:
            headers['Referer'] = referer
        else:
            headers['Referer'] = 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'
        return headers

    def _decode_content(self, content):
        try:
            return content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                return content.decode('ms950')
            except UnicodeDecodeError:
                try:
                    return content.decode('big5')
                except UnicodeDecodeError:
                    encoding = chardet.detect(content)['encoding'] or 'utf-8'
                    return content.decode(encoding, errors='replace')

    def download(self, url, save_path, payload=None, method='GET', referer=None, retries=3):
        """
        Downloads a file with retries, random delay, and UA rotation.
        Includes HTML table parsing fallback.
        """
        dir_name = os.path.dirname(save_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # Random delay to avoid being blocked
        time.sleep(random.uniform(self.min_delay, self.max_delay))

        for attempt in range(retries):
            try:
                headers = self._get_headers(referer)
                if method.upper() == 'GET':
                    response = self.session.get(url, stream=True, timeout=self.timeout, headers=headers)
                else:
                    response = self.session.post(url, data=payload, stream=True, timeout=self.timeout, headers=headers)

                if response.status_code == 200:
                    content_disposition = response.headers.get('Content-Disposition', '')
                    content_type = response.headers.get('Content-Type', '').lower()

                    # If it's explicitly a file attachment or binary
                    if 'attachment' in content_disposition or any(mime in content_type for mime in ['zip', 'csv', 'octet-stream']):
                        with open(save_path, 'wb') as f:
                            for data in response.iter_content(1024*1024):
                                f.write(data)
                        return 'success', save_path

                    # Check for HTML content (could be a table or a "No Data" page)
                    if 'text/html' in content_type:
                        full_content = response.content
                        decoded_content = self._decode_content(full_content)

                        if "查無資料" in decoded_content or len(decoded_content.strip()) < 100:
                            return 'not_found', "No Data found in HTML"

                        soup = BeautifulSoup(decoded_content, 'html.parser')
                        # Look for common TAIFEX table classes
                        table = soup.find('table', {'class': 'table_f'}) or \
                                soup.find('table', {'class': 'table_a'}) or \
                                soup.find('table')

                        if table:
                            rows = []
                            for tr in table.find_all('tr'):
                                cells = tr.find_all(['td', 'th'])
                                if cells:
                                    row = [cell.get_text(strip=True).replace(',', '') for cell in cells]
                                    rows.append(",".join(row))

                            data_to_save = "\n".join(rows)
                            if data_to_save.strip():
                                with open(save_path, 'w', encoding='utf-8-sig') as f:
                                    f.write(data_to_save)
                                return 'success', save_path

                        return 'not_found', "HTML response without identifiable table"

                    # Default: save as binary
                    with open(save_path, 'wb') as f:
                        for data in response.iter_content(1024*1024):
                            f.write(data)
                    return 'success', save_path

                elif response.status_code == 404:
                    return 'not_found', "404 Not Found"
                else:
                    if attempt < retries - 1:
                        time.sleep(2 * (attempt + 1))
                        continue
                    return 'error', f"HTTP {response.status_code}"

            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return 'timeout', "Request timed out"
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return 'error', str(e)

        return 'error', "Max retries reached"

    def run_parallel(self, tasks):
        """
        Executes a list of download tasks in parallel.
        Each task is a dict: {url, save_path, payload, method, referer, task_name}
        """
        results = []
        with tqdm(total=len(tasks), desc="Downloading") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {
                    executor.submit(self.download,
                                   t['url'], t['save_path'],
                                   t.get('payload'), t.get('method', 'GET'),
                                   t.get('referer')): t
                    for t in tasks
                }
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        status, message = future.result()
                        results.append({
                            'task': task,
                            'status': status,
                            'message': message
                        })
                        if status != 'success' and status != 'not_found':
                             with self.log_lock:
                                 print(f"Failed: {task.get('task_name')} - {message}")
                    except Exception as e:
                        results.append({
                            'task': task,
                            'status': 'exception',
                            'message': str(e)
                        })
                    pbar.update(1)
        return results

    def unzip(self, zip_path, extract_to, delete_zip=False):
        """
        Unzips a file to a directory. Handles recursive unzipping.
        """
        if not zipfile.is_zipfile(zip_path):
            return [zip_path]

        extracted_files = []
        try:
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
        except Exception as e:
            print(f"Failed to unzip {zip_path}: {e}")
            return [zip_path]

        if delete_zip:
            os.remove(zip_path)

        return extracted_files
