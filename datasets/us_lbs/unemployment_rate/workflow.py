# datasets/us_labor/unemployment_rate/workflow.py

from workflows.base_workflow import BaseWorkflow
import requests
import pandas as pd

class USLaborUnemploymentRateWorkflow(BaseWorkflow):
    def __init__(self, name, api_url, api_key):
        super().__init__(name)
        self.api_url = api_url
        self.api_key = api_key

    def fetch_data(self):
        headers = {'Content-type': 'application/json'}
        data = {
            "seriesid": ["LNS14000000"],
            "startyear": "2020",
            "endyear": "2023",
            "registrationkey": self.api_key
        }
        response = requests.post(self.api_url, json=data, headers=headers)
        return response.json()['Results']['series'][0]['data']

    def process_data(self, raw_data):
        data = []
        for entry in raw_data:
            data.append({
                'date': f"{entry['year']}-{entry['period'][1:]}",
                'unemployment_rate': float(entry['value'])
            })
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
        return df.sort_values('date')

    def run(self):
        self.log_start()
        raw_data = self.fetch_data()
        processed_data = self.process_data(raw_data)
        self.log_end()
        return processed_data