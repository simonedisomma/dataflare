import os
import yaml
from typing import List, Dict
from models.datacard import Datacard
from models.dataset import Dataset, Column
from difflib import SequenceMatcher

class SearchService:
    def __init__(self):
        self.datacards_dir = "datacards"
        self.datasets_dir = "datasets"

    def search_datasets(self, query: str) -> List[Dict]:
        datasets = []
        for root, dirs, files in os.walk(self.datasets_dir):
            for dir_name in dirs:
                similarity = SequenceMatcher(None, query.lower(), dir_name.lower()).ratio()
                if similarity > 0.6:  # You can adjust this threshold
                    dataset_path = os.path.join(root, dir_name)
                    dataset = self._load_dataset(dataset_path, dir_name)
                    datasets.append(dataset)
        return datasets

    def _load_dataset(self, dataset_path: str, dataset_name: str) -> Dict:
        # Load dataset metadata from a YAML file (assuming it exists)
        metadata_path = os.path.join(dataset_path, "metadata.yml")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
        else:
            metadata = {"description": f"Dataset found in {dataset_path}"}

        # Create Dataset object
        dataset = Dataset(name=dataset_name, description=metadata.get("description", ""))

        # Add columns if available in metadata
        if "columns" in metadata:
            for col in metadata["columns"]:
                dataset.add_column(col["name"], col["data_type"], col.get("description"))

        # Construct query specifications
        query_specs = {
            "select": [col.name for col in dataset.columns],
            "where": "Specify conditions using column names and operators (e.g., column_name > value)",
            "order_by": "Specify columns to sort by (e.g., ['column_name ASC', 'another_column DESC'])",
            "limit": "Specify the maximum number of rows to return"
        }

        return {
            "dataset": dataset.to_dict(),
            "query_specs": query_specs
        }

    def search_datacards(self, query: str) -> List[Datacard]:
        datacards = []
        for root, dirs, files in os.walk(self.datacards_dir):
            for file in files:
                if file.endswith('.yml'):
                    similarity = SequenceMatcher(None, query.lower(), file.lower()).ratio()
                    if similarity > 0.6:  # You can adjust this threshold
                        datacard_path = os.path.join(root, file)
                        with open(datacard_path, 'r') as f:
                            datacard_data = yaml.safe_load(f)
                        datacard = Datacard(
                            name=file[:-4],  # Remove .yml extension
                            description=datacard_data.get('subtitle', 'No description available'),
                            fields=datacard_data
                        )
                        datacards.append(datacard)
        return datacards