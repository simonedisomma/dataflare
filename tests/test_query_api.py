import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from data_binding.database_engine import ConnectionManager
from api.query import QueryModel

class MockConnectionManager(ConnectionManager):
    def __init__(self):
        self.data = {
            "company_a": {
                "users": [
                    {"name": "Alice", "email": "alice@example.com", "age": 30},
                    {"name": "Bob", "email": "bob@example.com", "age": 28},
                    {"name": "Charlie", "email": "charlie@example.com", "age": 35}
                ]
            }
        }

    def execute_query_on_dataset(self, organization, dataset, query):
        data = self.data.get(organization, {}).get(dataset, [])
        
        # Filter based on where clause
        if query.where:
            data = [item for item in data if eval(query.where, {}, item)]
        
        # Sort based on order_by
        if query.order_by:
            data = sorted(data, key=lambda x: [x.get(field) for field in query.order_by])
        
        # Apply limit
        if query.limit:
            data = data[:query.limit]
        
        # Select only requested fields
        result = [{field: item[field] for field in query.select} for item in data]
        
        return result

    # Implement other abstract methods
    def add_records(self, organization, dataset, records):
        pass

    def close_connection(self):
        pass

    def drop_dataset(self, organization, dataset):
        pass

    def register_dataset(self, organization, dataset, schema):
        pass

    def get_connection(self):
        return self  # Return self as we don't need a real connection for testing

    def test_query_api(self):
        query = {
            "select": ["name", "email"],
            "where": "age > 25",
            "order_by": ["name"],
            "limit": 2
        }
        
        organization = "company_a"
        dataset = "users"
        
        response = self.client.post(f"/query/{organization}/{dataset}", json=query)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")
        
        self.assertEqual(len(result), 2)
        self.assertTrue(all("name" in item and "email" in item for item in result))

if __name__ == '__main__':
    unittest.main()