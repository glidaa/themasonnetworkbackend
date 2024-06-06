import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from bs4.element import Comment
from openai import OpenAI
import boto3
import os
import json
from dotenv import load_dotenv
load_dotenv()

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

client = OpenAI(
    api_key = os.environ['OPENAI_API_KEY']
)
def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def scrape_raw_content(url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': get_base_url(url),
    })

    try:
        response = session.get(url, timeout=10)
        content = response.text
        soup = BeautifulSoup(content, "html.parser")

        article_body = ""
        for p in soup.find_all('p'):
            article_body += p.get_text() + "\n"

        return article_body
    
    except Exception as e:

        return "scraping_failure"
  
def format_raw_content(article):
    messages=[
        {
            "role": "user",
            "content": f'''You're given a scraped article from a webpage with miscellaneous garbage from scraping. 
            Rephrase, clean, format the article and return it as plain string without including any garbage, metadata or irrelevant 
            information. The article should be formatted in a way that it can be read by a human. 
            The article should be less than 4000 characters.
            Here's the scraped article: {article}''',
        }
    ]
    
    chat_completion = client.chat.completions.create(
        messages= messages,
        model="gpt-3.5-turbo-1106",
    )
    
    return  chat_completion.choices[0].message.content

def update_table(table: any, primary_key: tuple, attributes: list):
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

def format_article(article):
    if article["isScrapeContent"] or article["isRender"]:
        return -1

    article = scrape_raw_content(article["newsUrl"])

    if article == "scraping_failure" or article == "":
        return -1

    return format_raw_content(article)

def format_articles(event, context):
    count = 0
    for entry in table.scan()["Items"]:
        try:
            article = format_article(entry)
            if article == -1:
                continue
        except (TimeoutError, requests.exceptions.Timeout):
            print("TimeoutError")
            continue

        update_table(
            table,
            ("newsId", entry["newsId"]),
            [("newsContent", entry["newsContent"], article), ("isScrapeContent", False, True)]
        )
        count += 1

    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'{count} news scraped'})
    }

