from typing import Dict, Any

class ConnectionFactory:
    @staticmethod
    def create_connection(db_type: str, config: Dict[str, Any]):
        if db_type == 'duckdb':
            from data_binding.duckdb import DuckDBConnectionManager
            return DuckDBConnectionManager(config)
        # Add other database types here as needed
        else:
            raise ValueError(f"Unsupported database type: {db_type}")