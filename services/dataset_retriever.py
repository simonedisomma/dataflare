import logging
import os
import yaml

logger = logging.getLogger(__name__)

class DatasetSearchService:
    def __init__(self):
        self.datasets = self._load_datasets()
        logger.debug(f"Loaded {len(self.datasets)} datasets")
        for dataset in self.datasets:
            logger.debug(f"Loaded dataset: {dataset.get('name', 'Unknown')} from {dataset.get('organization', 'Unknown')}")

    def _load_datasets(self) -> list:
        datasets = []
        datasets_dir = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        logger.debug(f"Attempting to load datasets from: {datasets_dir}")
        
        try:
            for org in os.listdir(datasets_dir):
                org_path = os.path.join(datasets_dir, org)
                if os.path.isdir(org_path):
                    for dataset_id in os.listdir(org_path):
                        dataset_path = os.path.join(org_path, dataset_id)
                        yaml_path = os.path.join(dataset_path, 'dataset.yaml')
                        if os.path.isfile(yaml_path):
                            try:
                                with open(yaml_path, 'r') as f:
                                    dataset = yaml.safe_load(f)
                                    dataset['organization'] = org
                                    dataset['dataset_id'] = dataset_id
                                    datasets.append(dataset)
                            except yaml.YAMLError as e:
                                logger.error(f"Error parsing YAML file {yaml_path}: {str(e)}")
                        else:
                            logger.warning(f"dataset.yaml not found in {dataset_path}")
            
            logger.info(f"Successfully loaded {len(datasets)} datasets")
            return datasets
        except Exception as e:
            logger.error(f"Unexpected error loading datasets: {str(e)}")
            return []

    def search_datasets(self, query: str) -> list:
        logger.debug(f"Searching datasets with query: {query}")
        query_terms = query.lower().split()
        matched_datasets = []

        for dataset in self.datasets:
            dataset_name = dataset.get("name", "").lower()
            dataset_description = dataset.get("description", "").lower()
            dataset_organization = dataset.get("organization", "").lower()
            dataset_fields = [field.lower() for field in dataset.get("fields", [])]

            dataset_text = f"{dataset_name} {dataset_description} {dataset_organization} {' '.join(dataset_fields)}"
            
            match_score = sum(term in dataset_text for term in query_terms)
            
            if match_score > 0:
                matched_datasets.append((match_score, dataset))
                logger.debug(f"Matched dataset: {dataset.get('name', 'Unknown')} (score: {match_score})")
                logger.debug(f"Dataset details: name='{dataset_name}', org='{dataset_organization}', desc='{dataset_description}'")

        matched_datasets.sort(key=lambda x: x[0], reverse=True)
        result = [dataset for score, dataset in matched_datasets]

        logger.debug(f"Found {len(result)} matching datasets")
        return result