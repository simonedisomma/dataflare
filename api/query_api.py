# api/query_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional, Dict
from data_binding.query_engine import QueryEngine

class QueryModel(BaseModel):
    table: str = ""
    fields: List[str] = []
    filters: List[str] = []
    order_by: List[str] = []
    limit: Optional[int] = None

class QueryAPI:
    def __init__(self, query_engine: QueryEngine):
        self.query_engine = query_engine

    def query(self) -> 'QueryBuilder':
        return QueryBuilder(self)

    def execute(self, query_builder: 'QueryBuilder') -> List[Dict[str, Any]]:
        result = self.query_engine.execute_query(query_builder.build())
        print(f"Debug: Query result before returning: {result}")  
        return result

class QueryBuilder:
    def __init__(self, query_api: QueryAPI):
        self.query_api = query_api
        self.query_model = QueryModel()

    def from_table(self, table: str) -> 'QueryBuilder':
        self.query_model.table = table
        return self

    def select(self, *fields: str) -> 'QueryBuilder':
        self.query_model.fields.extend(fields)
        return self

    def where(self, condition: str) -> 'QueryBuilder':
        self.query_model.filters.append(condition)
        return self

    def order_by(self, *fields: str) -> 'QueryBuilder':
        self.query_model.order_by.extend(fields)
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        self.query_model.limit = limit
        return self

    def build(self) -> QueryModel:
        return self.query_model

app = FastAPI()

@app.post("/query")
async def query(query_model: QueryModel):
    # This is where you would execute the query using your query engine
    # For now, we'll just return the query model as a dict
    return query_model.dict()