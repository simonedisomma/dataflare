from data_binding.duckdb_engine import DuckDBEngine

class DuckDBBinder:
    def __init__(self, database: str):
        self.engine = DuckDBEngine(database)

    def bind_all(self, directory: str):
        self.engine.execute_query(f"CREATE VIEW all_data AS SELECT * FROM parquet_scan('{directory}/*.parquet')")
        print(f"Bound all Parquet files in {directory} to DuckDB view 'all_data'")

    def get_query_engine(self) -> DuckDBEngine:
        return self.engine