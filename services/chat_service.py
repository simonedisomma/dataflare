import logging
import json
from typing import List, Dict
from services.llm_service import LLMService
from services.dataset_search_service import DatasetSearchService
from services.datacard_search_service import DatacardSearchService
from api.services import QueryService
from api.query import QueryModel
from services.search_service import SearchService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        logger.debug("Initializing ChatService")
        self.dataset_search_service = DatasetSearchService()
        self.datacard_search_service = DatacardSearchService()
        self.llm_service = LLMService(self.dataset_search_service, self.datacard_search_service)
        self.system_prompt = """
        You are an AI assistant for a data analysis platform. Your role is to help users understand and query datasets.
        When a user asks about data or statistics, always provide information about relevant datasets, including their measures and dimensions.
        Be proactive in suggesting ways to analyze or visualize the data based on the available measures and dimensions.
        If a user's query is vague, ask for clarification and suggest potential analyses they might be interested in.
        """
        self.query_service = QueryService()
        self.search_service = SearchService()

    def process_message(self, message: str, chat_history: List[Dict]) -> Dict:
        logger.debug(f"Processing message: {message}")
        try:
            # Retrieve relevant information
            retrieved_info = self._retrieve_relevant_info(message)

            # Get response from LLM
            llm_response = self.llm_service.generate_response(message, chat_history, self.system_prompt, retrieved_info)

            # Extract the AI response and suggested query
            ai_response = llm_response.get('response', '')
            suggested_query = llm_response.get('suggested_query', {})

            # Execute the suggested query if available
            query_results = None
            if suggested_query:
                query_results = self._execute_query(suggested_query)

            # Generate final response
            final_response = self._generate_final_response(ai_response, suggested_query, query_results)

            return {
                "message": final_response,
                "retrieved_information": json.dumps(retrieved_info),
                "suggested_query": json.dumps(suggested_query)
            }
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            raise

    def _retrieve_relevant_info(self, message: str) -> Dict:
        datasets = self.dataset_search_service.search_datasets(message)
        datacards = self.datacard_search_service.search_datacards(message)
        return {
            "datasets": [self._format_dataset(d) for d in datasets],
            "datacards": [self._format_datacard(d) for d in datacards]
        }

    def _format_dataset(self, dataset):
        return {
            "name": dataset.get('name', 'Unnamed dataset'),
            "description": dataset.get('description', "No description available"),
            "measures": dataset.get('measures', []),
            "dimensions": dataset.get('dimensions', []),
            "organization": dataset.get('organization', ''),
            "dataset_slug": dataset.get('dataset_slug', '')
        }

    def _format_datacard(self, datacard):
        return {
            "name": datacard.get('title', 'Unnamed datacard'),
            "description": datacard.get('description', "No description available"),
            "organization": datacard.get('organization', ''),
            "datacard_slug": datacard.get('datacard_slug', '')
        }

    def _execute_query(self, suggested_query: Dict) -> Dict:
        try:
            query_model = QueryModel(**suggested_query)
            dataset_full_name = suggested_query.get('dataset', '')
            organization, dataset = dataset_full_name.split('/', 1) if '/' in dataset_full_name else (None, dataset_full_name)
            
            if not organization:
                raise ValueError("Organization not provided in the dataset name")
            
            result = self.query_service.execute_query_on_dataset(
                query_model,
                organization,
                dataset
            )
            return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _generate_final_response(self, ai_response: str, suggested_query: Dict, query_results: Dict) -> str:
        final_response = ai_response

        if suggested_query:
            final_response += "\n\nBased on your question, I've prepared a query to get more specific data:"
            final_response += f"\n```\n{json.dumps(suggested_query, indent=2)}\n```"

        if query_results:
            if "error" in query_results:
                final_response += f"\n\nUnfortunately, there was an error executing the query: {query_results['error']}"
            else:
                final_response += "\n\nHere are the results of the query:"
                final_response += f"\n```\n{json.dumps(query_results, indent=2)}\n```"
                final_response += "\n\nLet me know if you'd like me to explain these results or if you have any questions about the data."

        return final_response

    def _remove_retrieved_info(self, response: str) -> str:
        # Remove the "Retrieved Information" section from the response
        retrieved_info_index = response.find("Retrieved Information:")
        ai_response_index = response.find("AI Response:")
        
        if retrieved_info_index != -1 and ai_response_index != -1:
            return response[ai_response_index + len("AI Response:"):].strip()
        else:
            return response

    # We can remove the _dict_to_query_model method as it's no longer needed