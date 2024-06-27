import boto3
import json

dynamodb_client = boto3.resource('dynamodb')
subscribers_table = dynamodb_client.Table('themasonnetwork_subscribers')
unsubscribers_table = dynamodb_client.Table('themasonnetwork_unsubscribers')

def unsubscribe_email(event, context):
    user_email = event["user_email"]
    response = subscribers_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("user_email").eq(user_email)
    )
    items = response["Items"]
    # found user
    if len(items) > 0:
        user = items[0]
        print (user)
        response_add = unsubscribers_table.put_item(Item=user)
        response_delete = subscribers_table.delete_item(
            Key={
                'subscriber_id': user['subscriber_id']
            },
        )
        status_delete = response_delete["ResponseMetadata"]["HTTPStatusCode"]
        status_add = response_add["ResponseMetadata"]["HTTPStatusCode"]
        if status_add == 200 and status_delete == 200:
                print(f'unsubscribed user {user_email}\n')
                return {
                    'statusCode': 200,
                    'body': json.dumps('unsubscribe successfully')
                }
    else:
        print ('Can not find user {user_email}')
        return {
            'statusCode': 404,
            'body': json.dumps('Can not find the specify email')
        }
    return response
