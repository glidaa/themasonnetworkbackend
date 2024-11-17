# Code for handling adding images will be placed here
import boto3

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

def add_image(event, context):
    newsId = event['newsId']
    newsImageURL  = event['image']
    
    # Update the item directly
    response = table.update_item(
        Key={
            'newsId': newsId
        },
        UpdateExpression="set #img = :i",
        ExpressionAttributeNames={
            '#img': 'newsImageURL'
        },
        ExpressionAttributeValues={
            ':i': newsImageURL
        },
        ReturnValues="UPDATED_NEW"
    )

    return response