import logging
from typing import List, Dict
from services.search_service import SearchService
from services.llm_service import LLMService
from api.services import QueryService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, search_service: SearchService, query_service: QueryService):
        self.search_service = search_service
        self.query_service = query_service
        self.llm_service = LLMService(search_service, query_service)
        logger.debug("ChatService initialized")

    def process_message(self, message: str, chat_history: List[Dict], is_command_result: bool = False) -> str:
        logger.debug(f"Processing message: {message}")
        logger.debug(f"Chat history: {chat_history}")
        logger.debug(f"Is command result: {is_command_result}")
        
        try:
            system_prompt = """You are an AI assistant that helps users with dataset and datacard queries. 
            When appropriate, use the following commands to perform actions:
            <$search_dataset query="search query"/>
            <$search_datacard query="search query"/>
            <$query_dataset query="SQL query" from="organization/dataset"/>
            Always use these commands when you need to search for or query data. Do not make up information."""

            response = self.llm_service.generate_response(message, chat_history, system_prompt, is_command_result)
            logger.debug(f"Generated response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"An error occurred while processing your request: {str(e)}"