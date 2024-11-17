# Code for handling fetching news will be placed here
import json
import boto3
import time
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key
from concurrent.futures import ThreadPoolExecutor

# Initialize resources outside the handler
dynamodb = boto3.resource('dynamodb')
news_table = dynamodb.Table('themasonnetwork_drudgescrape')
jokes_table = dynamodb.Table('themasonnetwork_jokes')

def lambda_handler(event, context):
    # Define a batch size for scanning news table
    batch_size = 1000
    
    # Use filter expression to scan news table
    filter_expression = Attr('isRender').eq(True) | (Attr('isScrapeContent').eq(True) & Attr('newsContent').ne(""))
    
    start_time = time.time()
    # Perform the scan in batches
    scan_params = {
        'FilterExpression': filter_expression,
        'Limit': batch_size
    }
    response = news_table.scan(**scan_params)
    filtered_news = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = news_table.scan(**scan_params)
        filtered_news.extend(response.get('Items', []))

    # Sort news items by newsRank
    filtered_news.sort(key=lambda x: int(x["newsRank"]), reverse=True)

    # get first 100 news items
    filtered_news = filtered_news[:100]

    scan_news_time = time.time()
    #print(f"Scanned {len(filtered_news)} news items in {scan_news_time - start_time} seconds")

    filtered_news_ids = [news_item["newsId"] for news_item in filtered_news]
    # query all jokes in filtered_news_ids
    response = jokes_table.scan(
        FilterExpression=Attr('newsId').is_in(filtered_news_ids)
    )
    jokes = response.get("Items", [])

    # Map jokes to news items
    for news_item in filtered_news:
        news_id = news_item["newsId"]
        news_item["jokes"] = sorted([joke for joke in jokes if joke["newsId"] == news_id], key=lambda x: int(x["jokeRank"]), reverse=True)

    fetch_jokes_time = time.time()
    #print(f"Fetched jokes for {len(filtered_news)} news items in {fetch_jokes_time - scan_news_time} seconds")

    return {
        'statusCode': 200,
        'body': filtered_news
    }