import boto3

dynamodb = boto3.resource('dynamodb')
table_name = 'themasonnetwork_jokes'
table = dynamodb.Table(table_name)

def clear_table(event, context):
    try:
        scan = table.scan()
        with table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'jokeId': each['jokeId'],
                    }
                )
        return {
            'statusCode': 200,
            'body': 'Table cleared successfully'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }