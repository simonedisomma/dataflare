# data_storage/parquet_storage.py

import pandas as pd
import os

class ParquetStorage:
    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save(self, name: str, data: pd.DataFrame):
        path = os.path.join(self.directory, f"{name}.parquet")
        data.to_parquet(path, index=False)
        print(f"Saved {name} to {path}")
