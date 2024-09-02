from typing import List, Dict, Any

class Column:
    def __init__(self, name: str, data_type: str, description: str = None):
        self.name = name
        self.data_type = data_type
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Column':
        return cls(
            name=data["name"],
            data_type=data["data_type"],
            description=data.get("description")
        )

class Dataset:
    def __init__(self, name: str, description: str, columns: List[Column] = None):
        self.name = name
        self.description = description
        self.columns = columns or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "schema": {
                "columns": [column.to_dict() for column in self.columns]
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dataset':
        columns = [Column.from_dict(col) for col in data.get("schema", {}).get("columns", [])]
        return cls(
            name=data["name"],
            description=data["description"],
            columns=columns
        )

    def add_column(self, name: str, data_type: str, description: str = None):
        self.columns.append(Column(name, data_type, description))