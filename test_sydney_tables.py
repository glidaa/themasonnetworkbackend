import boto3
import uuid
from datetime import datetime

def test_sydney_tables():
    # Create DynamoDB resource in Sydney region
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    
    # Test news table
    try:
        news_table = dynamodb.Table('themasonnetwork_drudgescrape')
        
        # Try to write a test item
        test_news_id = str(uuid.uuid4())
        news_table.put_item(
            Item={
                'newsId': test_news_id,
                'newsDrudgeTitle': 'Test News Title',
                'newsUrl': 'http://test.com',
                'newsContent': 'This is a test news item',
                'timestamp': str(datetime.now())
            }
        )
        print("✓ Successfully wrote to news table")
        
        # Try to read the item back
        response = news_table.get_item(
            Key={
                'newsId': test_news_id
            }
        )
        if 'Item' in response:
            print("✓ Successfully read from news table")
            print("Test item:", response['Item']['newsDrudgeTitle'])
        
    except Exception as e:
        print("Error with news table:", str(e))

    # Test jokes table
    try:
        jokes_table = dynamodb.Table('themasonnetwork_jokes')
        
        # Try to write a test item
        test_joke_id = str(uuid.uuid4())
        jokes_table.put_item(
            Item={
                'jokeId': test_joke_id,
                'jokeContent': 'This is a test joke',
                'timestamp': str(datetime.now())
            }
        )
        print("✓ Successfully wrote to jokes table")
        
        # Try to read the item back
        response = jokes_table.get_item(
            Key={
                'jokeId': test_joke_id
            }
        )
        if 'Item' in response:
            print("✓ Successfully read from jokes table")
            print("Test item:", response['Item']['jokeContent'])
            
    except Exception as e:
        print("Error with jokes table:", str(e))

if __name__ == "__main__":
    print("Testing Sydney region tables...")
    test_sydney_tables()
