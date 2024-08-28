import pytest
import duckdb
import json
from api.query_api import QueryAPI
from data_binding.duckdb_engine import DuckDBEngine

@pytest.fixture
def sample_data():
    return [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"},
    ]

@pytest.fixture
def query_api(sample_data):
    # Use DuckDBEngine utils to create test data
    query_engine = DuckDBEngine(':memory:')
    query_engine.create_table("users", ["id INTEGER", "name VARCHAR", "age INTEGER", "email VARCHAR"])
    query_engine.insert_data("users", sample_data)

    return QueryAPI(query_engine)

def test_query_builder(query_api):
    result = query_api.execute(
        query_api.query()
            .from_table("users")
            .select("name", "email")
            .where("age > 25")
            .order_by("name")
            .limit(2)
    )

    print(f"Query builder result: {result}")  # For debugging
    assert len(result) == 2
    assert all("name" in item and "email" in item for item in result)
    print(f"Actual result: {json.dumps(result, indent=2)}")  # Print the actual result

def test_query_chaining(query_api):
    query = (query_api.query()
        .from_table("users")
        .select("name")
        .where("age > 30")
        .select("email")  # We can chain multiple selects
    )
    
    result = query_api.execute(query)

    print(f"Query chaining result: {result}")  # For debugging
    assert len(result) == 1  # Only Charlie should be over 30
    assert "name" in result[0] and "email" in result[0]
    assert result[0]["name"] == "Charlie"
    print(f"Actual result: {json.dumps(result, indent=2)}")  # Print the actual result

def test_empty_query(query_api):
    result = query_api.execute(query_api.query().from_table("users"))
    print(f"Empty query result: {result}")  # For debugging
    assert len(result) == 3  # Should return all data when no fields are specified
    print(f"Actual result: {json.dumps(result, indent=2)}")  # Print the actual result

def test_simple_query(query_api):
    result = query_api.execute(
        query_api.query()
            .from_table("users")
            .select("name", "email")
    )

    print(f"Simple query result: {result}")  # For debugging
    assert len(result) == 3
    assert all("name" in item and "email" in item for item in result)
    assert result[0]["name"] == "Alice"
    assert result[0]["email"] == "alice@example.com"
    print(f"Actual result: {json.dumps(result, indent=2)}")  # Print the actual result