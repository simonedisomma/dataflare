import os
import yaml
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class DatacardSearchService:
    def __init__(self, datacards_folder: str = 'datacards'):
        self.datacards_folder = datacards_folder
        logger.debug(f"DatacardSearchService initialized with folder: {datacards_folder}")

    def search_datacards(self, query: str) -> List[Dict]:
        logger.debug(f"Searching datacards for query: {query}")
        results = []
        query_tokens = self._tokenize(query)

        for root, dirs, files in os.walk(self.datacards_folder):
            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    logger.debug(f"Processing file: {file_path}")
                    with open(file_path, 'r') as f:
                        try:
                            datacard = yaml.safe_load(f)
                            if self._match_datacard(datacard, query_tokens):
                                results.append(datacard)
                                logger.debug(f"Matched datacard: {datacard.get('title', 'Unknown')}")
                        except yaml.YAMLError as e:
                            logger.error(f"Error parsing YAML file {file_path}: {e}")

        logger.debug(f"Found {len(results)} matching datacards")
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