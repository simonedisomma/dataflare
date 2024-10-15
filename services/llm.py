import os
import anthropic
from typing import List, Dict
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import sys

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, dataset_search_service, datacard_search_service):
        self.dataset_search_service = dataset_search_service
        self.datacard_search_service = datacard_search_service
        self.client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.debug("LLMService initialized")
        self.code_execution_instructions = """
        When suggesting Python code for data analytics, please format it as a code block wrapped in a ```execute-code``` command, like this:

        ```execute-code
        import pandas as pd
        import matplotlib.pyplot as plt

        # Load or query data
        df = pd.query_dataset('dataset_name', select=['field1', 'field2'], filters=[{'field': 'date', 'op': '>=', 'value': '2020-01-01'}])

        # Your data analysis code here
        print(df.head())

        # For visualizations:
        plt.figure(figsize=(10, 6))
        df.plot(kind='bar')
        plt.title('Sample Plot')
        plt.xlabel('Index')
        plt.ylabel('Values')
        plt.savefig('plot.png')  # Save the plot as a file
        plt.close()  # Close the plot to free up memory

        # Get dataset metadata
        dataset_metadata = pd.get_dataset_metadata('dataset_name')
        print(dataset_metadata)
        ```

        Always use this exact format when suggesting code to execute. The code should be self-contained and include all necessary imports.
        To query data, use the pd.query() function with the following parameters:
        - dataset: The full name of the dataset (e.g., 'us_lbs/unemployment_rate')
        - select: A list of fields to retrieve (fields have to be in the dataset definition)
        - filters: A list of filter conditions (optional)
        - order: A list of fields to order by (optional)
        - limit: The maximum number of records to retrieve (optional)

        To load an entire dataset, use pd.load_dataset('dataset_name').

        IMPORTANT: 
        1. Only use fields listed in the dataset definition.
        2. Create only 1 code snippet per current user LLM interaction.
        3. Always save matplotlib plots as files using plt.savefig() and close them with plt.close().
        4. After the code is executed, provide a summary of the results but not propose any additional code.
        """

    def generate_response(self, message: str, chat_history: List[Dict], system_prompt: str, retrieved_info: Dict) -> Dict:
        logger.debug(f"Generating response for message: {message}")
        
        try:
            formatted_info = self._format_relevant_info(retrieved_info)
            
            augmented_prompt = f"""
            {system_prompt}

            Relevant information:
            {formatted_info}

            {self.code_execution_instructions}

            Based on the user's input, suggest Python code for data analytics that includes querying, analysis, and visualization as needed.
            Make sure the code is complete and can be executed independently.
            For visualizations, use matplotlib and ensure the plot is saved or displayed.
            Don't apologize for anything.
            Be concise.
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
            suggested_code = self._extract_code_from_response(response)

            code_execution_result = None
            if suggested_code:
                code_execution_result = self.execute_code(suggested_code)

            assessment = None
            # Generate a follow-up response to assess the results
            if code_execution_result:
                follow_up_prompt = f"""
                Based on the previous response and the following results, provide an assessment:

                {code_execution_result.get('output', code_execution_result.get('error', ''))}

                Analyze these results and provide insights or recommendations.
                """
                follow_up_payload = {
                    "model": "claude-3-5-sonnet-20240620",
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": self._build_messages(follow_up_prompt, chat_history + [{"role": "assistant", "content": response}]),
                }
                assessment = self._make_llm_request(follow_up_payload)

            return {
                "message": response,
                "suggested_code": suggested_code,
                "code_execution_result": code_execution_result,
                "assessment": assessment
            }
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            raise

    def _format_relevant_info(self, relevant_info: Dict) -> str:
        formatted_info = []
        
        if 'datasets' in relevant_info:
            formatted_info.append("Datasets:")
            for dataset in relevant_info['datasets']:
                dataset_info = [
                    f"- {dataset['name']} ({dataset['organization']}/{dataset['dataset_slug']}): {dataset['description']}",
                    f"  Fields: {', '.join(dataset['fields'])}"
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

    def _extract_code_from_response(self, response: str) -> str:
        import re

        match = re.search(r'```execute-code\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def execute_code(self, code: str) -> Dict:
        try:
            output_buffer = io.StringIO()
            local_vars = {}

            # Redirect stdout to capture print outputs
            sys.stdout = output_buffer
            
            try:
                exec(code, globals(), local_vars)
            except Exception as e:
                return {"error": str(e)}
            finally:
                # Restore stdout
                sys.stdout = sys.__stdout__

            output = output_buffer.getvalue()

            plot_base64 = None
            if os.path.exists('plot.png'):
                with open('plot.png', 'rb') as image_file:
                    plot_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                os.remove('plot.png')  # Remove the file after reading

            dataframes = {name: var.to_html() for name, var in local_vars.items() if isinstance(var, pd.DataFrame)}

            return {
                "output": output,
                "plot": plot_base64,
                "dataframes": dataframes
            }
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}", exc_info=True)
            return {"error": str(e)}