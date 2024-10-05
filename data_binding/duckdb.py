import os
import duckdb
from typing import List, Any, Dict
from data_binding.database_engine import ConnectionManager
from utils.config_loader import load_dataset_definition, save_dataset_definition
from datetime import datetime, date

class DuckDBConnectionManager(ConnectionManager):
    def __init__(self, connection_config):
        super().__init__()
        self.connection_config = connection_config
        self.connection = None

    def get_connection(self):
        if not self.connection:
            self.connection = duckdb.connect(self.connection_config.get('database', ':memory:'))
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def register_parquet_file(self, file_path: str, table_name: str):
        conn = self.get_connection()
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM parquet_scan('{file_path}')")

    def register_dataset(self, organization: str, dataset_name: str, schema: List[str]):
        conn = self.get_connection()
        schema_str = ', '.join(schema)
        conn.execute(f"CREATE TABLE IF NOT EXISTS {dataset_name} ({schema_str})")
        # Save the dataset definition
        save_dataset_definition(organization=organization, dataset_code=dataset_name, dataset_name=dataset_name, database=dataset_name,connection_config=self.connection_config.get('database', ':memory:'), schema=schema)

    def add_records(self, organization: str, dataset_name: str, records: List[Dict[str, Any]]):
        conn = self.get_connection()
        if records:
            columns = ', '.join(records[0].keys())
            values = [tuple(record.values()) for record in records]
            placeholders = ', '.join(['?' for _ in records[0]])
            query = f"INSERT INTO {dataset_name} ({columns}) VALUES ({placeholders})"
            conn.executemany(query, values)

    def drop_dataset(self, organization: str, dataset_name: str):
        conn = self.get_connection()
        conn.execute(f"DROP TABLE IF EXISTS {dataset_name}")

    def execute_query_on_dataset(self, organization: str, dataset_name: str, query_model: Dict[str, Any]):
        # Load dataset configuration
        dataset_config = load_dataset_definition(organization, dataset_name)
        database_config = dataset_config.get('database', {})
        
        # Register parquet file if it exists
        parquet_file = database_config.get('file')
        table_name = database_config.get('table', dataset_name)
        if parquet_file:
            full_path = os.path.join('datasets', organization, dataset_name, 'data', parquet_file)
            self.register_parquet_file(full_path, table_name)
        
        # Set the table name in the query model
        query_model['table'] = table_name
        
        return self.execute_query(query_model)

    def execute_query(self, query_model):
        conn = self.get_connection()
        query = self._build_query(query_model)
        result = conn.execute(query).fetchall()
        columns = self._get_query_columns(query_model)
        return [self._serialize_row(dict(zip(columns, row))) for row in result]

    def _build_query(self, query_model):
        fields = self._get_query_columns(query_model)
        fields_str = ', '.join(fields)
        query = f"SELECT {fields_str} FROM {query_model['table']}"
        
        if 'where' in query_model:
            query += f" WHERE {query_model['where']}"
        
        if 'order_by' in query_model:
            order_by = query_model['order_by']
            if isinstance(order_by, list):
                order_by = ', '.join(order_by)
            query += f" ORDER BY {order_by}"
        
        if 'limit' in query_model:
            query += f" LIMIT {query_model['limit']}"
        
        return query

    def _get_query_columns(self, query_model):
        if 'select' in query_model:
            return query_model['select']
        elif 'measures' in query_model or 'dimensions' in query_model:
            measures = query_model.get('measures', [])
            dimensions = query_model.get('dimensions', [])
            return measures + dimensions
        else:
            return ['*']

    def _get_all_fields(self, table: str) -> List[str]:
        schema_query = f"PRAGMA table_info({table})"
        schema = self.get_connection().execute(schema_query).fetchall()
        return [col[1] for col in schema]  # col[1] is the column name

    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {k: self._serialize_value(v) for k, v in row.items()}

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
