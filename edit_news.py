import json
import boto3
import hashlib
from datetime import datetime

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')
articles_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

def valid_news_title(title: str) -> bool:
    return not (title.isupper() or title == '')


def lambda_handler(event, context):
    # Parse input
    if 'newsId' not in event:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing parameter: newsId'})
        }
    newsId = event['newsId']
    newsDrudgeTitle = event.get('newsDrudgeTitle')
    newsNewTitle = event.get('newsNewTitle')
    jokes = event.get('jokes')
    newsRank = event.get('newsRank')
    newsContent = event.get('newsContent')
    isRender = event.get('isRender')
    newsUrl = event.get('newsUrl')
    newsImageURL = event.get('newsImageURL')
    
    # print("newsNewTitle:", newsNewTitle)
    if (newsNewTitle and not valid_news_title(newsNewTitle)) \
        or (newsDrudgeTitle and not valid_news_title(newsDrudgeTitle)):
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid article title')
        }

    # Update item in the DynamoDB table
    try:
        articles_table.update_item(
            Key={
                "newsId": newsId
            },
            UpdateExpression="SET newsNewTitle = :newsNewTitle, newsContent = :newsContent, \
                newsRank = :newsRank, isRender = :isRender, newsUrl = :newsUrl, newsImageURL = :newsImageURL",
            ExpressionAttributeValues={
                ":newsNewTitle": newsNewTitle,
                ":newsContent": newsContent,
                ":newsRank": newsRank,
                ":isRender": isRender,
                ":newsUrl": newsUrl,
                ":newsImageURL": newsImageURL
            }
        )
        if jokes is not None:
            for joke in jokes:
                if 'jokeId' in joke:
                    jokes_table.update_item(
                        Key={
                            "jokeId": joke.get('jokeId')
                        },
                        UpdateExpression="SET jokeContent = :jokeContent, jokeRank = :jokeRank, \
                            newsTitle = :newsDrudgeTitle, newsRank = :newsRank",
                        ExpressionAttributeValues={
                            ":jokeContent": joke['joke'],
                            ":jokeRank": joke['rank'],
                            ":newsDrudgeTitle": newsDrudgeTitle,
                            ":newsRank": newsRank
                        }
                    )
                else:
                    joke_id = hashlib.md5(joke['joke'].encode()).hexdigest()
                    jokes_table.put_item(
                        Item={
                        "jokeId": joke_id,
                        "newsId": newsId,
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
        'body': json.dumps({'message': 'News article updated successfully', 'newsId': newsId})
    }

