from langchain.output_parsers import PydanticOutputParser
from langchain.callbacks import get_openai_callback
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
import json
import datetime
import boto3
import hashlib
import os

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

class SourcesError(Exception):
    """
        Raised when insufficient / irrelevant sources are provided for generation.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

content_generator = ChatOpenAI(
    temperature=0.25,
    model_name='gpt-4o',
)

jokes_generation_template = """\
    You're a late night host that's famous for his reaction to news. And, you're given a news headlines and content that you will read as jokes.
    For each news headline, you will read the headline and content and then make 4 one-liner jokes about them with a rank.
    Make all jokes around 100 characters.
    Make the joke without double quotes, "Headline: ", "Joke: " or anything else.
    Here's the headline: {title}
    Here's the article content: {content}
    Return only the outline as json in the following format: {format_instructions}
"""

class Joke(BaseModel):
  joke: str = Field(description="The one-liner joke generated")
  rank: int = Field(description="The rank of the joke")

class JokesList(BaseModel):
    jokes: List[Joke] = Field(description="The list of generated joke-rank pairs")

def generate_jokes_list(news_title, news_content):
    prompt = ChatPromptTemplate.from_template(jokes_generation_template)
    output_parser = PydanticOutputParser(pydantic_object=JokesList)
    
    jokes_request = prompt.format_messages(title=news_title, content=news_content,
                            format_instructions=output_parser.get_format_instructions())
    try:
        with get_openai_callback() as cb:
            jokes_response = content_generator(jokes_request)
    except Exception as open_ai_exception:
        raise OpenAIError(str(open_ai_exception)).with_traceback(open_ai_exception.__traceback__)

    try:
        outline = output_parser.parse(jokes_response.content)
    except Exception as parsing_error:
        # The JSON response from OpenAI is not valid
        raise ParsingError(str(parsing_error)).with_traceback(parsing_error.__traceback__)    

    # No need for a parser here, the response is a string
    return json.loads(outline.json())

dynamodb_client = boto3.resource('dynamodb')
news_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

def update_table(table: any, primary_key: tuple, attributes: list):
    # attributes = [(property_name, from, to), ...]
    update_expression = 'SET '
    expression_attribute_names = {}
    expression_attribute_values = {}

    for i, attribute in enumerate(attributes):
        if i > 0:
            update_expression += ', '
        update_expression += f'#{attribute[0]} = :{attribute[0]}'
        expression_attribute_names[f'#{attribute[0]}'] = attribute[0]
        expression_attribute_values[f':{attribute[0]}'] = attribute[2]

    response = table.update_item(
        Key={
            primary_key[0]: primary_key[1]
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues='UPDATED_NEW'
    )
    print("UpdateItem succeeded:")
    print(response)

def make_jokes(event, context):
    news_count = 0
    jokes_count = 0
    for entry in news_table.scan()["Items"]:
        if entry["isJokesGenerated"]:
            continue

        try:
            jokes = generate_jokes_list(entry['newsOriginalTitle'], entry['newsContent'])['jokes']
        except:
            continue
        for item in jokes:
            jokes_table.put_item(Item={
                "jokeId": hashlib.md5(item['joke'].encode()).hexdigest(),
                "newsId": entry["newsId"],
                "newsTitle": entry["newsOriginalTitle"],
                "newsRank": entry["newsRank"],
                "jokeContent": item['joke'],
                "jokeRank": item['rank'],
                "dateCreated": str(datetime.datetime.now()),
                "creator": "system"
            })

        update_table(
            news_table,
            ("newsId", entry["newsId"]),
            [("isJokesGenerated", False, True)]
        )
        news_count += 1
        jokes_count += len(jokes)

    return {
            'statusCode': 200,
            'body': json.dumps({'message': f'{news_count} news processed, {jokes_count} jokes generated'})
    }