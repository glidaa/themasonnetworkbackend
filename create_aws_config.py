import os
import configparser
from pathlib import Path
import sys

def setup_aws_credentials():
    print("=== AWS Credentials Setup ===")
    
    # Get user's home directory
    home = str(Path.home())
    print(f"\nHome directory: {home}")
    
    # Create .aws directory
    aws_dir = Path(home) / '.aws'
    print(f"\nCreating .aws directory at: {aws_dir}")
    
    try:
        aws_dir.mkdir(exist_ok=True)
        print("✓ .aws directory created/verified")
    except Exception as e:
        print(f"✗ Error creating .aws directory: {str(e)}")
        return
    
    # Get AWS credentials from user
    print("\nPlease enter your AWS credentials:")
    access_key = input("AWS Access Key ID: ")
    secret_key = input("AWS Secret Access Key: ")
    region = input("AWS Region (e.g., us-east-1): ")
    
    # Create credentials file
    credentials = configparser.ConfigParser()
    credentials['default'] = {
        'aws_access_key_id': access_key,
        'aws_secret_access_key': secret_key
    }
    
    # Create config file
    config = configparser.ConfigParser()
    config['default'] = {
        'region': region,
        'output': 'json'
    }
    
    # Write the files
    credentials_path = aws_dir / 'credentials'
    config_path = aws_dir / 'config'
    
    print("\nWriting configuration files:")
    try:
        with open(credentials_path, 'w') as f:
            credentials.write(f)
        print(f"✓ Credentials written to: {credentials_path}")
        
        with open(config_path, 'w') as f:
            config.write(f)
        print(f"✓ Config written to: {config_path}")
    except Exception as e:
        print(f"✗ Error writing configuration files: {str(e)}")
        return
    
    print("\nVerifying files exist:")
    print(f"Credentials file exists: {credentials_path.exists()}")
    print(f"Config file exists: {config_path.exists()}")
    
    if credentials_path.exists():
        print("\nCredentials file permissions:")
        print(oct(os.stat(credentials_path).st_mode)[-3:])
    
    print("\nTesting configuration...")
    try:
        import boto3
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        dynamodb = session.client('dynamodb')
        response = dynamodb.list_tables()
        print("✓ Successfully connected to AWS!")
        print("Tables:", response['TableNames'])
    except Exception as e:
        print(f"✗ Error testing connection: {str(e)}")
        print("\nDebug information:")
        print(f"Python version: {sys.version}")
        print(f"boto3 version: {boto3.__version__}")
        print(f"Working directory: {os.getcwd()}")

if __name__ == "__main__":
    setup_aws_credentials()
