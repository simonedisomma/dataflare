import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datasets.worldbank.main_gdp_and_other_stats_gdp.workflow import WorldBankGDPWorkflow


class TestWorldBankGDPWorkflow(unittest.TestCase):

    def setUp(self):
        self.workflow = WorldBankGDPWorkflow(
            name="test_worldbank_gdp",
            base_url="https://api.worldbank.org/v2/",
            endpoint="country/all/indicator/NY.GDP.MKTP.CD"
        )

    @patch('datasets.worldbank.main_gdp_and_other_stats_gdp.workflow.requests.get')
    def test_fetch_data(self, mock_get):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {},  # Metadata
            [
                {
                    "country": {"id": "USA", "value": "United States"},
                    "date": "2022",
                    "value": "25462700000000"
                },
                {
                    "country": {"id": "CHN", "value": "China"},
                    "date": "2022",
                    "value": "17963170000000"
                }
            ]
        ]
        mock_get.return_value = mock_response

        # Call the method
        result = self.workflow.fetch_data()

        # Assert the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['country']['id'], 'USA')
        self.assertEqual(result[1]['country']['id'], 'CHN')

    def test_process_data(self):
        # Prepare test data
        raw_data = [
            {
                "country": {"id": "USA", "value": "United States"},
                "date": "2022",
                "value": "25462700000000"
            },
            {
                "country": {"id": "CHN", "value": "China"},
                "date": "2022",
                "value": "17963170000000"
            },
            {
                "country": {"id": "JPN", "value": "Japan"},
                "date": "2022",
                "value": None
            }
        ]

        # Call the method
        result = self.workflow.process_data(raw_data)

        # Assert the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # Japan should be excluded due to None value
        self.assertEqual(list(result.columns), ['country', 'country_code', 'year', 'gdp'])
        self.assertEqual(result.iloc[0]['country'], 'United States')
        self.assertEqual(result.iloc[0]['country_code'], 'USA')
        self.assertEqual(result.iloc[0]['year'], 2022)
        self.assertEqual(result.iloc[0]['gdp'], 25462700000000.0)

    @patch('datasets.worldbank.main_gdp_and_other_stats_gdp.workflow.WorldBankGDPWorkflow.fetch_data')
    @patch('datasets.worldbank.main_gdp_and_other_stats_gdp.workflow.WorldBankGDPWorkflow.process_data')
    def test_run(self, mock_process_data, mock_fetch_data):
        # Mock the fetch_data and process_data methods
        mock_fetch_data.return_value = [{"some": "data"}]
        mock_process_data.return_value = pd.DataFrame({"column": [1, 2, 3]})

        # Call the method
        result = self.workflow.run()

        # Assert the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        mock_fetch_data.assert_called_once()
        mock_process_data.assert_called_once_with([{"some": "data"}])

if __name__ == '__main__':
    unittest.main()