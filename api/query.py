from pydantic import BaseModel, Field
from typing import List, Optional

class QueryModel(BaseModel):
    description: Optional[str] = Field(None, description="Description of the query")
    select: List[str] = Field(default_factory=list)
    where: Optional[str] = None
    order_by: Optional[List[str]] = Field(default_factory=list)
    limit: Optional[int] = None
    table: Optional[str] = None

class QueryBuilder:
    def __init__(self):
        self.query_model = QueryModel()

    def from_table(self, table: str) -> 'QueryBuilder':
        self.query_model.table = table
        return self

    def select(self, *fields: str) -> 'QueryBuilder':
        self.query_model.select.extend(fields)
        return self

    def where(self, condition: str) -> 'QueryBuilder':
        self.query_model.where = condition
        return self

    def order_by(self, *fields: str) -> 'QueryBuilder':
        self.query_model.order_by.extend(fields)
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        self.query_model.limit = limit
        return self

    def build(self) -> QueryModel:
        return self.query_model