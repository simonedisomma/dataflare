import unittest
import requests
import os
import shutil
import threading
import time
import pandas as pd
from main import initialize_workflows
from data_binding.database_engine import ConnectionManager
from api.query import QueryModel
from api.services import QueryService, DatacardService
from app import app, start_server, stop_server
from utils.config_loader import load_config, load_dataset_definition
from workflows.base_workflow import BaseWorkflow

class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load config
        cls.config = load_config()

        # Initialize components
        cls.workflow_manager = initialize_workflows('test_datasets')

        # Create connection manager
        connection_config = cls.config.get('connection', {})
        cls.connection_manager = ConnectionManager.create(connection_config)

        # Initialize services
        cls.query_service = QueryService(cls.connection_manager)
        cls.datacard_service = DatacardService(cls.connection_manager)

        # Start the API in a separate thread
        cls.api_thread = threading.Thread(target=start_server, args=(cls.config['api']['host'], cls.config['api']['port']))
        cls.api_thread.daemon = True
        cls.api_thread.start()
        
        # Wait for the API to start
        cls._wait_for_api_start()

        cls.api_base_url = "http://localhost:8000"

    @classmethod
    def tearDownClass(cls):
        # Stop API
        stop_server()
        cls.api_thread.join(timeout=5)

        # Clean up test data
        cls._clean_up_test_data()

    @classmethod
    def _wait_for_api_start(cls):
        max_retries = 5
        for _ in range(max_retries):
            try:
                requests.get(f"http://{cls.config['api']['host']}:{cls.config['api']['port']}")
                break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Failed to start API server")

    @classmethod
    def _clean_up_test_data(cls):
        cls.connection_manager.drop_dataset('organization', 'dataset')
        cls.connection_manager.close_connection()
        if os.path.exists('test_data/main.db'):
            os.remove('test_data/main.db')
        if os.path.exists('test_data/parquet'):
            shutil.rmtree('test_data/parquet')

    def setUp(self):
        # Create test data directory
        os.makedirs('test_data/parquet', exist_ok=True)
        os.chmod('test_data/parquet', 0o755)

    def test_end_to_end(self):
        # 1. Create and store test data
        self._create_and_store_test_data()

        # 2. Register dataset
        self._register_dataset()

        # 3. Create and add workflow
        self._create_and_add_workflow()

        # 4. Run workflow
        self._run_workflow()

        # 5. Query data
        self._query_data()


    def _create_and_store_test_data(self):
        test_df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
        test_df.to_parquet('test_data/parquet/test_workflow.parquet')
        self.assertTrue(os.path.exists('test_data/parquet/test_workflow.parquet'))

    def _register_dataset(self):
        self.connection_manager.register_dataset('test_organization', 'test_dataset', ['id INTEGER', 'name TEXT'])
        test_records = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
            {'id': 3, 'name': 'Charlie'}
        ]
        self.connection_manager.add_records('test_organization','test_dataset', test_records)

    def _create_and_add_workflow(self):
        class SampleWorkflow(BaseWorkflow):
            def fetch_data(self):
                return pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})

            def process_data(self, data):
                return data

            def run(self):
                data = self.fetch_data()
                return self.process_data(data)

        self.workflow_manager.add_workflow(SampleWorkflow(name="sample_workflow"))
        # TODO: Add a method to verify workflow addition

    def _run_workflow(self):
        results = self.workflow_manager.run_all_workflows()
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0, "No workflows were executed")
        self.assertIn("sample_workflow", results)

    def _query_data(self):
        query_model = QueryModel(
            select=['id', 'name'],
            table='test_dataset',
            where='id > 1'
        )
        
        dataset_config = load_dataset_definition('test_organization', 'test_dataset')
        result = self.query_service.execute_query_on_dataset(query_model, 'test_organization', 'test_dataset')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Bob')
        self.assertEqual(result[1]['name'], 'Charlie')

if __name__ == '__main__':
    unittest.main()