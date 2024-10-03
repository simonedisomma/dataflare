import unittest
import logging
from api.services import QueryService
from api.query import QueryModel
from utils.config_loader import load_dataset_definition, load_config
import json

logger = logging.getLogger(__name__)

class TestQueryService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_config = load_dataset_definition('us_lbs', 'unemployment_rate')
        cls.config = load_config()
        logger.info(f"Loaded dataset config: {json.dumps(cls.dataset_config, indent=2)}")
        logger.info(f"Loaded general config: {json.dumps(cls.config, indent=2)}")

    def setUp(self):
        self.query_service = QueryService()

    def test_recent_unemployment_rates(self):
        query_dict = {
            "description": "Recent unemployment rates for all US states",
            "select": ["date", "state", "unemployment_rate"],
            "order_by": ["date DESC", "state ASC"],
            "limit": 60,
            "table": self.dataset_config['database']['table'],
            "organization": "us_lbs",
            "dataset": "unemployment_rate"
        }

        logger.info(f"Executing query: {json.dumps(query_dict, indent=2)}")

        result = self.query_service.execute_query_on_dataset(
            query_dict,
            query_dict["organization"],
            query_dict["dataset"]
        )

        logger.info(f"Query result: {json.dumps(result, indent=2, default=str)}")

        self.assertIn('result', result, "Result key not found in query response")
        self.assertNotIn('error', result, f"Query execution failed: {result.get('error', 'Unknown error')}")

        data = result['result']
        self.assertIsInstance(data, list, "Query result should be a list")
        self.assertGreater(len(data), 0, "Query result should not be empty")

        logger.info(f"Total rows returned: {len(data)}")

        # Check that more than 0 records are returned
        self.assertGreater(len(data), 0, "Query should return more than 0 records")
        logger.info(f"Number of records returned: {len(data)}")

        # Check the structure of the first row
        first_row = data[0]
        self.assertIn('date', first_row, "Date field missing in result")
        self.assertIn('state', first_row, "State field missing in result")
        self.assertIn('unemployment_rate', first_row, "Unemployment rate field missing in result")

        # Check data types
        self.assertIsInstance(first_row['date'], str, "Date should be a string")
        self.assertIsInstance(first_row['state'], str, "State should be a string")
        self.assertIsInstance(first_row['unemployment_rate'], (int, float), "Unemployment rate should be a number")

        # Check ordering
        for i in range(1, len(data)):
            self.assertGreaterEqual(data[i-1]['date'], data[i]['date'], "Results should be ordered by date DESC")
            if data[i-1]['date'] == data[i]['date']:
                self.assertLessEqual(data[i-1]['state'], data[i]['state'], "Results with same date should be ordered by state ASC")

        # Check limit
        self.assertLessEqual(len(data), 60, "Result should not exceed the specified limit")

        logger.info("Test passed successfully")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()