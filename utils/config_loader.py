import yaml
from typing import Dict, List
import os

def load_yaml(file_path: str) -> Dict:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_dataset_yaml_path(organization: str, dataset_code: str) -> str:
    return os.path.join('datasets', organization, dataset_code, 'dataset.yaml')

def load_dataset_definition(dataset_code: str, organization: str) -> Dict:
    file_path = get_dataset_yaml_path(organization, dataset_code)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset definition file not found: {file_path}")

    return load_yaml(file_path)

def save_dataset_definition(dataset_name: str, database: str, connection_config: Dict, schema: List[str], organization: str, dataset_code: str):
    dataset_definition = {
        'name': dataset_name,
        'location': database,
        'connection': connection_config,
        'schema': schema
    }
    file_path = get_dataset_yaml_path(organization, dataset_code)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        yaml.dump(dataset_definition, f)