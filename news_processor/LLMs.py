from openai import OpenAI
import os
from langchain.prompts import ChatPromptTemplate

import json
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback


class OpenAIError(Exception):
    """
        Raised when an OpenAI API related error occurs.
        the error could be caused by a bad request, server error, token error, etc.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ParsingError(Exception):
    """
        Raised when the langchain parser fails to parse a response from OpenAI.
        Could be caused by hitting a completion tokens limit, or a bad response from OpenAI.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LLMModule:
    
    def __init__(self, prompt_template=None) -> None:
        self.llm_client = OpenAI(
            api_key=os.environ['OPENAI_API_KEY']
        )
        self.chat_client = ChatOpenAI(
            temperature=0.25,
            model_name='gpt-4-turbo',
        )
        if prompt_template is not None:
            self.prompt_template = ChatPromptTemplate.from_template(
                prompt_template
            )
    
    # This function is called when prompt_template is None
    def prompt(self, message):
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ]
    
        chat_completion = self.llm_client.chat.completions.create(
            messages= messages,
            model="gpt-4-turbo",
        )
        
        return  chat_completion.choices[0].message.content

    def prompt_to_json(
            self,
            input_json,
            output_parser
        ):
        prompt_messages = self.prompt_template.format_messages(**input_json)
        try:
            with get_openai_callback() as cb:
                jokes_response = self.chat_client(prompt_messages)
                # jokes_response = chat_completion.choices[0].message.content
        except Exception as open_ai_exception:
            raise OpenAIError(str(open_ai_exception)).with_traceback(open_ai_exception.__traceback__)
        try:
            outline = output_parser.parse(jokes_response.content)
        except Exception as parsing_error:
            # The JSON response from OpenAI is not valid
            raise ParsingError(str(parsing_error)).with_traceback(parsing_error.__traceback__)    

        # No need for a parser here, the response is a string
        return json.loads(outline.json())
