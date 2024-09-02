import pytest
from fastapi.testclient import TestClient
from app import app, get_connection_manager
from data_binding.database_engine import ConnectionManager
import yaml
from api.services import QueryService, DatacardService
import json

class MockConnectionManager(ConnectionManager):
    def __init__(self):
        self.data = {
            "us_lbs": {
                "unemployment_rate": [
                    {"date": "2023-01-01", "unemployment_rate": 3.5},
                    {"date": "2023-02-01", "unemployment_rate": 3.6},
                    {"date": "2023-03-01", "unemployment_rate": 3.4}
                ]
            }
        }

    def execute_query_on_dataset(self, organization, dataset, query):
        return self.data.get(organization, {}).get(dataset, [])

    def add_records(self, organization, dataset, records):
        pass  # Mock implementation

    def close_connection(self):
        pass  # Mock implementation

    def drop_dataset(self, organization, dataset):
        pass  # Mock implementation

    def get_connection(self):
        return self  # Mock implementation

    def register_dataset(self, organization, dataset, schema):
        pass  # Mock implementation

@pytest.fixture
def client():
    app.dependency_overrides[get_connection_manager] = lambda: MockConnectionManager()
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_render_flow(client):
    # Test rendering the HTML
    response = client.get("/render/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test fetching the datacard HTML
    response = client.get("/datacard/us_lbs/unemployment_rate")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test fetching the datacard metadata
    response = client.get("/api/datacard/us_lbs/unemployment_rate")
    assert response.status_code == 200
    metadata = response.json()
    assert "title" in metadata
    assert "subtitle" in metadata
    assert "query" in metadata

    # Test querying the dataset
    query_data = metadata["query"]
    response = client.post(f"/query/us_lbs/unemployment_rate", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "date" in data[0]
    assert "unemployment_rate" in data[0]