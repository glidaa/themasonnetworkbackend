import boto3

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')
articles_table = dynamodb_client.Table('themasonnetwork_drudgescrape')
subscribers_table = dynamodb_client.Table('themasonnetwork_subscribers')

def add_subscribers(user_email):
    # Create the item dictionary
    item = {
        'subscriber_id': str(hash(user_email)),
        'user_email': user_email,
    }
    try:
        subscribers_table.put_item(Item=item)
        print(f"Item added successfully: {item}")
    except Exception as e:
        print(f"Error adding item: {e}")

# if __name__ == "__main__":
#     user_email = "boskojeftic491@gmail.com"
#     temp_res = add_subscribers(user_email)
#     print(temp_res)
    