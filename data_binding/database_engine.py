from abc import ABC, abstractmethod
from typing import List, Dict, Any
from api.query import QueryModel
from utils.config_loader import load_dataset_definition
import logging

logger = logging.getLogger(__name__)

class ConnectionManager(ABC):
    @classmethod
    def create(cls, connection_config):
        # This method should return an instance of a concrete ConnectionManager
        # based on the connection_config. For now, we'll just return ConcreteConnectionManager
        return ConcreteConnectionManager(connection_config)

    @abstractmethod
    def execute_query_on_dataset(self, organization: str, dataset_name: str, query_model: QueryModel) -> List[Dict[str, Any]]:
        pass

class ConcreteConnectionManager(ConnectionManager):
    def __init__(self, connection_config):
        self.connection_config = connection_config

    def execute_query_on_dataset(self, organization: str, dataset_name: str, query_model: QueryModel):
        logger.debug(f"Executing query on dataset: {organization}/{dataset_name}")
        logger.debug(f"Query model: {query_model}")
        
        dataset_config = load_dataset_definition(organization, dataset_name)
        
        # Here, you would implement the logic to execute the query using the query_model
        # and dataset_config. This might involve creating a connection to the database,
        # translating the query_model into a format your database understands, and executing it.
        
        # For now, we'll return a dummy result
        return [{"date": "2023-01-01", "state": "California", "unemployment_rate": 5.5},
                {"date": "2023-01-01", "state": "New York", "unemployment_rate": 5.2}]

