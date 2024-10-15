import pytest
import pandas as pd
from services.dataframe import DataFrameService, load_dataset, query_dataset
from services.query import QueryService

@pytest.fixture(scope="module")
def setup_dataframe_service():
    
    query_service = QueryService()
    dataframe_service = DataFrameService()
    dataframe_service.query_service = query_service

    class AppContext:
        def __init__(self):
            self.dataframe_service = dataframe_service
    
    pd.app_context = AppContext()
    pd.load_dataset = load_dataset
    pd.query = query_dataset
    
    yield dataframe_service
    
    del pd.app_context
    del pd.load_dataset
    del pd.query

def test_query_unemployment_rate(setup_dataframe_service):
    # Execute query on real dataset
    df = pd.query('us_lbs/unemployment_rate', 
                  select=['date', 'unemployment_rate'],
                  order=['date'],
                  limit=10)  # Limit to 10 rows for test efficiency

    # Parse the 'date' column to datetime
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%dT%H:%M:%S')

    # Assertions
    assert not df.empty, "DataFrame should not be empty"
    assert len(df) <= 10, "DataFrame should have at most 10 rows due to limit"
    assert list(df.columns) == ['date', 'unemployment_rate'], "DataFrame should have 'date' and 'unemployment_rate' columns"
    
    # Check data types
    assert pd.api.types.is_datetime64_any_dtype(df['date']), "'date' column should be datetime type"
    assert pd.api.types.is_float_dtype(df['unemployment_rate']), "'unemployment_rate' column should be float type"
    
    # Check if data is sorted by date
    assert df['date'].is_monotonic_increasing, "Data should be sorted by date in ascending order"
    
    # Check for reasonable unemployment rate values
    assert df['unemployment_rate'].between(0, 100).all(), "Unemployment rate should be between 0 and 100"

    print(df.head())  # Print first few rows for manual inspection

if __name__ == "__main__":
    pytest.main([__file__])