from typing import List, Dict, Any
import yaml
import json
import os

class Datacard:
    def __init__(self, name: str, description: str, fields: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.fields = fields or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "fields": self.fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Datacard':
        return cls(
            name=data["name"],
            description=data["description"],
            fields=data.get("fields", {})
        )
    
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
        yaml_path = os.path.join(dataset_location, "dataset.yaml")
        try:
            with open(yaml_path, 'r') as file:
                yaml_content = yaml.safe_load(file)
                return yaml_content  # YAML is already JSON-compatible
        except FileNotFoundError:
            raise FileNotFoundError(f"dataset.yaml not found at {yaml_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing dataset.yaml: {str(e)}")
