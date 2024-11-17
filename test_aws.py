import boto3
import os
import sys

def test_aws_configuration():
    print("=== AWS Configuration Test ===")
    
    # Check if AWS credentials exist in environment
    print("\nChecking environment variables:")
    if 'AWS_ACCESS_KEY_ID' in os.environ:
        print("✓ AWS_ACCESS_KEY_ID is set")
    else:
        print("✗ AWS_ACCESS_KEY_ID is not set")
    
    if 'AWS_SECRET_ACCESS_KEY' in os.environ:
        print("✓ AWS_SECRET_ACCESS_KEY is set")
    else:
        print("✗ AWS_SECRET_ACCESS_KEY is not set")
    
    if 'AWS_DEFAULT_REGION' in os.environ:
        print("✓ AWS_DEFAULT_REGION is set to:", os.environ['AWS_DEFAULT_REGION'])
    else:
        print("✗ AWS_DEFAULT_REGION is not set")
    
    # Check AWS credentials file
    home = os.path.expanduser("~")
    credentials_path = os.path.join(home, '.aws', 'credentials')
    config_path = os.path.join(home, '.aws', 'config')
    
    print("\nChecking AWS credential files:")
    print(f"Credentials file ({credentials_path}):", "exists" if os.path.exists(credentials_path) else "not found")
    print(f"Config file ({config_path}):", "exists" if os.path.exists(config_path) else "not found")
    
    print("\nTrying to connect to AWS:")
    try:
        # Try to create a DynamoDB client
        session = boto3.Session()
        dynamodb = session.client('dynamodb')
        
        # Get the current credentials being used
        creds = session.get_credentials()
        if creds is None:
            print("✗ No AWS credentials found")
        else:
            print("✓ Found AWS credentials")
            
        # Try to list tables
        response = dynamodb.list_tables()
        print("✓ Successfully connected to DynamoDB!")
        print("Tables found:", response['TableNames'])
        
    except Exception as e:
        print("✗ Error connecting to AWS:", str(e))
        print("\nTo configure AWS credentials, you can:")
        print("1. Set environment variables:")
        print("   AWS_ACCESS_KEY_ID=your_access_key")
        print("   AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("   AWS_DEFAULT_REGION=your_region")
        print("\n2. Or create credentials file:")
        print("   Create ~/.aws/credentials with:")
        print("   [default]")
        print("   aws_access_key_id = your_access_key")
        print("   aws_secret_access_key = your_secret_key")
        print("\n3. Or use AWS CLI to configure:")
        print("   python -m awscli configure")

if __name__ == "__main__":
    test_aws_configuration()
