# main.py

import yaml
import os
from importlib.util import spec_from_file_location, module_from_spec
from workflow_manager.manager import WorkflowManager
from data_storage.parquet_storage import ParquetStorage
from data_binding.duckdb_binder import DuckDBBinder
from data_binding.query_engine import QueryEngine
from api.query_api import QueryAPI
from tqdm import tqdm

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
    print(f"Searching for datasets in: {datasets_path}")
    for config_path in discover_datasets(datasets_path):
        print(f"Found config file: {config_path}")
        try:
            dataset_config = load_dataset_config(config_path)
            workflow_path = os.path.join(os.path.dirname(config_path), dataset_config['workflow']['file'])
            print(f"Loading workflow from: {workflow_path}")
            workflow_class = load_workflow_class(workflow_path, dataset_config['workflow']['class'])
            workflow = workflow_class(
                name=dataset_config['name'],
                **dataset_config['source']
            )
            manager.add_workflow(workflow)
            print(f"Added workflow: {workflow.name}")
        except Exception as e:
            print(f"Error loading workflow from {config_path}: {str(e)}")
    return manager

def initialize_storage(base_path: str = 'data/parquet') -> ParquetStorage:
    return ParquetStorage(base_path)

def initialize_data_binding(db_path: str = 'data/main.db') -> DuckDBBinder:
    try:
        return DuckDBBinder(db_path)
    except RuntimeError as e:
        print(f"Error initializing DuckDB: {e}")
        print("Creating a new database file.")
        return DuckDBBinder(':memory:')  # Use in-memory database as fallback

def initialize_api(query_engine: QueryEngine, host: str = '0.0.0.0', port: int = 8000) -> QueryAPI:
    # Initialize API
    api = QueryAPI(query_engine)
    api.set_host_and_port(host, port)
    return api

    # Initialize components
    workflow_manager = initialize_workflows('datasets')
    storage = initialize_storage()
    data_binder = initialize_data_binding()

def main():
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Initialize components
    workflow_manager = initialize_workflows('datasets')
    storage = initialize_storage()
    data_binder = initialize_data_binding()
    query_engine = data_binder.get_query_engine()

    # Get total number of workflows
    total_workflows = len(workflow_manager.workflows)

    # Run all workflows with progress bar
    results = {}
    with tqdm(total=total_workflows, desc="Running workflows") as pbar:
        for name, workflow in workflow_manager.workflows.items():
            results[name] = workflow.run()
            pbar.update(1)

    # Store results with progress bar
    with tqdm(total=len(results), desc="Storing results") as pbar:
        for name, data in results.items():
            storage.save(name, data)
            pbar.update(1)

    # Bind data only if Parquet files exist
    if os.listdir(storage.directory):
        data_binder.bind_all(storage.directory)
        
        # Initialize and start API
        api = initialize_api(query_engine=query_engine)
  
    else:
        print("No data files found. Skipping data binding and API initialization.")

    # Display workflow metadata
    print("\nWorkflow Metadata:")
    for metadata in workflow_manager.get_workflow_metadata():
        print(metadata)

if __name__ == "__main__":
    main()