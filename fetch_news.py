import json
import boto3

def lambda_handler(event, context):
    dynamodb_client = boto3.resource('dynamodb')
    news_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
    jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

    # Filter news
    # 1- If renderable within iframe
    # 2- If not renderable within iframe but has content
    filtered_news = []
    for item in news_table.scan()["Items"]:
        if item["isRender"]:
            filtered_news.append(item)
        else:
            if item["isScrapeContent"] and item["newsContent"] != "":
                filtered_news.append(item)
    filtered_news.sort(key=lambda x: int(x["newsRank"]), reverse=True)
    
    # Join jokes
    for news_item in filtered_news:
        news_id = news_item["newsId"]
        # Fetch jokes for the current news item
        response = jokes_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('newsId').eq(news_id)
        )
        jokes = response.get("Items", [])
        # Add jokes to the news item
        news_item["jokes"] = jokes

    return {
        'statusCode': 200,
        'body': filtered_news
    }
