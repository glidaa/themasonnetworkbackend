import boto3

def test_dynamo_connection():
    try:
        # Create DynamoDB client
        dynamodb = boto3.client('dynamodb')
        
        # Try to list tables
        response = dynamodb.list_tables()
        
        print("Successfully connected to DynamoDB!")
        print("Available tables:", response['TableNames'])
        
    except Exception as e:
        print("Error connecting to DynamoDB:", str(e))

if __name__ == "__main__":
    test_dynamo_connection()
