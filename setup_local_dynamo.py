import boto3

def create_tables_in_sydney():
    # Create DynamoDB resource in Sydney region
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    
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
        print("Created news table in Sydney region:", table.table_name)
        table.wait_until_exists()
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
        print("Created jokes table in Sydney region:", table.table_name)
        table.wait_until_exists()
    except Exception as e:
        print("Jokes table might already exist:", str(e))

def check_sydney_tables():
    # Connect to Sydney region
    dynamodb = boto3.client('dynamodb', region_name='ap-southeast-2')
    
    # List all tables
    response = dynamodb.list_tables()
    tables = response['TableNames']
    
    print("\nTables in Sydney region (ap-southeast-2):")
    for table in tables:
        if 'themasonnetwork' in table:
            print(f"- {table}")
            # Get table status
            desc = dynamodb.describe_table(TableName=table)
            status = desc['Table']['TableStatus']
            print(f"  Status: {status}")

if __name__ == "__main__":
    print("Setting up DynamoDB tables in Sydney region (ap-southeast-2)...")
    create_tables_in_sydney()
    print("\nVerifying tables...")
    check_sydney_tables()
