import boto3
import json

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')
articles_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
subscribers_table = dynamodb_client.Table('themasonnetwork_subscribers')

def add_subscribers(event, context):
    user_email = event["user_email"]
    # Create the item dictionary
    item = {
        'subscriber_id': str(hash(user_email)),
        'user_email': user_email,
    }
    try:
        subscribers_table.put_item(Item=item)
        print(f"Item added successfully: {item}")
    except Exception as e:
        print(f"Error adding item: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Added user_email successfully')
    }

