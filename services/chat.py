import logging
from typing import List, Dict, Optional
from services.llm import LLMService
from services.dataset_retriever import DatasetSearchService
from services.datacard_retriever import DatacardSearchService
from services.query import QueryService
from models.query import QueryModel
from services.search import SearchService
from models.retrieved_info import RetrievedInfo, DatasetInfo, DatacardInfo
from models.chat import ChatResult, ChatMessage, ChatHistory, ChatSession, SuggestedQuery, CodeExecutionResult

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        logger.debug("Initializing ChatService")
        self.dataset_search_service = DatasetSearchService()
        self.datacard_search_service = DatacardSearchService()
        self.llm_service = LLMService(self.dataset_search_service, self.datacard_search_service)
        self.system_prompt = """
        You are an AI assistant for a data analysis platform. Your role is to help users understand and query datasets.
        When a user asks about data or statistics, always provide information about relevant datasets, including their fields.
        Be proactive in suggesting ways to analyze or visualize the data based on the available fields.
        If a user's query is vague, ask for clarification and suggest potential analyses they might be interested in.
        
        IMPORTANT: Always focus on the user's most recent query and provide relevant information or suggestions based on the available datasets.
        If the user mentions a specific topic like "US unemployment", prioritize queries and analyses related to that topic.
        """
        self.query_service = QueryService()
        self.search_service = SearchService()

    def process_message(self, message: str, chat_session: ChatSession) -> ChatResult:
        logger.debug(f"Processing message: {message}")
        try:
            chat_session.add_message("user", message)

            # Retrieve relevant information
            retrieved_info = self._retrieve_relevant_info(message)
            logger.debug(f"Retrieved information: {retrieved_info}")

            # Get response from LLM
            llm_response = self.llm_service.generate_response(message, chat_session.history.messages, self.system_prompt, retrieved_info)

            # Generate final response
            final_response = self._generate_final_response(llm_response)

            suggested_query = SuggestedQuery(**llm_response.get('suggested_query', {})) if llm_response.get('suggested_query') else None
            code_execution_result = CodeExecutionResult(**llm_response.get('code_execution_result', {})) if llm_response.get('code_execution_result') else None

            response = ChatResult(
                message=final_response,
                retrieved_information=retrieved_info,
                suggested_query=suggested_query,
                code_execution_result=code_execution_result
            )

            chat_session.set_current_result(response)
            chat_session.add_message("assistant", final_response)

            logger.debug(f"Final response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            raise

    def _generate_final_response(self, llm_response: Dict) -> str:
        response_parts = [
            self._get_main_message(llm_response),
            self._get_suggested_code(llm_response),
            self._get_code_execution_result(llm_response),
            self._get_assessment(llm_response)
        ]
        return "\n\n".join(filter(None, response_parts))

    def _get_main_message(self, llm_response: Dict) -> str:
        return llm_response.get('message', '')

    def _get_suggested_code(self, llm_response: Dict) -> Optional[str]:
        if suggested_code := llm_response.get('suggested_code'):
            return f"Here's the Python code I've prepared for your analysis:\n```python\n{suggested_code}\n```"
        return None

    def _get_code_execution_result(self, llm_response: Dict) -> Optional[str]:
        if code_execution_result := llm_response.get('code_execution_result'):
            result_parts = [
                "Here are the results of the code execution:",
                self._format_execution_output(code_execution_result),
                self._format_plot_info(code_execution_result),
                self._format_dataframe_info(code_execution_result)
            ]
            return "\n".join(filter(None, result_parts))
        return None

    def _format_execution_output(self, code_execution_result: Dict) -> str:
        if "error" in code_execution_result:
            return f"Error: {code_execution_result['error']}"
        return f"```\n{code_execution_result.get('output', 'No output')}\n```"

    def _format_plot_info(self, code_execution_result: Dict) -> Optional[str]:
        if code_execution_result.get('plot'):
            return "A plot has been generated. You can view it in the chat interface."
        return None

    def _format_dataframe_info(self, code_execution_result: Dict) -> Optional[str]:
        if code_execution_result.get('dataframes'):
            return "DataFrames have been generated. You can view them in the chat interface."
        return None

    def _get_assessment(self, llm_response: Dict) -> Optional[str]:
        if assessment := llm_response.get('assessment'):
            return f"Assessment:\n{assessment}"
        return None

    def _retrieve_relevant_info(self, message: str) -> RetrievedInfo:
        datasets = self.dataset_search_service.search_datasets(message)
        datacards = self.datacard_search_service.search_datacards(message)
        return RetrievedInfo(
            datasets=[self._format_dataset(d) for d in datasets],
            datacards=[self._format_datacard(d) for d in datacards]
        )

    def _format_dataset(self, dataset) -> DatasetInfo:
        return DatasetInfo(
            name=dataset.get('name', 'Unnamed dataset'),
            description=dataset.get('description', "No description available"),
            fields=dataset.get('fields', []),
            organization=dataset.get('organization', ''),
            dataset_slug=dataset.get('dataset_slug', '')
        )

    def _format_datacard(self, datacard) -> DatacardInfo:
        return DatacardInfo(
            name=datacard.get('title', 'Unnamed datacard'),
            description=datacard.get('description', "No description available"),
            organization=datacard.get('organization', ''),
            datacard_slug=datacard.get('datacard_slug', '')
        )

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

    def _remove_retrieved_info(self, response: str) -> str:
        # Remove the "Retrieved Information" section from the response
        retrieved_info_index = response.find("Retrieved Information:")
        ai_response_index = response.find("AI Response:")
        
        if retrieved_info_index != -1 and ai_response_index != -1:
            return response[ai_response_index + len("AI Response:"):].strip()
        else:
            return response
