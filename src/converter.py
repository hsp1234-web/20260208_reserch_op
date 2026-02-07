import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
from src.exceptions import ConverterError

class TaifexConverter:
    def __init__(self, chunksize=100000):
        self.chunksize = chunksize

    def csv_to_parquet(self, csv_path, parquet_path, encoding=None):
        """
        Converts a large CSV to Parquet in chunks to save memory.
        """
        if encoding is None:
            encoding = self.detect_encoding(csv_path)

        try:
            # Some TAIFEX files might have empty lines or comments at the end.
            # We use on_bad_lines='skip' or similar if needed.
            reader = pd.read_csv(csv_path, encoding=encoding, chunksize=self.chunksize,
                                 low_memory=False, on_bad_lines='warn')

            writer = None

            for chunk in reader:
                # Clean up column names (strip spaces and remove empty columns)
                chunk.columns = [str(c).strip() for c in chunk.columns]
                chunk = chunk.loc[:, ~chunk.columns.str.contains('^Unnamed')]

                # Basic data cleaning: strip string columns
                for col in chunk.select_dtypes(['object']).columns:
                    chunk[col] = chunk[col].astype(str).str.strip()

                # Convert to arrow table
                table = pa.Table.from_pandas(chunk)

                if writer is None:
                    writer = pq.ParquetWriter(parquet_path, table.schema, compression='snappy')

                writer.write_table(table)

            if writer:
                writer.close()
            else:
                raise ConverterError("No data found in CSV.")

            return parquet_path
        except Exception as e:
            if os.path.exists(parquet_path):
                os.remove(parquet_path)
            raise ConverterError(f"Failed to convert {csv_path} to parquet: {e}")

    def detect_encoding(self, file_path):
        import chardet
        with open(file_path, 'rb') as f:
            rawdata = f.read(10000)
            result = chardet.detect(rawdata)
            encoding = result['encoding']

        # Normalize common TAIFEX encodings
        if encoding is None or encoding.lower() in ['ascii', 'windows-1252']:
            # Check for Big5
            for enc in ['utf-8-sig', 'ms950', 'big5']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        f.readline()
                    return enc
                except:
                    continue
            return 'ms950'

        return encoding
