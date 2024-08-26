# datasets/worldbank/gdp/workflow.py

from workflows.base_workflow import BaseWorkflow
import requests
import pandas as pd

class WorldBankGDPWorkflow(BaseWorkflow):
    def __init__(self, name, base_url, endpoint):
        super().__init__(name)
        self.base_url = base_url
        self.endpoint = endpoint

    def fetch_data(self):
        url = f"{self.base_url}{self.endpoint}"
        response = requests.get(url, params={'format': 'json', 'per_page': 1000})
        return response.json()[1]  # World Bank API returns metadata in [0] and data in [1]

    def process_data(self, raw_data):
        data = []
        for entry in raw_data:
            if entry['value'] is not None:
                data.append({
                    'country': entry['country']['value'],
                    'country_code': entry['country']['id'],
                    'year': int(entry['date']),
                    'gdp': float(entry['value'])
                })
        return pd.DataFrame(data)

    def run(self):
        self.log_start()
        raw_data = self.fetch_data()
        processed_data = self.process_data(raw_data)
        self.log_end()
        return processed_data