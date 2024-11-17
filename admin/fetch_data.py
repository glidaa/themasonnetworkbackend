import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_all_data():
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

    # Save data to a JSON file
    with open('admin/data.json', 'w') as f:
        json.dump(data, f, indent=4)

    print("Data fetched and saved to admin/data.json")

if __name__ == "__main__":
    fetch_all_data()
