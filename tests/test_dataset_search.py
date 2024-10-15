import unittest
import sys
import os
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.search import SearchService

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDatasetSearch(unittest.TestCase):
    def setUp(self):
        self.search_service = SearchService()
        logger.debug("SearchService initialized")

    def test_search_us_lbs_unemployment(self):
        query = "us lbs unemployment"
        logger.debug(f"Searching for query: {query}")
        results = self.search_service.search_datasets(query)
        
        logger.debug(f"Number of results found: {len(results)}")
        self.assertGreater(len(results), 0, "No results found")
        
        found_unemployment_dataset = False
        for dataset in results:
            dataset_info = dataset.get("dataset", {})
            dataset_name = dataset_info.get("name", "").lower()
            logger.debug(f"Checking dataset: {dataset_name}")
            if "unemployment_rate" in dataset_name:
                found_unemployment_dataset = True
                logger.debug(f"Found matching dataset: {dataset_name}")
                break
        
        self.assertTrue(found_unemployment_dataset, "US LBS unemployment dataset not found in search results")
        logger.debug("Test completed")

if __name__ == '__main__':
    unittest.main()
