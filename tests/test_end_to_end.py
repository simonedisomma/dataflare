import unittest
import pandas as pd
import requests
import os
import shutil
import threading
import time
from main import initialize_workflows, initialize_storage, initialize_data_binding, initialize_api
from data_binding.query_engine import QueryEngine

class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs('test_data/parquet', exist_ok=True)
        os.chmod('test_data/parquet', 0o755)
        
        # Create a test Parquet file
        test_df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
        test_df.to_parquet('test_data/parquet/test_workflow.parquet')

        # Initialize components
        cls.workflow_manager = initialize_workflows('test_datasets')
        cls.storage = initialize_storage('test_data/parquet')
        cls.data_binder = initialize_data_binding('test_data/main.db')
        
        # Bind the test data
        cls.data_binder.bind_all('test_data/parquet')
        
        # Get the query engine from the data binder
        query_engine = cls.data_binder.get_query_engine()
        
        # Initialize the API
        cls.api = initialize_api(query_engine, host='localhost', port=8000)
        
        # Start the API in a separate thread
        cls.api_thread = threading.Thread(target=cls.api.start)
        cls.api_thread.daemon = True
        cls.api_thread.start()
        
        # Wait for the API to start
        max_retries = 5
        for _ in range(max_retries):
            try:
                requests.get('http://localhost:8000')
                break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Failed to start API server")

    @classmethod
    def tearDownClass(cls):
        # Stop API
        requests.get('http://localhost:8000/shutdown')
        cls.api_thread.join(timeout=5)

        # Clean up test data
        cls.data_binder.engine.conn.close()
        os.remove('test_data/main.db')
        shutil.rmtree('test_data/parquet')

    def test_workflow_execution(self):
        # Add a sample workflow for testing
        from workflows.base_workflow import BaseWorkflow
        import pandas as pd

        class SampleWorkflow(BaseWorkflow):
            def fetch_data(self):
                return pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})

            def process_data(self, data):
                return data

            def run(self):
                data = self.fetch_data()
                return self.process_data(data)

        self.workflow_manager.add_workflow(SampleWorkflow(name="sample_workflow"))
        
        results = self.workflow_manager.run_all_workflows()
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0, "No workflows were executed")
        self.assertIn("sample_workflow", results)

    def test_data_storage(self):
        # Assuming we have a test workflow that produces data
        test_data = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
        self.storage.save('test_workflow', test_data)
        
        # Check if file exists
        self.assertTrue(os.path.exists('test_data/parquet/test_workflow.parquet'))

    def test_data_binding(self):
        self.data_binder.bind_all('test_data/parquet')
        
        # Check if data is accessible via DuckDB
        result = self.data_binder.engine.execute_query("SELECT * FROM all_data")
        self.assertGreater(len(result), 0)

    def test_api_query(self):
        # Make a test query to the API
        response = requests.get('http://localhost:8000/query?q=SELECT * FROM all_data LIMIT 5')
        if response.status_code != 200:
            print(f"API Error: {response.json()}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('result', data)
        self.assertGreater(len(data['result']), 0)

if __name__ == '__main__':
    unittest.main()