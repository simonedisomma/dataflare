# data_binding/duckdb_binder.py

import duckdb

class DuckDBBinder:
    def __init__(self, database: str):
        self.conn = duckdb.connect(database)

    def bind_all(self, directory: str):
        self.conn.execute(f"CREATE VIEW all_data AS SELECT * FROM parquet_scan('{directory}/*.parquet')")
        print(f"Bound all Parquet files in {directory} to DuckDB view 'all_data'")
