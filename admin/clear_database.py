import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def clear_database():
    # Initialize a session using Amazon DynamoDB
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('REGION_NAME')
    )

    # Initialize DynamoDB resource
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('themasonnetwork_drudgescrape')

    # Scan the table to get all data
    response = table.scan()
    data = response.get('Items', [])

    # Delete each item
    with table.batch_writer() as batch:
        for item in data:
            batch.delete_item(
                Key={
                    'newsId': item['newsId']
                }
            )
    print("Database cleared.")

if __name__ == "__main__":
    clear_database()
