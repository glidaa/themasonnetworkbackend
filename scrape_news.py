import requests
from bs4 import BeautifulSoup
import boto3
import json
import urllib3
import time
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('themasonnetwork_drudgescrape_2')

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
    try:
        option = Options()
        # option.headless = True
        option.add_argument("--headless=new") # for Chrome >= 109

        browser = webdriver.Chrome(options=option)
        browser.implicitly_wait(5)
        browser.get(url)
        
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        html = soup.prettify("utf-8")
        
        articles_parent_elements = browser.find_elements(By.XPATH, "//td[@align='LEFT']")
        for articles_parent in articles_parent_elements:
            articles_elements = articles_parent.find_elements(By.TAG_NAME, 'a')
            for article_element in articles_elements:
                article_text = article_element.text
                article_link = article_element.get_attribute('href')
                if not valid_news_title(article_text):
                    continue
                if table.get_item(Key={"newsId": str(hash(article_link))}).get("Item"):
                    continue
                table.put_item(Item={
                    "newsId": str(hash(article_link)),
                    "newsOriginalTitle": article_text,
                    "newsUrl": article_link,
                    "newsContent": "", # Placeholder for content
                    "newsRank": calculate_news_rank(),
                    "newsNewTitle": "", # When admin updates the title
                    "isScrapeContent": False,
                    "isJokesGenerated": False,
                    "isRender": allow_iframe(article_link),
                    "newsImageURL": "", # Added by admin,
                    # Timestamp can be sorted in descendent or ascentdent order
                    "createdTimeStamp": int(time.time())
                })
        print ("successfully scraped new data from Drudge")
    except Exception as e:
    # TODO: Should we change to selenium
        raise Exception("Error scraping drudgereport", str(e))
