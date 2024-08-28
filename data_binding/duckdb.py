import os
import duckdb
from typing import List, Any, Dict
from api.services import QueryModel
from data_binding.database_engine import ConnectionManager
from utils.config_loader import load_dataset_definition, save_dataset_definition

class DuckDBConnectionManager(ConnectionManager):
    def __init__(self, connection_config):
        super().__init__(connection_config)
        self.connection = None

    def get_connection(self):
        if not self.connection:
            self.connection = duckdb.connect(self.connection_config.get('database', ':memory:'))
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

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

    def execute_query(self, query_model):
        conn = self.get_connection()
        query = self._build_query(query_model)
        result = conn.execute(query).fetchall()
        return [dict(zip(query_model.select, row)) for row in result]

    def execute_query_on_dataset(self, organization: str, dataset_name: str, query_model: QueryModel):
        query_model.table = dataset_name
        return self.execute_query(query_model)

    def _build_query(self, query_model):
        fields = ', '.join(query_model.select) if query_model.select else '*'
        query = f"SELECT {fields} FROM {query_model.table}"
        
        if query_model.where:
            query += f" WHERE {query_model.where}"
        
        if query_model.order_by:
            query += " ORDER BY " + ", ".join(query_model.order_by)
        
        if query_model.limit:
            query += f" LIMIT {query_model.limit}"
        
        return query

    def _get_all_fields(self, table: str) -> List[str]:
        schema_query = f"PRAGMA table_info({table})"
        schema = self.get_connection().execute(schema_query).fetchall()
        return [col[1] for col in schema]  # col[1] is the column name
