import boto3

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

def edit_title(event, context):
    newsId = event['newsId']
    newsNewTitle = event['title']

    # Update the item directly
    response = table.update_item(
        Key={
            'newsId': newsId
        },
        UpdateExpression="set #title = :t",
        ExpressionAttributeNames={
            '#title': 'newsNewTitle'
        },
        ExpressionAttributeValues={
            ':t': newsNewTitle
        },
        ReturnValues="UPDATED_NEW"
    )

    return response