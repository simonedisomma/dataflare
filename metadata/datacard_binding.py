import yaml
import json
from typing import Dict, Any

class DatacardBinding:
    @staticmethod
    def get_datacard_definition(dataset_location: str) -> Dict[str, Any]:
        """
        Retrieve the datacard definition from the dataset.yaml file and return it as JSON.

        Args:
            dataset_location (str): The path to the dataset directory containing the dataset.yaml file.

        Returns:
            Dict[str, Any]: The datacard definition as a JSON-compatible dictionary.

        Raises:
            FileNotFoundError: If the dataset.yaml file is not found.
            yaml.YAMLError: If there's an error parsing the YAML file.
        """
        try:
            with open(f"{dataset_location}/dataset.yaml", 'r') as file:
                yaml_content = yaml.safe_load(file)
                return json.loads(json.dumps(yaml_content))  # Ensure JSON compatibility
        except FileNotFoundError:
            raise FileNotFoundError(f"dataset.yaml not found in {dataset_location}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing dataset.yaml: {str(e)}")
