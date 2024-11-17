from flask import Flask, jsonify, send_from_directory
import boto3
import os
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.')

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/api/data', methods=['GET'])
def get_data():
    # Initialize a session using Amazon DynamoDB
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('REGION_NAME')
    )

    # Initialize DynamoDB resource
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('themasonnetwork_drudgescrape')

    # Scan the table to get all data
    response = table.scan()
    data = response.get('Items', [])

    logging.info(f"Fetched {len(data)} items from DynamoDB")

    return jsonify(data)

@app.route('/admin/<path:path>')
def serve_admin(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True)
