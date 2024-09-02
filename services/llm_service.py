import os
import anthropic
from typing import List, Dict
import re
import json
from utils.config_loader import load_config
import logging
from services.search_service import SearchService
from api.services import QueryService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, search_service: SearchService, query_service: QueryService):
        self.search_service = search_service
        self.query_service = query_service
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.debug("LLMService initialized")

    def generate_response(self, message: str, chat_history: List[Dict], system_prompt: str, is_command_result: bool = False) -> str:
        logger.debug(f"Generating response for message: {message}")
        logger.debug(f"Chat history: {json.dumps(chat_history, indent=2)}")
        logger.debug(f"System prompt: {system_prompt}")
        logger.debug(f"Is command result: {is_command_result}")
        
        try:
            payload = {
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": self._build_messages(message, chat_history),
                "stop_sequences": ["/>"]  # Stop generating after encountering a command
            }

            logger.debug(f"Payload for LLM request: {json.dumps(payload, indent=2)}")

            response = self._make_llm_request(payload)
            logger.debug(f"LLM response: {response}")

            return response
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            raise

    def _build_messages(self, message: str, chat_history: List[Dict]) -> List[Dict]:
        logger.debug("Building messages")
        messages = []
        last_role = None
        for entry in chat_history:
            role = "user" if entry.get("role") == "user" else "assistant"
            content = entry.get('content', '')
            if role != last_role:  # Only add the message if it's a different role from the last one
                messages.append({"role": role, "content": content})
                logger.debug(f"Added message: role={role}, content={content}")
                last_role = role
            else:
                logger.debug(f"Skipped duplicate role message: role={role}, content={content}")
        
        # Always add the new user message at the end
        if last_role != "user":
            messages.append({"role": "user", "content": message})
            logger.debug(f"Added user message: {message}")
        else:
            logger.debug(f"Appended to last user message: {message}")
            messages[-1]["content"] += f"\n{message}"
        
        logger.debug(f"Built messages: {json.dumps(messages, indent=2)}")
        return messages

    def _make_llm_request(self, payload: dict) -> str:
        logger.debug("Making LLM request")
        try:
            response = self.client.messages.create(**payload)
            logger.debug(f"Raw LLM response: {response}")

            content = response.content[0].text
            
            # Check if the response was stopped due to a stop sequence
            if response.stop_reason == 'stop_sequence':
                # Add back the stop sequence ("/>" in this case)
                content += "/>"
            
            logger.debug(f"Extracted content from LLM response: {content}")
            return content
        except Exception as e:
            logger.error(f"Error making LLM request: {str(e)}", exc_info=True)
            raise

    def _format_chat_history(self, chat_history: List[Dict]) -> List[Dict]:
        logger.debug("Formatting chat history")
        formatted_history = []
        for message in chat_history:
            role = "user" if message.get("role") == "user" else "assistant"
            content = message.get("content", "")
            formatted_history.append({"role": role, "content": content})
            logger.debug(f"Formatted message: role={role}, content={content}")
        logger.debug(f"Formatted chat history: {json.dumps(formatted_history, indent=2)}")
        return formatted_history

    def _extract_query_dataset(self, response: str) -> Dict:
        # Extract dataset query information from the response
        pass