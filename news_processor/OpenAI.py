import os
from openai import OpenAI
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
import json
from langchain_openai import ChatOpenAI
from langchain_community.callbacks.manager import get_openai_callback
import logging

load_dotenv()

class OpenAIError(Exception):
    """Raised when an OpenAI API related error occurs."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ParsingError(Exception):
    """Raised when the LangChain parser fails to parse a response."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class LLMModule:
    def __init__(self, prompt_template=None) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logging.info("OpenAI API key set.")
        self.chat_client = ChatOpenAI(
            temperature=0.25,
            model_name='gpt-4',
        )
        if prompt_template is not None:
            self.prompt_template = ChatPromptTemplate.from_template(
                prompt_template
            )
    
    def prompt(self, message):
        logging.info(f"Sending message to OpenAI: {message}")
        messages = [
            {
                "role": "user",
                "content": message,
            }
        ]
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            logging.info(f"Received response from OpenAI: {reply}")
            return reply
        except Exception as e:
            logging.error(f"Error during OpenAI API call: {e}")
            raise OpenAIError(str(e)) from e

    def prompt_to_json(self, input_json, output_parser):
        prompt_messages = self.prompt_template.format_messages(**input_json)
        try:
            with get_openai_callback() as cb:
                response = self.chat_client(prompt_messages)
        except Exception as open_ai_exception:
            logging.error(f"Error during OpenAI API call: {open_ai_exception}")
            raise OpenAIError(str(open_ai_exception)) from open_ai_exception
        try:
            outline = output_parser.parse(response.content)
        except Exception as parsing_error:
            logging.error(f"Error parsing response: {parsing_error}")
            raise ParsingError(str(parsing_error)) from parsing_error
        return json.loads(outline.json())

class OpenAIArticleGenerator:
    def __init__(self, prompt_template=None):
        self.llm = LLMModule(prompt_template=prompt_template)

    def generate_article(self, url):
        """Generates an article based on the provided URL."""
        prompt = (
            f"As a Fox News reporter, write a structured article about the content from this URL: {url}. "
            "Start by explaining the problem, cite examples, explain what happened, and provide an opinion on what this could mean."
        )
        return self.llm.prompt(prompt)

    def generate_from_message(self, message):
        """Generates a response from OpenAI based on the given message."""
        return self.llm.prompt(message)

    def generate_from_json(self, input_json, output_parser):
        """Generates a response from OpenAI and parses it into JSON."""
        return self.llm.prompt_to_json(input_json, output_parser)
