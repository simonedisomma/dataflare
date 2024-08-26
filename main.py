# main.py

import yaml
import os
from importlib.util import spec_from_file_location, module_from_spec
from workflow_manager.manager import WorkflowManager
from data_storage.parquet_storage import ParquetStorage
from data_binding.duckdb_binder import DuckDBBinder
from api.query_api import QueryAPI

def load_dataset_config(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def load_workflow_class(workflow_path: str, class_name: str):
    spec = spec_from_file_location("workflow_module", workflow_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

def discover_datasets(base_path: str = 'datasets'):
    for root, dirs, files in os.walk(base_path):
        if 'config.yaml' in files:
            yield os.path.join(root, 'config.yaml')

def initialize_workflows(datasets_path: str) -> WorkflowManager:
    manager = WorkflowManager()
    for config_path in discover_datasets(datasets_path):
        dataset_config = load_dataset_config(config_path)
        workflow_path = os.path.join(os.path.dirname(config_path), dataset_config['workflow']['file'])
        workflow_class = load_workflow_class(workflow_path, dataset_config['workflow']['class'])
        workflow = workflow_class(
            name=dataset_config['name'],
            **dataset_config['source']
        )
        manager.add_workflow(workflow)
    return manager

def initialize_storage(base_path: str = 'data/parquet') -> ParquetStorage:
    return ParquetStorage(base_path)

def initialize_data_binding(db_path: str = 'data/main.db') -> DuckDBBinder:
    return DuckDBBinder(db_path)

def initialize_api(host: str = '0.0.0.0', port: int = 8000, db_path: str = 'data/main.db') -> QueryAPI:
    return QueryAPI(host=host, port=port, db_path=db_path)

def main():
    # Initialize components
    workflow_manager = initialize_workflows('datasets')
    storage = initialize_storage()
    data_binder = initialize_data_binding()

    # Run all workflows
    results = workflow_manager.run_all_workflows()

    # Store results
    for name, data in results.items():
        storage.save(name, data)

    # Bind data
    data_binder.bind_all(storage.directory)

    # Initialize and start API
    api = initialize_api()
    api.start()

    # Display workflow metadata
    print("\nWorkflow Metadata:")
    for metadata in workflow_manager.get_workflow_metadata():
        print(metadata)

if __name__ == "__main__":
    main()