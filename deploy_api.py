import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def deploy_api():
    # Initialize a session using Amazon API Gateway
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='ap-southeast-2'  # Sydney region
    )

    apigateway = session.client('apigateway')

    # Create a new API
    api_response = apigateway.create_rest_api(
        name='NewsAPI',
        description='API for managing news articles',
        endpointConfiguration={
            'types': ['REGIONAL']
        }
    )

    api_id = api_response['id']
    print(f"API created with ID: {api_id}")

    # Create resources and methods for each endpoint
    resources = [
        ('/news', 'GET'),
        ('/newNews', 'POST'),
        ('/editNews', 'PUT'),
        ('/edit_title', 'PATCH'),
        ('/add-image', 'POST'),
        ('/add-joke', 'POST'),
        ('/store_email', 'POST')
    ]

    for resource_path, method in resources:
        resource_response = apigateway.create_resource(
            restApiId=api_id,
            parentId=api_response['rootResourceId'],
            pathPart=resource_path.strip('/')
        )
        print(f"Resource created: {resource_path}")

        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_response['id'],
            httpMethod=method,
            authorizationType='NONE'
        )
        print(f"Method {method} added to resource {resource_path}")

    # Deploy the API
    deployment_response = apigateway.create_deployment(
        restApiId=api_id,
        stageName='production'
    )
    print(f"API deployed to stage: {deployment_response['id']}")

if __name__ == "__main__":
    deploy_api()
