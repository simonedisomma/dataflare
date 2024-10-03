import os
import anthropic
from typing import List, Dict
import json
import logging
from services.dataset_search_service import DatasetSearchService
from services.datacard_search_service import DatacardSearchService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, dataset_search_service: DatasetSearchService, datacard_search_service: DatacardSearchService):
        self.dataset_search_service = dataset_search_service
        self.datacard_search_service = datacard_search_service
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.debug("LLMService initialized")
        self.query_format_instructions = """
        When suggesting a query, please format it as a JSON object wrapped in a ```data-query-json``` command, like this:

        ```data-query-json
        {
            "description": "A brief description of the query",
            "select": ["list", "of", "fields", "to", "select"],
            "where": "condition for filtering data",
            "order_by": ["list", "of", "fields", "to", "order", "by"],
            "limit": number_of_results_to_return,
            "table": "name_of_the_table",
            "organization": "organization_name",
            "dataset": "dataset_name"
        }
        ```

        Always use this exact format when suggesting a query.
        """

    def generate_response(self, message: str, chat_history: List[Dict], system_prompt: str) -> Dict:
        logger.debug(f"Generating response for message: {message}")
        
        try:
            # Perform RAG to get relevant information
            relevant_info = self.retrieve_relevant_info(message, chat_history)
            
            # Format the relevant information
            formatted_info = self._format_relevant_info(relevant_info)
            
            # Augment the system prompt with the retrieved information and query format instructions
            augmented_prompt = f"""
            {system_prompt}

            Relevant information:
            {formatted_info}

            {self.query_format_instructions}

            Based on the user's input, suggest a specific query to execute on the relevant dataset. 
            Format the query suggestion as JSON wrapped in the ```data-query-json``` command as shown above.
            After suggesting the query, wait for the query results. Once you receive the results, analyze them and provide insights to the user.
            If you receive an error instead of results, explain the error to the user and suggest how to modify the query to avoid the error.
            """

            # Modify the payload to instruct the LLM to generate a query
            augmented_prompt += "\nBased on the user's input, suggest a specific query to execute on the relevant dataset. Format the query suggestion as JSON."
            
            payload = {
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": augmented_prompt,
                "messages": self._build_messages(message, chat_history),
            }

            logger.debug(f"Payload for LLM request: {json.dumps(payload, indent=2)}")

            response = self._make_llm_request(payload)
            logger.debug(f"LLM response: {response}")

            # Include the retrieved RAG information in the response
            full_response = f"Retrieved Information:\n{formatted_info}\n\nAI Response:\n{response}"
            
            # Parse the LLM response to extract the suggested query
            suggested_query = self._extract_query_from_response(response)

            return {
                "response": full_response,
                "suggested_query": suggested_query
            }
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            raise

    def retrieve_relevant_info(self, message: str, chat_history: List[Dict]) -> Dict[str, List[Dict]]:
        logger.debug(f"Retrieving relevant info for message: {message}")
        # Combine the current message and chat history for context
        context = message + " " + " ".join([msg["content"] for msg in chat_history])
        
        # Search for relevant datasets and datacards
        datasets = self.dataset_search_service.search_datasets(context)
        datacards = self.datacard_search_service.search_datacards(context)
        
        logger.debug(f"Retrieved {len(datasets)} datasets and {len(datacards)} datacards")
        return {
            "datasets": datasets,
            "datacards": datacards
        }

    def _format_relevant_info(self, relevant_info):
        formatted_info = "Retrieved Information:\n"
        
        if 'datasets' in relevant_info:
            formatted_info += "Datasets:\n"
            for dataset in relevant_info['datasets']:
                name = dataset.get('name', 'Unnamed dataset')
                description = dataset.get('description', 'No description available')
                measures = ", ".join(dataset.get('measures', []))
                dimensions = ", ".join(dataset.get('dimensions', []))
                formatted_info += f"- {name}: {description}\n"
                formatted_info += f"  Measures: {measures}\n"
                formatted_info += f"  Dimensions: {dimensions}\n"
        
        if 'datacards' in relevant_info:
            formatted_info += "Datacards:\n"
            for datacard in relevant_info['datacards']:
                name = datacard.get('name', 'Unnamed datacard')
                description = datacard.get('description', 'No description available')
                formatted_info += f"- {name}: {description}\n"
        
        return formatted_info.strip()

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

    def _extract_query_from_response(self, response: str) -> Dict:
        import re
        import json

        # Look for the data-query-json block
        match = re.search(r'```data-query-json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.error("Failed to parse suggested query JSON")
        else:
            logger.error("No data-query-json block found in the response")
        return {}