from abc import ABC, abstractmethod
from typing import List, Any

class QueryEngine(ABC):
    @abstractmethod
    def execute_query(self, query: str) -> List[Any]:
        pass