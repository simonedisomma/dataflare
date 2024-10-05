from data_binding.database_engine import ConcreteConnectionManager
from typing import List, Dict, Any
import logging
from utils.config_loader import load_config, load_dataset_definition
import os
import yaml
import json
from datetime import datetime, date

logger = logging.getLogger(__name__)

class QueryService:
    def __init__(self):
        self.connection_managers = {}

    def execute_query_on_dataset(self, query_model: Dict[str, Any], organization: str, dataset: str):
        logger.debug(f"Executing query on {organization}/{dataset}: {query_model}")
        try:
            # Load the dataset definition
            dataset_config = load_dataset_definition(organization, dataset)
            
            # Extract database configuration
            database_config = dataset_config.get('database', {})
            db_type = database_config.get('type')
            
            if not db_type:
                raise ValueError(f"Database type not specified in dataset configuration for {organization}/{dataset}")
            
            # Create or get a connection manager using the dataset config
            connection_key = f"{organization}/{dataset}"
            if connection_key not in self.connection_managers:
                self.connection_managers[connection_key] = ConcreteConnectionManager(database_config)
            
            connection_manager = self.connection_managers[connection_key]
            
            # Ensure query_model is a dictionary
            if not isinstance(query_model, dict):
                query_model = query_model.dict()
            
            # Execute the query
            result = connection_manager.execute_query_on_dataset(organization, dataset, query_model)
            
            # Ensure the result is JSON serializable
            return json.loads(json.dumps(result, default=self._json_serial))
        except FileNotFoundError:
            logger.error(f"Dataset configuration not found for {organization}/{dataset}")
            raise
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

class DatacardService:
    def __init__(self):
        pass

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