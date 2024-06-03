import json
import boto3
from boto3.dynamodb.conditions import Attr
from concurrent.futures import ThreadPoolExecutor

# Initialize resources outside the handler
dynamodb = boto3.resource('dynamodb')
news_table = dynamodb.Table('themasonnetwork_drudgescrape')
jokes_table = dynamodb.Table('themasonnetwork_jokes')

def lambda_handler(event, context):
    # Define a batch size for scanning news table
    batch_size = 100
    
    # Use filter expression to scan news table
    filter_expression = Attr('isRender').eq(True) | (Attr('isScrapeContent').eq(True) & Attr('newsContent').ne(""))
    
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

    # Function to fetch jokes for a news item
    def fetch_jokes(news_item):
        news_id = news_item["newsId"]
        response = jokes_table.scan(
            FilterExpression=Attr('newsId').eq(news_id)
        )
        jokes = response.get("Items", [])
        news_item["jokes"] = sorted(jokes, key=lambda x: int(x["jokeRank"]), reverse=True)
        return news_item
    
    # Use ThreadPoolExecutor to fetch jokes in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        filtered_news = list(executor.map(fetch_jokes, filtered_news))

    return {
        'statusCode': 200,
        'body': filtered_news
    }