# AWS DynamoDB Setup Guide

## Prerequisites

1. Install AWS CLI:
   ```bash
   pip install awscli boto3
   ```

2. Configure AWS Credentials:
   Option 1 - Using Python Setup Script (Recommended):
   ```bash
   python create_aws_config.py
   ```
   This will:
   - Prompt for your AWS credentials
   - Create the necessary config files
   - Test the connection automatically

   Option 2 - Manual Configuration:
   Create these files manually:
   ```
   ~/.aws/credentials:
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key

   ~/.aws/config:
   [default]
   region = your_region
   output = json
   ```

## Testing AWS Connection

Run the test script to verify your AWS setup:
```bash
python test_aws.py
```

This will:
- Check for environment variables
- Verify AWS credential files
- Test connection to DynamoDB
- List any existing tables

## Direct DynamoDB Access

1. Use setup_db.py to manage your DynamoDB tables:
   ```python
   # For AWS DynamoDB
   dynamodb = boto3.resource('dynamodb',
                           region_name='your-region')  # e.g., 'us-east-1'
   ```

## API Gateway + Lambda Setup

1. Create a Lambda Function:
   - Go to AWS Lambda console
   - Create new function
   - Use Python runtime
   - Add DynamoDB permissions to Lambda role:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "dynamodb:GetItem",
                   "dynamodb:PutItem",
                   "dynamodb:UpdateItem",
                   "dynamodb:DeleteItem",
                   "dynamodb:Scan",
                   "dynamodb:Query"
               ],
               "Resource": "your-dynamodb-table-arn"
           }
       ]
   }
   ```

2. Create API Gateway:
   - Go to API Gateway console
   - Create new REST API
   - Create resources and methods (GET, POST, etc.)
   - Link methods to Lambda function
   - Deploy API

3. Example Lambda Function:
   ```python
   import boto3
   import json

   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('your-table-name')

   def lambda_handler(event, context):
       try:
           # Example: GET request to scan table
           if event['httpMethod'] == 'GET':
               response = table.scan()
               return {
                   'statusCode': 200,
                   'body': json.dumps(response['Items'])
               }
           
           # Example: POST request to add item
           elif event['httpMethod'] == 'POST':
               body = json.loads(event['body'])
               table.put_item(Item=body)
               return {
                   'statusCode': 200,
                   'body': json.dumps({'message': 'Item added successfully'})
               }
               
       except Exception as e:
           return {
               'statusCode': 500,
               'body': json.dumps({'error': str(e)})
           }
   ```

4. Update Local Code:
   ```python
   import requests

   API_ENDPOINT = 'your-api-gateway-url'

   # Example: Get items
   response = requests.get(API_ENDPOINT)
   items = response.json()

   # Example: Add item
   data = {'id': '123', 'content': 'test'}
   response = requests.post(API_ENDPOINT, json=data)
   ```

## Security Considerations

1. Use API keys or AWS IAM authentication for API Gateway
2. Enable CORS if needed
3. Use environment variables for sensitive values
4. Consider using AWS Secrets Manager for credentials
5. Implement proper error handling and logging

## Testing

1. Test Direct Access:
   ```python
   python setup_db.py
   ```

2. Test API Gateway:
   ```bash
   curl -X GET your-api-gateway-url
   curl -X POST -H "Content-Type: application/json" -d '{"id":"123","content":"test"}' your-api-gateway-url
   ```

## Troubleshooting

1. Run the test script to diagnose issues:
   ```bash
   python test_aws.py
   ```

2. Common issues:
   - Missing AWS credentials
   - Incorrect region
   - Insufficient IAM permissions
   - Network connectivity problems

3. If you need to reconfigure:
   ```bash
   python create_aws_config.py
