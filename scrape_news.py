import requests
from bs4 import BeautifulSoup
import boto3
import time
from datetime import datetime, timezone

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape')

def valid_news_title(title: str) -> bool:
    return not (title.isupper() or title == '')

def calculate_news_rank():
    base_unix = 1716888352
    now_unix = int(time.time())

    today_date = datetime.fromtimestamp(base_unix, tz=timezone.utc).date()
    
    scrape_date = datetime.fromtimestamp(now_unix, tz=timezone.utc).date()
    
    date_diff = (today_date - scrape_date).days
    
    return date_diff + 1  # Adding 1 to make the rank 1-based


def scrap(event, context):
    url = 'https://drudgereport.com/'
    result = requests.get(url)

    if result.status_code == 200:
        content = result.text
        soup = BeautifulSoup(content, "html.parser")

        sections = soup.select("td[align='LEFT']")

        for section in sections:
            for i, link in enumerate(section.select("a")):
                if not valid_news_title(link.text):
                    continue

                table.put_item(Item={
                    "newsId": str(hash(link["href"])),
                    "newsOriginalTitle": link.text,
                    "newsUrl": link["href"],
                    "newsContent": "",
                    "newsRank": calculate_news_rank(),
                    "newsNewTitle": "",
                    "isScrapeContent": False,
                    "isJokesGenearted": False,
                    "isRender": True,
                    "newsImageURL": ""
                })
                
        return table.scan()
    else:
        raise Exception("Error scraping drudgereport", result.status_code)