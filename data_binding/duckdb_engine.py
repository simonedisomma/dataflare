import duckdb
from typing import List, Any, Dict
from data_binding.query_engine import QueryEngine
from api.query_api import QueryModel

class DuckDBEngine(QueryEngine):
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path)

    def execute_query(self, query_model: QueryModel) -> List[Dict[str, Any]]:
        sql_query = self._build_sql_query(query_model)
        result = self.conn.execute(sql_query).fetchall()
        print(f"Debug: DuckDB query result: {result}")  # Add this line
        return [dict(zip(query_model.fields or self._get_all_fields(query_model.table), row)) for row in result]

    def _build_sql_query(self, query_model: QueryModel) -> str:
        fields = ', '.join(query_model.fields) if query_model.fields else '*'
        query = f"SELECT {fields} FROM {query_model.table}"
        
        if query_model.filters:
            query += " WHERE " + " AND ".join(query_model.filters)
        
        if query_model.order_by:
            query += " ORDER BY " + ", ".join(query_model.order_by)
        
        if query_model.limit:
            query += f" LIMIT {query_model.limit}"
        
        return query

    def _get_all_fields(self, table: str) -> List[str]:
        schema_query = f"PRAGMA table_info({table})"
        schema = self.conn.execute(schema_query).fetchall()
        return [col[1] for col in schema]  # col[1] is the column name
    
    def create_table(self, table_name: str, columns: List[str]) -> None:
        columns_definition = ", ".join(columns)
        query = f"CREATE TABLE {table_name} ({columns_definition})"
        self.conn.execute(query)
        print(f"Created table '{table_name}' with columns: {columns}")

    def insert_data(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        if not data:
            print(f"No data to insert into table '{table_name}'")
            return

        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?" for _ in data[0]])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        values = [tuple(row.values()) for row in data]
        self.conn.executemany(query, values)
        print(f"Inserted {len(data)} rows into table '{table_name}'")