from abc import ABC, abstractmethod
from typing import List, Dict, Any
from api.query import QueryModel  
from utils.config_loader import load_dataset_definition

class ConnectionManager(ABC):
    _engines = {}

    @staticmethod
    def create(connection_config: Dict) -> 'ConnectionManager':
        driver = connection_config.get('driver', 'duckdb')
        if driver == 'duckdb':
            from data_binding.duckdb import DuckDBConnectionManager
            return DuckDBConnectionManager(connection_config)
        # Add more drivers here as needed
        raise ValueError(f"Unsupported driver: {driver}")

    def __init__(self, connection_config):
        self.connection_config = connection_config

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def close_connection(self):
        pass

    @abstractmethod
    def register_dataset(self, organization: str, dataset_name: str, schema: List[str]):
        pass

    @abstractmethod
    def add_records(self, organization: str, dataset_name: str, records: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def drop_dataset(self, organization: str, dataset_name: str):
        pass

    @abstractmethod
    def execute_query(self, query_model: QueryModel, dataset_config: dict) -> List[Dict[str, Any]]:
        # Implement the query execution logic here
        # Use both query_model and dataset_config to build and execute the query
        pass

    @abstractmethod
    def execute_query_on_dataset(self, organization: str, dataset_name: str, query_model: QueryModel) -> List[Dict[str, Any]]:
        pass

    @classmethod
    def register(cls, engine_type, engine_class):
        cls._engines[engine_type] = engine_class

    @classmethod
    def create_engine(cls, engine_type, connection_config):
        if engine_type not in cls._engines:
            raise ValueError(f"Unsupported engine type: {engine_type}")
        return cls._engines[engine_type](connection_config)

    def get_connection_manager(self, dataset_config: dict):
        connection_type = dataset_config.get('connection', {}).get('type')
        if connection_type:
            try:
                module_name = f"{connection_type}_engine"
                class_name = f"{connection_type.capitalize()}ConnectionManager"
                module = __import__(module_name, fromlist=[class_name])
                connection_manager_class = getattr(module, class_name)
                return connection_manager_class(dataset_config['connection'])
            except (ImportError, AttributeError):
                raise ValueError(f"Unsupported connection type: {connection_type}")
        else:
            raise ValueError("Connection type not specified in dataset config")

    def execute_query(self, query: str, dataset_config: dict) -> List[Any]:
        connection_manager = self.get_connection_manager(dataset_config)
        with connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
    
