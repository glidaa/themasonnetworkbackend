import boto3

def test_dynamodb_connection():
    try:
        # Create a DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name='ap-southeast-2')
        
        # List tables
        response = dynamodb.list_tables()
        
        print("Successfully connected to DynamoDB!")
        print("Available tables:", response['TableNames'])
        
    except Exception as e:
        print("Error connecting to DynamoDB:", str(e))

if __name__ == "__main__":
    test_dynamodb_connection()
