# main.py

import yaml
import os
from tqdm import tqdm
from importlib.util import spec_from_file_location, module_from_spec
from workflow_manager.manager import WorkflowManager
from data_binding.database_engine import ConnectionManager
from app import start_server, stop_server
from utils.config_loader import load_config


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


def main():
    config = load_config()

    # Initialize components
    workflow_manager = initialize_workflows('datasets')

    # Get total number of workflows
    total_workflows = len(workflow_manager.workflows)

    # Run all workflows with progress bar
    results = {}
    with tqdm(total=total_workflows, desc="Running workflows") as pbar:
        for name, workflow in workflow_manager.workflows.items():
            results[name] = workflow.run()
            pbar.update(1)


    # Display workflow metadata
    print("\nWorkflow Metadata:")
    for metadata in workflow_manager.get_workflow_metadata():
        print(metadata)

if __name__ == "__main__":
    main()