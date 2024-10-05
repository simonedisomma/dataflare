from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
from data_binding.connection_factory import ConnectionFactory

logger = logging.getLogger(__name__)

class ConnectionManager(ABC):
    @abstractmethod
    def execute_query_on_dataset(self, organization: str, dataset: str, query_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

class ConcreteConnectionManager(ConnectionManager):
    def __init__(self, database_config):
        self.database_config = database_config
        self.connection_manager = None

    def execute_query_on_dataset(self, organization: str, dataset: str, query_model: Dict[str, Any]):
        logger.debug(f"Executing query on dataset: {organization}/{dataset}")
        logger.debug(f"Query model: {query_model}")
        logger.debug(f"Database config: {self.database_config}")
        
        db_type = self.database_config.get('type')
        
        if not self.connection_manager:
            self.connection_manager = ConnectionFactory.create_connection(db_type, self.database_config)
        
        return self.connection_manager.execute_query_on_dataset(organization, dataset, query_model)

