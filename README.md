# 台灣期交所 (TAIFEX) 數據整合研究計畫

本專案旨在建立一個穩定、高效且具備自我保護機制的台灣期權數據處理管道。特別針對大數據量（如逐筆成交資料 Tick Data）進行優化，確保在有限的記憶體資源下不會當機，並提供掛起保護機制。

## 🌟 核心功能

1.  **記憶體安全 (Memory Efficiency)**：
    *   使用 Pandas 的 `chunksize` 機制進行分塊讀取與轉換，處理數 GB 的 CSV 檔案時僅需消耗極小記憶體。
    *   採用串流下載 (Streaming Download)，避免大檔案在下載時擠爆記憶體。
2.  **掛起保護機制 (Timeout Watchdog)**：
    *   內建 20 秒超時保護。若下載或轉換操作卡住超過 20 秒，系統將自動拋出 `TimeoutError` 並釋放資源，防止環境死機。
3.  **自動化處理**：
    *   支援 ZIP 檔案的自動解壓，並具備遞迴解壓功能（處理 ZIP 內的 ZIP）。
    *   自動偵測檔案編碼（支援 `MS950`, `Big5`, `UTF-8-sig`）。
4.  **高效儲存**：
    *   將原始資料轉換為 Parquet 格式，大幅縮小檔案體積並提升回測時的讀取速度。

## 📁 專案結構

```text
.
├── src/
│   ├── downloader.py    # 下載與解壓模組 (支援串流與遞迴解壓縮)
│   ├── converter.py     # 資料轉換模組 (Pandas 分塊處理)
│   ├── service.py       # 高階整合服務 (包含保護機制)
│   ├── utils.py         # 工具程式 (Watchdog 裝飾器)
│   └── exceptions.py    # 自定義異常處理
├── tests/
│   └── test_taifex.py   # 單元測試 (pytest)
├── data/
│   ├── raw/             # 原始資料存放處
│   └── parquet/         # 轉換後的 Parquet 檔案
└── README.md            # 本說明文件
```

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install pandas pyarrow requests pytest psutil tqdm chardet
```

### 2. 使用範例
使用 `ProtectedTaifexService` 進行具備保護機制的數據處理：

```python
from src.service import ProtectedTaifexService

# 初始化服務，設定 20 秒超時保護
service = ProtectedTaifexService(timeout=20)

# 下載並轉換範例 (以 Put/Call Ratio 為例)
url = "https://www.taifex.com.tw/cht/3/dlPcRatioDown"
service.process_day(
    url=url,
    raw_path="data/raw/pc_ratio.csv",
    parquet_path="data/parquet/pc_ratio.parquet",
    payload={'queryStartDate': '2025/02/05', 'queryEndDate': '2025/02/05'},
    method='POST'
)
```

### 3. 執行測試
確保所有功能正常運作：
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest tests/test_taifex.py
```

## 🛠 技術細節
*   **語言**: Python 3
*   **數據處理**: Pandas + PyArrow
*   **保護機制**: Thread-based Watchdog + Requests Timeout
*   **儲存格式**: Apache Parquet (Snappy 壓縮)

## 📝 後續計畫
*   開發台指期與選擇權的價差單策略分析。
*   實作回測引擎比較「價差單策略」與「買進持有」的績效。
