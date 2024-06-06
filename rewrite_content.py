import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import boto3
import logger
import json

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

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

        print(article_body)

        return article_body
    
    except Exception as e:
        exception_str = "scraping_failure"
        return exception_str


def check_isRender(news_id):
    try:
        # Retrieve the item
        response = table.get_item(Key={'newsId': news_id})
        
        # Check if the item exists in the response
        if 'Item' in response:
            item = response['Item']
            
            # Retrieve the 'isRender' value
            is_render = item.get('isRender')
            return is_render
        else:
            logger.warning(f"Item with newsId '{news_id}' not found")
            return None
    except Exception as e:
        logger.error(f"Error getting item from DynamoDB: {e}")
        return None

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
    # print(response)


def rewrite_content(event, context):
    count = 0
    for entry in table.scan()["Items"]: 
        if not (entry["isRender"]):
            newsId = entry["newsId"]
            article_content = scrape_raw_content(entry["newsUrl"])
            update_table(
                table,
                ("newsId", newsId),
                [("isRender", False, True), ("article", None, article_content)]
            )    
        count += 1
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'{count} news rewrited'})
    }
