import os
import anthropic
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, dataset_search_service, datacard_search_service):
        self.dataset_search_service = dataset_search_service
        self.datacard_search_service = datacard_search_service
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.debug("LLMService initialized")
        self.query_format_instructions = """
        When suggesting a query, please format it as a JSON object wrapped in a ```data-query-json``` command, like this:

        ```data-query-json
        {
            "dataset": "organization/dataset_name",
            "measures": ["at_least_one_measure_field"],
            "dimensions": ["at_least_one_dimension_field"],
            "filters": [],
            "order": ["field ASC" or "field DESC"],
            "limit": number_of_results
        }
        ```

        Always use this exact format when suggesting a query. The dataset should be the full name including the organization, e.g., "us_lbs/unemployment_rate".
        IMPORTANT:
        1. Use the exact field names as provided in the dataset information. Do not substitute or rename fields.
        2. Always include at least one measure and one dimension in every query.
        3. The "measures" and "dimensions" fields must never be empty.
        4. If you're unsure about which measure or dimension to use, include the most relevant ones based on the user's question.
        5. For time-series data, always include a dimension with type date or time field as a dimension.
        """

    def generate_response(self, message: str, chat_history: List[Dict], system_prompt: str, retrieved_info: Dict) -> Dict:
        logger.debug(f"Generating response for message: {message}")
        
        try:
            # Format the relevant information
            formatted_info = self._format_relevant_info(retrieved_info)
            
            # Augment the system prompt with the retrieved information and query format instructions
            augmented_prompt = f"""
            {system_prompt}

            Relevant information:
            {formatted_info}

            {self.query_format_instructions}

            Based on the user's input, suggest a specific query to execute on the relevant dataset. 
            Format the query suggestion as JSON wrapped in the ```data-query-json``` command as shown above.
            Make sure to include the full dataset name with organization (e.g., "us_lbs/unemployment_rate") in the "dataset" field.
            Use ONLY the exact field names provided in the dataset information for measures and dimensions.
            ALWAYS include at least one measure and one dimension in your query.
            After suggesting the query, provide a brief explanation of what the query will do and how it relates to the user's question.
            """

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

            # Parse the LLM response to extract the suggested query
            suggested_query = self._extract_query_from_response(response)

            # Validate the suggested query
            if not self._is_valid_query(suggested_query):
                raise ValueError("Generated query is invalid: missing required fields or empty measures/dimensions")

            return {
                "response": response,
                "suggested_query": suggested_query
            }
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            raise

    def _is_valid_query(self, query: Dict) -> bool:
        return (
            query.get('dataset') and
            query.get('measures') and
            query.get('dimensions') and
            len(query['measures']) > 0 and
            len(query['dimensions']) > 0
        )

    def _format_relevant_info(self, relevant_info: Dict) -> str:
        formatted_info = []
        
        if 'datasets' in relevant_info:
            formatted_info.append("Datasets:")
            for dataset in relevant_info['datasets']:
                dataset_info = [
                    f"- {dataset['name']} ({dataset['organization']}/{dataset['dataset_slug']}): {dataset['description']}",
                    f"  Measures: {', '.join(dataset['measures'])}",
                    f"  Dimensions: {', '.join(dataset['dimensions'])}"
                ]
                formatted_info.extend(dataset_info)
        
        if 'datacards' in relevant_info:
            formatted_info.append("Datacards:")
            for datacard in relevant_info['datacards']:
                formatted_info.append(f"- {datacard['name']} ({datacard['organization']}/{datacard['datacard_slug']}): {datacard['description']}")
        
        return "\n".join(formatted_info)

    def _build_messages(self, message: str, chat_history: List[Dict]) -> List[Dict]:
        messages = []
        last_role = None
        for entry in chat_history:
            role = "user" if entry.get("role") == "user" else "assistant"
            content = entry.get('content', '')
            if role != last_role:
                messages.append({"role": role, "content": content})
                last_role = role
            else:
                messages[-1]["content"] += f"\n{content}"
        
        if last_role != "user":
            messages.append({"role": "user", "content": message})
        else:
            messages[-1]["content"] += f"\n{message}"
        
        return messages

    def _make_llm_request(self, payload: dict) -> str:
        try:
            response = self.client.messages.create(**payload)
            content = response.content[0].text
            
            if response.stop_reason == 'stop_sequence':
                content += "/>"
            
            return content
        except Exception as e:
            logger.error(f"Error making LLM request: {str(e)}", exc_info=True)
            raise

    def _extract_query_from_response(self, response: str) -> Dict:
        import re

        match = re.search(r'```data-query-json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.error("Failed to parse suggested query JSON")
        else:
            logger.error("No data-query-json block found in the response")
        return {}