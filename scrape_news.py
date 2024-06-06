import requests
from bs4 import BeautifulSoup
import boto3
import json
import urllib3
import time
from datetime import datetime, timezone

MAX_ITEMS = 100

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

def valid_news_title(title: str) -> bool:
    return not (title.isupper() or title == '')

def calculate_news_rank():
    base_unix = 1717167540
    now_unix = int(time.time())

    today_date = datetime.fromtimestamp(base_unix, tz=timezone.utc).date()
    
    scrape_date = datetime.fromtimestamp(now_unix, tz=timezone.utc).date()
    
    date_diff = (scrape_date - today_date).days
    
    return date_diff + 1  # Adding 1 to make the rank 1-based


def allow_iframe(url: str) -> bool:
    if not url:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'URL parameter is required'})
        }

    http = urllib3.PoolManager()
    try:
        response = http.request('HEAD', url)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    headers = response.headers
    x_frame_options = headers.get('X-Frame-Options')
    content_security_policy = headers.get('Content-Security-Policy')

    can_render_in_iframe = True
    if x_frame_options or (content_security_policy and 'frame-ancestors' in content_security_policy):
        can_render_in_iframe = False

    return can_render_in_iframe

def get_table_size():
    response = table.scan(
        Select='COUNT'
    )
    return response['Count']

def get_oldest_news_id():
    response = table.scan(
        ProjectionExpression="newsId, newsRank",
        FilterExpression="attribute_exists(newsRank)"
    )
    items = response['Items']
    if items:
        oldest_item = min(items, key=lambda x: int(x['newsRank']))
        return oldest_item['newsId']
    return None

def scrape_news(event, context):
    url = 'https://drudgereport.com/'
    result = requests.get(url)

    if result.status_code == 200:
        content = result.text
        soup = BeautifulSoup(content, "html.parser")

        sections = soup.select("td[align='LEFT']")

        count = 0
        for section in sections:
            for i, link in enumerate(section.select("a")):
                if not valid_news_title(link.text):
                    continue

                if table.get_item(Key={"newsId": str(hash(link["href"]))}).get("Item"):
                    continue

                # Check the table size and remove the oldest item if needed
                table_size = get_table_size()
                if table_size >= MAX_ITEMS:
                    oldest_news_id = get_oldest_news_id()
                    print(oldest_news_id)
                    if oldest_news_id:
                        table.delete_item(Key={"newsId": oldest_news_id})

                table.put_item(Item={
                    "newsId": str(hash(link["href"])),
                    "newsOriginalTitle": link.text,
                    "newsUrl": link["href"],
                    "newsContent": "", # Placeholder for content
                    "newsRank": calculate_news_rank(),
                    "newsNewTitle": "", # When admin updates the title
                    "isScrapeContent": False,
                    "isJokesGenerated": False,
                    "isRender": allow_iframe(link["href"]),
                    "newsImageURL": "" # Added by admin
                })
                count += 1
        print(count)        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'{count} news scraped'})
        }
    else:
        raise Exception("Error scraping drudgereport", result.status_code)
    

# if __name__ == "__main__":
#     temp_res = get_oldest_news_id()
#     print(temp_res)
