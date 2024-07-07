import json
import boto3
import hashlib
import time
from datetime import datetime, timezone

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')
scrape_table = dynamodb_client.Table('themasonnetwork_drudgescrape') 
jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

def valid_news_title(title: str) -> bool:
    return not (title.isupper() or title == '')


def lambda_handler(event, context):
    # Parse input
    try:
        newsDrudgeTitle = event['newsDrudgeTitle']
        jokes = event['jokes']
        newsRank = event['newsRank']
        newsContent = event['newsContent']
        isRender = event['isRender']
        newsImageURL = event['newsImageURL']
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing parameter: {str(e)}'})
        }

    # Validate title
    if not valid_news_title(newsDrudgeTitle):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid news title'})
        }

    # Create a unique news ID
    news_id = hashlib.md5(newsDrudgeTitle.encode()).hexdigest()

    # Put item in the DynamoDB table
    try:
        scrape_table.put_item(Item={
            "newsId": news_id,
            "newsDrudgeTitle": newsDrudgeTitle,
            "newsUrl": "",  # Placeholder for URL
            "newsContent": newsContent,
            "newsRank": newsRank,
            "newsNewTitle": "",  # Placeholder for updated title by admin
            "isScrapeContent": False,
            "isJokesGenerated": False,
            "isRender": isRender,
            "newsImageURL": newsImageURL
        })
        for joke in jokes:
            joke_id = hashlib.md5(joke['joke'].encode()).hexdigest()
            jokes_table.put_item(Item={
                "jokeId": joke_id,
                "newsId": news_id,
                "newsTitle": newsDrudgeTitle,
                "newsRank": newsRank,
                "jokeContent": joke['joke'],
                "jokeRank": joke['rank'],
                "dateCreated": str(datetime.now()),
                "creator": "system"
            })
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'News article saved successfully', 'newsId': news_id})
    }
