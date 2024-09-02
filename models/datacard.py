from typing import List, Dict, Any

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
            fields=data["fields"]
        )