import requests
import json
import logging

class LLMModule:
    def __init__(self, prompt_template):
        self.prompt_template = prompt_template
        self.api_url = "http://127.0.0.1:1234/v1/chat/completions"
        self.model = "llama-3.2-1b-instruct"

    def prompt_to_json(self, input_json):
        # Prepare the data for the API request
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Always answer in JSON format."},
                {"role": "user", "content": self.prompt_template.format(html_content=input_json["html_content"])}
            ],
            "temperature": 0.7
        }

        # Log data before making the API request
        logging.info("Prepared data for API request:")
        logging.info(json.dumps(data, ensure_ascii=False, indent=4))

        # Make the API request
        try:
            response = requests.post(self.api_url, json=data, timeout=260)
            response.raise_for_status()
            response_data = response.json()
            logging.info(f"LLM response data: {response_data}")
            content = response_data['choices'][0]['message']['content']
            # Directly parse the content as JSON
            try:
                parsed_content = json.loads(content)
                logging.info(f"Parsed LLM content: {parsed_content}")
                return parsed_content
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON output: {e}")
                logging.error(f"Raw content: {content}")
                return None
        except requests.exceptions.Timeout:
            logging.error("LLM API request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during API request: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during LLM processing: {e}")
            return None
