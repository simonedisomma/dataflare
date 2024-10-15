import pandas as pd
from typing import List, Dict
from utils.config_loader import load_dataset_definition
from services.query import QueryService
from models.query import QueryModel
from pydantic import BaseModel, Field
import logging
import os
import yaml

logger = logging.getLogger(__name__)

class DataFrameService:

    def load_dataset(self, dataset_with_org: str) -> pd.DataFrame:
        
        organization, dataset_code = dataset_with_org.split('/', 1)

        print(f"Loading dataset: {dataset_with_org}")
        print(f"Organization: {organization}")
        print(f"Dataset code: {dataset_code}")
        
        # Load dataset definition
        dataset_def = load_dataset_definition(dataset_code=dataset_code, organization=organization)
        
        # Create a query that selects all measures and dimensions, and includes other query parameters
        query_model = QueryModel(
            dataset=dataset_code,
            organization=organization,
            select=dataset_def.get('measures', []) + dataset_def.get('dimensions', []),
            filters=dataset_def.get('filters', []),
            order=dataset_def.get('order', []),
            limit=dataset_def.get('limit')
        )
        # Execute the query
        if self.query_service is None:
            raise ValueError("QueryService is not initialized. Please ensure it's properly set up.")
        result = self.query_service.execute_query_on_dataset(query_model, organization, dataset_code)
        
        # Convert the result to a DataFrame
        if not result:
            return pd.DataFrame()  # Return an empty DataFrame if no results
        return pd.DataFrame(result)

    def query_dataset(self, dataset_with_org: str, select: List[str] = None, filters: List[Dict] = None, 
              order: List[str] = None, limit: int = None) -> pd.DataFrame:
        
        organization, dataset_code = dataset_with_org.split('/', 1)
        
        logger.debug(f"Querying dataset: {dataset_with_org}")
        logger.debug(f"Organization: {organization}")
        logger.debug(f"Dataset code: {dataset_code}")
        
        query_model = QueryModel(
            select=select or [],
            dataset=dataset_code,
            organization=organization,
            filters=filters or [],
            order=order or [],
            limit=limit
        )

        # Load dataset definition
        dataset_def = load_dataset_definition(dataset_code=dataset_code, organization=organization)
        


        # If select is provided, split it into measures and dimensions
        if select:
            measures = dataset_def.get('measures', [])
            dimensions = dataset_def.get('dimensions', [])
            
            query_model.measures = [field for field in select if field in measures]
            query_model.dimensions = [field for field in select if field in dimensions]
        
        # Execute the query
        query_service = QueryService()
        result = query_service.execute_query_on_dataset(query_model,dataset=dataset_code, organization=organization)
        
        # Convert the result to a DataFrame
        return pd.DataFrame(result)

    def get_dataset_metadata(self, dataset_with_org: str) -> Dict:
        organization, dataset_code = dataset_with_org.split('/', 1)
        
        logger.debug(f"Getting metadata for dataset: {dataset_with_org}")
        
        # Load dataset definition
        dataset_def = load_dataset_definition(dataset_code=dataset_code, organization=organization)
        
        # Extract field names and data types
        fields = dataset_def.get('measures', []) + dataset_def.get('dimensions', [])
        field_types = dataset_def.get('field_types', {})
        
        metadata = {
            'fields': fields,
            'field_types': field_types,
            'measures': dataset_def.get('measures', []),
            'dimensions': dataset_def.get('dimensions', [])
        }
        
        return metadata
    
    def save_dataset(self, dataset_with_org: str, dataframe: pd.DataFrame) -> None:
        organization, dataset_code = dataset_with_org.split('/', 1)
        
        logger.debug(f"Saving dataset: {dataset_with_org}")
        logger.debug(f"Organization: {organization}")
        logger.debug(f"Dataset code: {dataset_code}")
        
        # Create the dataset directory if it doesn't exist
        os.makedirs(f"datasets/{organization}/{dataset_code}/data", exist_ok=True)
        
        # Save in a parquet file, overwriting if it exists
        parquet_path = f"datasets/{organization}/{dataset_code}/data/data.parquet"
        dataframe.to_parquet(parquet_path, index=False)
        logger.info(f"Dataset saved to {parquet_path}")

        # Prepare the metadata
        metadata = {
            'title': f"{dataset_code.replace('_', ' ').title()} Dataset",
            'subtitle': f"Data for {organization} {dataset_code}",
            'fields': dataframe.columns.tolist(),
            'measures': [col for col in dataframe.select_dtypes(include=['int64', 'float64']).columns],
            'dimensions': [col for col in dataframe.select_dtypes(include=['object', 'datetime64']).columns],
            'field_types': {col: str(dtype) for col, dtype in dataframe.dtypes.items()},
            'sources': [
                {
                    'name': f"{organization} {dataset_code} Data Source",
                    'link': f"https://example.com/{organization}/{dataset_code}"
                }
            ],
            'database': {
                'type': 'duckdb',
                'file': 'data.parquet',
                'table': dataset_code
            }
        }

        # Save or update the metadata as a YAML file
        yaml_path = f"datasets/{organization}/{dataset_code}/dataset.yaml"
        if os.path.exists(yaml_path):
            # If the file exists, load it and update only the necessary fields
            with open(yaml_path, 'r') as f:
                existing_metadata = yaml.safe_load(f)
            existing_metadata.update(metadata)
            metadata = existing_metadata

        with open(yaml_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)

        logger.info(f"Dataset metadata saved/updated for {dataset_with_org}")

# Monkey-patch pandas to add these methods
def load_dataset(dataset_with_organization: str) -> pd.DataFrame:
    return pd.app_context.dataframe_service.load_dataset(dataset_with_organization)

def query_dataset(dataset: str, select: List[str] = None, filters: List[Dict] = None, 
          order: List[str] = None, limit: int = None) -> pd.DataFrame:
    return pd.app_context.dataframe_service.query_dataset(dataset, select, filters, order, limit)

def get_dataset_metadata(dataset_with_organization: str) -> Dict:
    return pd.app_context.dataframe_service.get_dataset_metadata(dataset_with_organization)

def save_dataset(dataset_with_organization: str, dataframe: pd.DataFrame) -> None:
    return pd.app_context.dataframe_service.save_dataset(dataset_with_organization, dataframe)

pd.load_dataset = load_dataset
pd.query_dataset = query_dataset
pd.get_dataset_metadata = get_dataset_metadata
pd.save_dataset = save_dataset