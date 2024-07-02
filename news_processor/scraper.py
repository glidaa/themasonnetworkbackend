from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import boto3
import urllib3
import time
from datetime import datetime, timezone
from LLMs import LLMModule
import requests


class Scraper():
    
    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument('--headless=new')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36'
        self.options.add_argument('user-agent={0}'.format(user_agent))

        self.browser = webdriver.Chrome(options=self.options)
    
    def get_page(self,url, wait_time):
        self.browser.implicitly_wait(wait_time)
        self.browser.get(url)


class NewsScraper(Scraper):
    
    def __init__(self) -> None:
        super().__init__()
        self.drudge_url = 'https://drudgereport.com/'
        self.dynamodb_client = boto3.resource('dynamodb')
        self.drudge_news_table = self.dynamodb_client.Table('themasonnetwork_drudgescrape')

    # This function allows to see if the article can be rendered    
    def allow_iframe(self, url):
        http = urllib3.PoolManager()
        try:
            response = http.request('HEAD', url)
        except Exception as e:
            return False
        headers = response.headers
        x_frame_options = headers.get('X-Frame-Options')
        content_security_policy = headers.get('Content-Security-Policy')

        can_render_in_iframe = True
        if x_frame_options or (content_security_policy and 'frame-ancestors' in content_security_policy):
            can_render_in_iframe = False

        return can_render_in_iframe

    
    def calculate_news_rank(self):
        base_unix = 1717167540
        now_unix = int(time.time())

        today_date = datetime.fromtimestamp(base_unix, tz=timezone.utc).date()
        
        scrape_date = datetime.fromtimestamp(now_unix, tz=timezone.utc).date()
        
        date_diff = (scrape_date - today_date).days
        
        return date_diff + 1  # Adding 1 to make the rank 1-based
    
    def valid_news_title(self, article_title):
        return not (article_title.isupper() or article_title == '')
    
    def store_articles(self, articles_elements):
        for article_element in articles_elements:
            article_title = article_element.text
            article_link = article_element.get_attribute('href')
            if not self.valid_news_title(article_title):
                continue
            if self.drudge_news_table.get_item(Key={"newsId": str(hash(article_link))}).get("Item"):
                continue
            self.drudge_news_table.put_item(Item={
                    "newsId": str(hash(article_link)),
                    "newsOriginalTitle": article_title,
                    "newsUrl": article_link,
                    "newsContent": "", # Placeholder for content
                    "newsRank": self.calculate_news_rank(),
                    "newsNewTitle": "", # When admin updates the title
                    "isScrapeContent": False,
                    "isJokesGenerated": False,
                    "isRender": self.allow_iframe(article_link),
                    "newsImageURL": "", # Added by admin,
                    # Timestamp can be sorted in descendent or ascentdent order
                    "createdTimeStamp": int(time.time())
            })

    def scrape_news(self):
        self.get_page(url=self.drudge_url, wait_time=2)
        articles_parent_elements = self.browser.find_elements(By.XPATH, "//td[@align='LEFT']")
        for articles_parent in articles_parent_elements:
            articles_elements = articles_parent.find_elements(By.TAG_NAME, 'a')
            self.store_articles(articles_elements)


class ContentScraper(Scraper):
    
    def __init__(self) -> None:
        super().__init__()
        self.dynamodb_client = boto3.resource('dynamodb')
        self.drudge_news_table = self.dynamodb_client.Table('themasonnetwork_drudgescrape')

    def format_article(self, article):
        if article["isScrapeContent"] or article["isRender"]:
            return -1

        article = self.scrape_raw_content(article["newsUrl"])

        if article == "scraping_failure" or article == "":
            return -1

        return self.format_raw_content(article)

    def format_raw_content(self, content):
        llm_client = LLMModule()
        message = f"""You're given a scraped article from a webpage with miscellaneous garbage from scraping. 
            Rephrase, clean, format the article and return it as plain string without including any garbage, metadata or irrelevant 
            information. The article should be formatted in a way that it can be read by a human. 
            The article should be less than 4000 characters.
            Here's the scraped article: {content}
        """
        return llm_client.prompt(message)
        
    def scrape_raw_content(self, url):
        # consider moving this to selenium ?
        self.get_page(url=url,wait_time=1)
        # TODO: add handler for msn.com pages
        all_contents_tags = self.browser.find_elements(By.TAG_NAME, 'p')
        article_body = ""
        for content_tag in all_contents_tags:
            article_text = content_tag.text
            article_body += article_text
        return article_body
    
    def update_table(self, table: any, primary_key: tuple, attributes: list):
        update_expression = 'SET '
        expression_attribute_names = {}
        expression_attribute_values = {}

        for i, attribute in enumerate(attributes):
            if i > 0:
                update_expression += ', '
            update_expression += f'#{attribute[0]} = :{attribute[0]}'
            expression_attribute_names[f'#{attribute[0]}'] = attribute[0]
            expression_attribute_values[f':{attribute[0]}'] = attribute[2]

        response = table.update_item(
            Key={
                primary_key[0]: primary_key[1]
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='UPDATED_NEW'
        )
        print("UpdateItem succeeded:")
        print(response)

    def format_articles(self):
        for entry in self.drudge_news_table.scan()["Items"]:
            try:
                print (entry)
                article = self.format_article(entry)
                if article == -1:
                    continue
                
            except (TimeoutError, requests.exceptions.Timeout):
                print("TimeoutError")
                continue

            self.update_table(
                    self.drudge_news_table,
                    ("newsId", entry["newsId"]),
                    [("newsContent", entry["newsContent"], article), ("isScrapeContent", False, True)]
                )