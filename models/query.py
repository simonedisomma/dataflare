
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class QueryModel(BaseModel):
    description: Optional[str] = Field(None, description="Description of the query")
    select: List[str] = Field(default_factory=list, description="Fields to select")
    measures: List[str] = Field(default_factory=list, description="Measures to aggregate")
    dimensions: List[str] = Field(default_factory=list, description="Dimensions to group by")
    where: Optional[str] = Field(None, description="Filter condition")
    order_by: Optional[List[str]] = Field(default_factory=list, description="Fields to order by")
    limit: Optional[int] = Field(None, description="Limit the number of results")
    table: Optional[str] = Field(None, description="Table to query")

class Condition(BaseModel):
    field: str
    operator: str
    value: Union[str, int, float, bool]

class QueryBuilder:
    def __init__(self):
        self.query_model = QueryModel()

    def from_table(self, table: str) -> 'QueryBuilder':
        self.query_model.table = table
        return self

    def select(self, *fields: str) -> 'QueryBuilder':
        self.query_model.select.extend(fields)
        return self

    def measures(self, *fields: str) -> 'QueryBuilder':
        self.query_model.measures.extend(fields)
        self.query_model.select.extend(fields)
        return self

    def dimensions(self, *fields: str) -> 'QueryBuilder':
        self.query_model.dimensions.extend(fields)
        self.query_model.select.extend(fields)
        return self

    def where(self, condition: Union[str, Condition]) -> 'QueryBuilder':
        if isinstance(condition, Condition):
            self.query_model.where = f"{condition.field} {condition.operator} {condition.value}"
        else:
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
