import logging
import boto3
from news_processor.LLMs import LLMModule
from pydantic import BaseModel, Field
from typing import List
from langchain.output_parsers import PydanticOutputParser
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Joke(BaseModel):
  joke: str = Field(description="The one-liner joke generated")
  rank: int = Field(description="The rank of the joke")


class JokesList(BaseModel):
    jokes: List[Joke] = Field(description="The list of generated joke-rank pairs")


class Joker():
    
    def __init__(self) -> None:
        self.dynamodb_client = boto3.resource('dynamodb')
        self.news_table = self.dynamodb_client.Table('themasonnetwork_drudgescrape')
        self.jokes_table = self.dynamodb_client.Table('themasonnetwork_jokes')
        self.jokes_generation_template = """\
            You're a late night host. And, you're given a news headlines that you will read as jokes.
            For each news headline, you will read the headline and then make 4 one-liner jokes about it.
            Make all jokes around 100 characters.
            Make the joke without double quotes, "Headline: ", "Joke: " or anything else.
            Here's the headline: {title}
            Return only the outline as json in the following format: {format_instructions}
        """
        self.LLMModule = LLMModule(
            prompt_template=self.jokes_generation_template
        )
        
    def update_table(self, table: any, primary_key: tuple, attributes: list):
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
        logging.info(f"Updated table {table.name} for key {primary_key}: {response}")

    
    def generate_jokes_list(self, news_title):
        output_parser = PydanticOutputParser(pydantic_object=JokesList)
        input_to_llm = {
            "title": news_title,
            "format_instructions": output_parser.get_format_instructions()
        }
        logging.info(f"Generating jokes for news title: {news_title}")
        generated_jokes = self.LLMModule.prompt_to_json(
            input_json=input_to_llm,
            output_parser=output_parser
        )
        logging.info(f"Generated jokes: {generated_jokes}")
        return generated_jokes
    
    def make_jokes(self):
        
        for entry in self.news_table.scan()["Items"]:
            # This typo cause bad data
            if "isJokesGenearted" in entry.keys():
                continue
            if entry["isJokesGenerated"]:
                continue
            try:
                jokes = self.generate_jokes_list(
                    entry['newsOriginalTitle']
                )['jokes']
            except Exception as e:
                logging.error(f"Error generating jokes: {str(e)}")
                continue
            # This is to update table
            for item in jokes:
                logging.info(f"Storing joke: {item['joke']}")
                self.jokes_table.put_item(Item={
                    "jokeId": str(hash(item['joke'])),
                    "newsId": entry["newsId"],
                    "newsTitle": entry["newsOriginalTitle"],
                    "newsRank": entry["newsRank"],
                    "jokeContent": item['joke'],
                    "jokeRank": item['rank'],
                    "dateCreated": str(datetime.datetime.now()),
                    "creator": "system"
                })

            self.update_table(
                self.news_table,
                ("newsId", entry["newsId"]),
                [("isJokesGenerated", False, True)]
            )
