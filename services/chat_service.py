import logging
import json
from typing import List, Dict
from services.llm_service import LLMService
from services.dataset_search_service import DatasetSearchService
from services.datacard_search_service import DatacardSearchService
from api.services import QueryService
from utils.connection_manager import get_connection_manager
from api.query import QueryModel

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        logger.debug("Initializing ChatService")
        dataset_search_service = DatasetSearchService()
        datacard_search_service = DatacardSearchService()
        self.llm_service = LLMService(dataset_search_service, datacard_search_service)
        self.system_prompt = """
        You are an AI assistant for a data analysis platform. Your role is to help users understand and query datasets.
        When a user asks about data or statistics, always provide information about relevant datasets, including their measures and dimensions.
        Be proactive in suggesting ways to analyze or visualize the data based on the available measures and dimensions.
        If a user's query is vague, ask for clarification and suggest potential analyses they might be interested in.
        """
        self.query_service = QueryService()

    def process_message(self, message: str, chat_history: List[Dict]) -> str:
        logger.debug(f"Processing message: {message}")
        try:
            llm_output = self.llm_service.generate_response(message, chat_history, self.system_prompt)
            response = llm_output["response"]
            
            # Extract JSON query from the response
            json_query = self._extract_json_query(response)
            
            if json_query:
                logger.debug(f"Extracted JSON query: {json_query}")
                # Execute the extracted query
                query_result = self.query_service.execute_query_on_dataset(
                    json_query,
                    json_query.get("organization", "default"),
                    json_query.get("dataset", "us_labor_unemployment_rate")
                )
                
                # Send the query result back to the LLM for analysis
                analysis_prompt = f"""
                The following query was executed:
                {json.dumps(json_query, indent=2)}

                The query returned the following result:
                {json.dumps(query_result, indent=2)}

                Please analyze these results and provide insights to the user. If there was an error, explain it and suggest how to modify the query.
                """
                
                analysis_output = self.llm_service.generate_response(analysis_prompt, [], self.system_prompt)
                response += f"\n\nQuery Analysis:\n{analysis_output['response']}"

            logger.debug(f"Generated response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            raise

    def _extract_json_query(self, response: str) -> Dict:
        try:
            start = response.index("```data-query-json")
            end = response.index("```", start + 18)  # 18 is the length of "```data-query-json"
            json_str = response[start + 18:end].strip()
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            logger.error("Failed to extract or parse JSON query from response")
            return None

    # We can remove the _dict_to_query_model method as it's no longer needed