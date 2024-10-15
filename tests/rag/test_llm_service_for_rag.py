import json
from services.chat import ChatService

def test_chat_service_retrieves_correct_information():
    chat_service = ChatService()
    query = "us lbs unemployment"
    expected_datasets = [
        {
            "name": "unemployment_rate",
            "description": "Monthly US unemployment rate",
            "fields": ["unemployment_rate"],
            "organization": "us_lbs",
            "dataset_slug": ""
        },
        {
            "name": "users",
            "description": "No description available",
            "fields": [],
            "organization": "company_a",
            "dataset_slug": ""
        }
    ]

    # Process the message using ChatService
    response = chat_service.process_message(query, [])

    # Assert that retrieved_information is present in the response
    assert "retrieved_information" in response

    # Parse the retrieved_information JSON
    retrieved_info = json.loads(response["retrieved_information"])

    # Assert that the datasets key is present in retrieved_information
    assert "datasets" in retrieved_info

    # Assert that at least one of the expected datasets is present in the retrieved information
    assert any(expected_dataset in retrieved_info["datasets"] for expected_dataset in expected_datasets), "Expected datasets not found"

    # Assert that the message field is present and is a string
    assert "message" in response
    assert isinstance(response["message"], str)

    # Assert that suggested_query is present and is a JSON string
    assert "suggested_query" in response
    suggested_query = json.loads(response["suggested_query"])
    assert isinstance(suggested_query, dict)

    # Assert that code_execution_result is present
    assert "code_execution_result" in response

    # Assert that unemployment_rate field is not null
    unemployment_dataset = next((dataset for dataset in retrieved_info["datasets"] if dataset["name"] == "unemployment_rate"), None)
    assert unemployment_dataset is not None
    assert "unemployment_rate" in unemployment_dataset["fields"]
    assert unemployment_dataset["fields"]["unemployment_rate"] is not None
