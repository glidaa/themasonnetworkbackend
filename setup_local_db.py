import boto3

def create_local_tables():
    # Create a local DynamoDB client
    dynamodb = boto3.resource('dynamodb', 
                            endpoint_url='http://localhost:8000',
                            region_name='local',
                            aws_access_key_id='dummy',
                            aws_secret_access_key='dummy')
    
    # Create news table
    try:
        table = dynamodb.create_table(
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
        table = dynamodb.create_table(
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

    # Create subscribers table
    try:
        table = dynamodb.create_table(
            TableName='themasonnetwork_subscribers',
            KeySchema=[
                {
                    'AttributeName': 'subscriber_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'subscriber_id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Created subscribers table:", table.table_name)
    except Exception as e:
        print("Subscribers table might already exist:", str(e))

def check_local_data():
    # Connect to local DynamoDB
    dynamodb = boto3.resource('dynamodb', 
                            endpoint_url='http://localhost:8000',
                            region_name='local',
                            aws_access_key_id='dummy',
                            aws_secret_access_key='dummy')
    
    # Scan news table
    table = dynamodb.Table('themasonnetwork_drudgescrape')
    response = table.scan()
    items = response['Items']
    
    print(f"\nFound {len(items)} news items:")
    for item in items:
        print(f"\nTitle: {item.get('newsDrudgeTitle', 'No title')}")
        print(f"URL: {item.get('newsUrl', 'No URL')}")
        print(f"Content: {item.get('newsContent', 'No content')[:100]}...")  # Show first 100 chars of content

if __name__ == "__main__":
    print("Setting up local DynamoDB tables...")
    create_local_tables()
    print("\nChecking local data...")
    check_local_data()
