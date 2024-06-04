import boto3
import datetime

dynamodb_client = boto3.resource('dynamodb')
scrape_table = dynamodb_client.Table('themasonnetwork_drudgescrape') 
jokes_table = dynamodb_client.Table('themasonnetwork_jokes')

def add_joke(event, context):
    newsId = event["newsId"]
    joke = event["joke"]
    joke_rank = event["jokeRank"]

    news = scrape_table.get_item(Key={"newsId": newsId}).get("Item")
    print(news)

    response = jokes_table.put_item(Item={
        "jokeId": str(hash(joke)),
        "newsId": newsId,
        "newsTitle": news['newsOriginalTitle'],
        "newsRank": news['newsRank'], 
        "jokeContent": joke,
        "jokeRank": joke_rank,
        "dateCreated": str(datetime.datetime.now()),
        "creator": "admin"
    })
    
    return response

# if __name__ == "__main__":
#     event = {
#         "newsId": "2da9a6992446440fb9facd638365ef49",
#         "joke": "Amazon is really good?",
#         "jokeRank": 2
#     }
#     context="ok"
#     temp_res = add_joke(event, context)
#     print(temp_res)