import os
import yaml
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class DatasetSearchService:
    def __init__(self):
        self.datasets_dir = 'datasets'

    def search_datasets(self, query: str) -> List[Dict]:
        results = []
        for org in os.listdir(self.datasets_dir):
            org_path = os.path.join(self.datasets_dir, org)
            if os.path.isdir(org_path):
                for dataset_slug in os.listdir(org_path):
                    dataset_path = os.path.join(org_path, dataset_slug)
                    if os.path.isdir(dataset_path):
                        yaml_path = os.path.join(dataset_path, 'dataset.yaml')
                        if os.path.exists(yaml_path):
                            with open(yaml_path, 'r') as f:
                                dataset_info = yaml.safe_load(f)
                                dataset_info['organization'] = org
                                dataset_info['dataset_slug'] = dataset_slug
                                if query.lower() in dataset_info.get('name', '').lower() or query.lower() in dataset_info.get('description', '').lower():
                                    results.append(dataset_info)
        return results