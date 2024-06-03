import requests
from bs4 import BeautifulSoup
import boto3
from boto3.dynamodb.conditions import Key
import json
import urllib3
import os
import time
import hashlib
from datetime import datetime, timezone

MAX_ITEMS = int(os.environ.get('MAX_ITEMS'))
BASE_UNIX = int(os.environ.get('BASE_UNIX'))

dynamodb_client = boto3.resource('dynamodb')
news_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

def valid_news_title(title: str) -> bool:
    return not (title.isupper() or title == '')

def calculate_news_rank():
    now_unix = int(time.time())
    today_date = datetime.fromtimestamp(BASE_UNIX, tz=timezone.utc).date()
    scrape_date = datetime.fromtimestamp(now_unix, tz=timezone.utc).date()
    
    date_diff = (scrape_date - today_date).days
    
    return date_diff + 1  # Adding 1 to make the rank 1-based


def allow_iframe(url: str) -> bool:
    http = urllib3.PoolManager()
    try:
        response = http.request('HEAD', url)
    except:
        return False

    headers = response.headers
    x_frame_options = headers.get('X-Frame-Options')
    content_security_policy = headers.get('Content-Security-Policy')

    return not (x_frame_options or (content_security_policy and 'frame-ancestors' in content_security_policy))

def get_table_size():
    response = news_table.scan(
        Select='COUNT'
    )
    return response['Count']

def get_oldest_news_id():
    response = news_table.scan(
        ProjectionExpression="newsId, newsRank",
        FilterExpression="attribute_exists(newsRank)"
    )
    items = response['Items']
    if items:
        oldest_item = min(items, key=lambda x: int(x['newsRank']))
        return oldest_item['newsId']
    
    return None

def delete_jokes_by_news_id(news_id):
    # Scan jokes table to find all jokes with the given newsId
    response = jokes_table.scan(
        FilterExpression=Key('newsId').eq(news_id)
    )
    jokes = response.get('Items', [])

    # Delete each joke
    with jokes_table.batch_writer() as batch:
        for joke in jokes:
            batch.delete_item(
                Key={
                    'jokeId': joke['jokeId']
                }
            )

def scrap(event, context):
    url = 'https://drudgereport.com/'
    result = requests.get(url)

    if result.status_code == 200:
        content = result.text
        soup = BeautifulSoup(content, "html.parser")

        sections = soup.select("td[align='LEFT']")

        count = 0
        for section in sections:
            for i, link in enumerate(section.select("a")):
                if not valid_news_title(link.text):
                    continue

                if news_table.get_item(Key={"newsId": hashlib.md5(link["href"].encode()).hexdigest()}).get("Item"):
                    continue

                # Check the table size and remove the oldest item if needed
                table_size = get_table_size()
                if table_size >= MAX_ITEMS:
                    oldest_news_id = get_oldest_news_id()
                    if oldest_news_id:
                        news_table.delete_item(Key={"newsId": oldest_news_id})
                        delete_jokes_by_news_id(oldest_news_id)
                     

                news_table.put_item(Item={
                    "newsId": hashlib.md5(link["href"].encode()).hexdigest(),
                    "newsOriginalTitle": link.text,
                    "newsUrl": link["href"],
                    "newsContent": "", # Placeholder for content
                    "newsRank": calculate_news_rank(),
                    "newsNewTitle": "", # When admin updates the title
                    "isScrapeContent": False,
                    "isJokesGenerated": False,
                    "isRender": allow_iframe(link["href"]),
                    "newsImageURL": "" # Added by admin
                })
                count += 1
                
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'{count} news scraped'})
        }
    else:
        raise Exception("Error scraping drudgereport", result.status_code)