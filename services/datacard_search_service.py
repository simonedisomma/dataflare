import os
import yaml
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class DatacardSearchService:
    def __init__(self):
        self.datacards_dir = 'datacards'

    def search_datacards(self, query: str) -> List[Dict]:
        results = []
        for org in os.listdir(self.datacards_dir):
            org_path = os.path.join(self.datacards_dir, org)
            if os.path.isdir(org_path):
                for datacard_file in os.listdir(org_path):
                    if datacard_file.endswith('.yml'):
                        datacard_path = os.path.join(org_path, datacard_file)
                        with open(datacard_path, 'r') as f:
                            datacard_info = yaml.safe_load(f)
                            datacard_info['organization'] = org
                            datacard_info['datacard_slug'] = os.path.splitext(datacard_file)[0]
                            if query.lower() in datacard_info.get('title', '').lower() or query.lower() in datacard_info.get('description', '').lower():
                                results.append(datacard_info)
        return results

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def _match_datacard(self, datacard: Dict, query_tokens: List[str]) -> bool:
        datacard_text = ' '.join([
            datacard.get('title', ''),
            datacard.get('subtitle', ''),
            ' '.join(str(v) for v in datacard.get('query', {}).values()),
            datacard.get('xAxis', ''),
            datacard.get('yAxis', ''),
            datacard.get('chart_type', ''),
            ' '.join(source.get('name', '') for source in datacard.get('sources', []))
        ]).lower()
        datacard_tokens = self._tokenize(datacard_text)
        
        # Check for exact matches first
        if any(token in datacard_tokens for token in query_tokens):
            return True
        
        # Check for partial matches
        return any(any(query_token in datacard_token for datacard_token in datacard_tokens) for query_token in query_tokens)