from data_binding.database_engine import ConnectionManager
from api.query import QueryModel, QueryBuilder
from typing import List, Dict, Any
import logging
import yaml
import os

logger = logging.getLogger(__name__)

class QueryService:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def create_query(self) -> QueryBuilder:
        return QueryBuilder()

    def execute_query(self, query_model: QueryModel) -> List[Dict[str, Any]]:
        result = self.connection_manager.execute_query(query_model)
        print(f"Debug: Query result before returning: {result}")
        return result
    
    def execute_query_on_dataset(self, query_model: QueryModel, organization: str, dataset_name: str) -> List[Dict[str, Any]]:
        logger.debug(f"Executing query on dataset: {organization}/{dataset_name}")
        logger.debug(f"Query model: {query_model}")
        try:
            result = self.connection_manager.execute_query_on_dataset(organization, dataset_name, query_model)
            logger.debug(f"Query result: {result}")
            return result
        except Exception as e:
            logger.exception(f"Error executing query: {str(e)}")
            raise

class DatacardService:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def get_datacard(self, organization: str, definition: str) -> Dict[str, Any]:
        logger.debug(f"Attempting to get datacard for {organization}/{definition}")
        try:
            # Construct the path to the YAML file
            file_path = os.path.join('datacards', organization, f"{definition}.yml")
            logger.debug(f"Looking for datacard file at: {file_path}")

            # Check if the file exists
            if not os.path.exists(file_path):
                logger.error(f"Datacard file not found: {file_path}")
                raise FileNotFoundError(f"Datacard file not found: {file_path}")

            # Read and parse the YAML file
            with open(file_path, 'r') as file:
                datacard_definition = yaml.safe_load(file)
            
            logger.debug(f"Successfully loaded datacard: {datacard_definition}")
            return datacard_definition
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {str(e)}")
            raise ValueError(f"Error parsing YAML file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_datacard: {str(e)}")
            raise