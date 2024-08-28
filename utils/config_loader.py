import yaml
from typing import Dict, List
import os

DEFAULT_CONFIG_PATH = 'config/config.yaml'

def load_yaml(file_path: str) -> Dict:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict:
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root
    project_root = os.path.dirname(current_dir)
    # Construct the full path
    full_path = os.path.join(project_root, config_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Config file not found: {full_path}")
    return load_yaml(full_path)

def get_dataset_yaml_path(organization: str, dataset_code: str) -> str:
    return os.path.join('datasets', organization, dataset_code, 'dataset.yaml')

def load_dataset_definition(organization: str, dataset_code: str) -> Dict:
    #debug line
    print(f"Loading dataset definition for {organization}/{dataset_code}")
    with open(get_dataset_yaml_path(organization, dataset_code), 'r') as f:
        return yaml.safe_load(f)

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