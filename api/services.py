from data_binding.database_engine import ConnectionManager
from api.query import QueryModel, QueryBuilder
from typing import List, Dict, Any
import logging
from utils.config_loader import load_config

logger = logging.getLogger(__name__)

class QueryService:
    def __init__(self):
        config = load_config()
        connection_config = config.get('connection', {})
        self.connection_manager = ConnectionManager.create(connection_config)

    def create_query(self) -> QueryBuilder:
        return QueryBuilder()

    def execute_query_on_dataset(self, query_model, organization, dataset):
        try:
            if isinstance(query_model, dict):
                query_model = QueryModel(**query_model)
            
            logger.debug(f"Executing query: {query_model}")
            result = self.connection_manager.execute_query_on_dataset(organization, dataset, query_model)
            return {"result": result, "query_model": query_model.dict()}
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return {"error": str(e), "query_model": query_model.dict() if isinstance(query_model, QueryModel) else query_model}

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