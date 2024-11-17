import boto3
import os

class DynamoDBSetup:
    def __init__(self, use_local=False):  # Default to AWS DynamoDB
        if use_local:
            self.dynamodb = boto3.resource('dynamodb',
                                         endpoint_url='http://localhost:8000',
                                         region_name='local',
                                         aws_access_key_id='dummy',
                                         aws_secret_access_key='dummy')
        else:
            # Use AWS DynamoDB
            self.dynamodb = boto3.resource('dynamodb',
                                         region_name=os.getenv('AWS_REGION', 'ap-southeast-2'))  # Default to Sydney region

    def create_tables(self):
        # Create news table
        try:
            table = self.dynamodb.create_table(
                TableName='themasonnetwork_drudgescrape',
                KeySchema=[
                    {
                        'AttributeName': 'newsId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'newsId',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Created news table:", table.table_name)
        except Exception as e:
            print("News table might already exist:", str(e))

        # Create jokes table
        try:
            table = self.dynamodb.create_table(
                TableName='themasonnetwork_jokes',
                KeySchema=[
                    {
                        'AttributeName': 'jokeId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'jokeId',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Created jokes table:", table.table_name)
        except Exception as e:
            print("Jokes table might already exist:", str(e))

    def check_data(self):
        # Scan news table
        table = self.dynamodb.Table('themasonnetwork_drudgescrape')
        response = table.scan()
        items = response['Items']
        
        print(f"\nFound {len(items)} news items:")
        for item in items:
            print(f"\nTitle: {item.get('newsDrudgeTitle', 'No title')}")
            print(f"URL: {item.get('newsUrl', 'No URL')}")
            print(f"Content: {item.get('newsContent', 'No content')[:100]}...")

if __name__ == "__main__":
    # For AWS DynamoDB
    aws_db = DynamoDBSetup(use_local=False)
    print("Setting up AWS DynamoDB tables...")
    aws_db.create_tables()
    print("\nChecking AWS data...")
    aws_db.check_data()
