import pytest
import json
from data_binding.database_engine import ConnectionManager
from api.services import QueryService
from api.query import QueryBuilder

@pytest.fixture
def sample_data():
    return [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"},
    ]

@pytest.fixture
def query_service(sample_data):
    connection_config = {'driver': 'duckdb', 'db_path': ':memory:'}
    connection_manager = ConnectionManager.create(connection_config)
    
    connection_manager.register_dataset("company_a", "users", ["id INTEGER", "name VARCHAR", "age INTEGER", "email VARCHAR"])
    connection_manager.add_records("company_a", "users", sample_data)

    return QueryService(connection_manager)

def test_query_builder(query_service):
    query_builder = (QueryBuilder()
        .from_table("users")
        .select("name", "email")
        .where("age > 25")
        .order_by("name")
        .limit(2)
    )
    result = query_service.execute_query(query_builder.build())

    assert len(result) == 2
    assert all("name" in item and "email" in item for item in result)
    print(f"Query builder result: {json.dumps(result, indent=2)}")

def test_query_chaining(query_service):
    query_builder = (QueryBuilder()
        .from_table("users")
        .select("name")
        .where("age > 30")
        .select("email")
    )
    
    result = query_service.execute_query(query_builder.build())

    assert len(result) == 1  # Only Charlie should be over 30
    assert "name" in result[0] and "email" in result[0]
    assert result[0]["name"] == "Charlie"
    print(f"Query chaining result: {json.dumps(result, indent=2)}")

def test_empty_query(query_service):
    query_builder = QueryBuilder().from_table("users")
    result = query_service.execute_query(query_builder.build())
    assert len(result) == 3  # Should return all data when no fields are specified
    print(f"Empty query result: {json.dumps(result, indent=2)}")

def test_simple_query(query_service):
    query_builder = (QueryBuilder()
        .from_table("users")
        .select("name", "email")
    )
    result = query_service.execute_query(query_builder.build())
    print(f"Simple query result: {json.dumps(result, indent=2)}")

    assert len(result) == 3
    assert all("name" in item and "email" in item for item in result)
    assert result[0]["name"] == "Alice"
    assert result[0]["email"] == "alice@example.com"
