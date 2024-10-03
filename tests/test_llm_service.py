import unittest
from typing import List, Dict
from services.llm_service import LLMService
from services.dataset_search_service import DatasetSearchService
from services.datacard_search_service import DatacardSearchService

class TestLLMService(unittest.TestCase):
    def setUp(self):
        self.dataset_search_service = DatasetSearchService()
        self.datacard_search_service = DatacardSearchService()
        self.llm_service = LLMService(self.dataset_search_service, self.datacard_search_service)

    def test_retrieve_relevant_info_for_unemployment(self):
        message = "lbs unemployment"
        chat_history = []
        
        result = self.llm_service.retrieve_relevant_info(message, chat_history)
        
        # Check if datasets were retrieved
        self.assertIsInstance(result["datasets"], list)
        self.assertTrue(len(result["datasets"]) > 0, "No datasets were retrieved")
        
        # Check if the US LBS unemployment dataset was retrieved
        us_lbs_datasets = [d for d in result["datasets"] if "us_labor_unemployment_rate" in d["name"].lower()]
        self.assertTrue(len(us_lbs_datasets) > 0, "US LBS unemployment dataset was not retrieved")
        
        # Check if datacards were retrieved
        self.assertIsInstance(result["datacards"], list)
        self.assertTrue(len(result["datacards"]) > 0, "No datacards were retrieved")
        
        # Check if the US LBS unemployment datacard was retrieved
        us_lbs_datacards = [d for d in result["datacards"] if "us monthly unemployment rate" in d["title"].lower()]
        self.assertTrue(len(us_lbs_datacards) > 0, "US LBS unemployment datacard was not retrieved")

    def test_retrieve_relevant_info_no_match(self):
        message = "irrelevant query that should not match anything"
        chat_history = []
        
        result = self.llm_service.retrieve_relevant_info(message, chat_history)
        
        self.assertEqual(len(result["datasets"]), 0, "Datasets were retrieved for an irrelevant query")
        self.assertEqual(len(result["datacards"]), 0, "Datacards were retrieved for an irrelevant query")

if __name__ == '__main__':
    unittest.main()