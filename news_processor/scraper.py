from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import boto3
import urllib3
import time
from LLMs import LLMModule
import requests
from selenium.common.exceptions import TimeoutException
from boto3.dynamodb.conditions import Attr
from urllib.parse import urlparse
import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import List


class ArticleInfo(BaseModel):
    content: str = Field(description="The content of the article")
    title: str = Field(
            description="The title of the article"
    )

class Scraper():
    
    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
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
        self.visited_site = {}
        self.default_a_tags_keywords = ["CALIFORNIA NOTICE", "DO NOT SELL MY INFO", "CUSTOM",
                "PRIVACY POLICY", "AGENCE FRANCE-PRESSE", "AP TOP", "AP RADIO", "ARAB NEWS", "BLOOMBERG", "DEUTSCHE PRESSE-AGENTUR",
                "DEUTCHE WELLE", "INTERFAX", "ITAR-TASS", "KYODO", "MCCLATHY [DC]", "NHK", "PRAVDA", "PRESS TRUST INDIA", "REUTERS POLITICS WORLD",
                "XINHUA", "YONHAP", "WEATHER ACTION", "ZOOM EARTH", "QUAKE SHEET", "ARCHIVES", "RECENT HEADLINES..."]
        self.article_extractor_template = """
            You will be given html code of a page of a news article.
            I want to know the title of the article 
            and extract the content of the articles.
            Here is the html code : {html_content}
            Return the results as json in the following format: {format_instruction}
        """
        self.LLMModule = LLMModule(
            prompt_template=self.article_extractor_template
        )

    def _is_article(self, drudge_title, article_url):
        if article_url == "https://www.france24.com/en/live-news/":
            return False
        if "youtube.com" in article_url:
            return False
        if "trends.google.com" in article_url:
            return False
        return drudge_title not in self.default_a_tags_keywords
    
    # This function allows to see if the article can be rendered    
    def _allow_iframe(self, url):
        http = urllib3.PoolManager()
        if "msn.com" in url:
            return True
        try:
            response = http.request('HEAD', url=url,  timeout=2)
        except TimeoutError:
            return False
        except Exception as e:
            return False
        headers = response.headers
        x_frame_options = headers.get('X-Frame-Options')
        content_security_policy = headers.get('Content-Security-Policy')
        can_render_in_iframe = True
        if x_frame_options or (content_security_policy and 'frame-ancestors' in content_security_policy):
            can_render_in_iframe = False
        return can_render_in_iframe
    
    def _check_duplicate(self, article_url):
        filter_expression = Attr('newsUrl').eq(article_url)
        scan_params = {
            'FilterExpression': filter_expression,
        }
        response = self.drudge_news_table.scan(**scan_params)
        filtered_news = response.get('Items', [])
        print (filtered_news)
        return len(filtered_news) > 0

    def _get_deplicate(self, article_url):
        filter_expression = Attr('newsUrl').eq(article_url)
        scan_params = {
            'FilterExpression': filter_expression,
        }
        response = self.drudge_news_table.scan(**scan_params)
        filtered_news = response.get('Items', [])
        return filtered_news[0]
    
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


    def _click_allow(self, article_url):
        if "france24.com" in article_url and "france24.com" not in self.visited_site.keys():
            wait = WebDriverWait(self.browser, 2)  # Wait for up to 10 seconds
            element = wait.until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
            element.click()
            self.visited_site["france24.com"] = 1
        if "yahoo.com" in article_url and "yahoo.com" not in self.visited_site.keys():
            wait = WebDriverWait(self.browser, 2)  # Wait for up to 10 seconds
            element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'accept-all')))
            element.click()
            self.visited_site["yahoo.com"] = 1
        
    def _format_title(self, input_string):
        # This regex pattern matches any character that is not a letter or number
        pattern = re.compile('[\W_]+')
        # Substitute found patterns with an empty string
        return pattern.sub('', input_string)

    def _scrape_the_article(self, article_url, drudge_title):
        # Manual handle by each pages
        self.get_page(url=article_url,wait_time=3)
        self._click_allow(article_url)
        self.browser.set_page_load_timeout(600)
        html_content = self.browser.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        # Removing unnecessary tags for minimizing tokens
        for tag in soup(['style', 'script', 'link', 'meta', 'button', 'svg', 'img', 'iframe', 'span']):
            tag.decompose()
        clean_html = soup.prettify("utf-8")
        drudge_title = self._format_title(drudge_title)
        output_parser = PydanticOutputParser(pydantic_object=ArticleInfo)
        input_to_llm = {
            "html_content": clean_html,
            "format_instruction": output_parser.get_format_instructions()
        }
        response_llm = self.LLMModule.prompt_to_json(
            input_json=input_to_llm,
            output_parser=output_parser
        )
        print (response_llm)
        return response_llm

    def scrape_news(self):
        self.get_page(url=self.drudge_url, wait_time=2)
        drudge_page_structure = []
        article_tags = self.browser.find_elements(By.TAG_NAME, "a")
        
        # The reason for creating a temp tag is to have a clear 
        for article_tag in article_tags:
            drudge_title = article_tag.text
            article_url = article_tag.get_attribute('href')
            if self._is_article(drudge_title, article_url):
                drudge_page_structure.append([drudge_title, article_url])
        current_base_unix = int(time.time())
        position_tag = len(drudge_page_structure)
        for drudge_tag in drudge_page_structure:
            drudge_title = drudge_tag[0]
            article_url = drudge_tag[1]
            print (drudge_title)
            print (article_url)
            if self._check_duplicate(article_url):
                entry = self._get_deplicate(article_url)
                self.update_table(
                    self.drudge_news_table,
                    ("newsId", entry["newsId"]),
                    [("newsRank", entry["newsRank"], str(current_base_unix + position_tag))]
                )
            item = {
                    "newsId": str(hash(article_url)),
                    "newsOriginalTitle": "",
                    "newsDrudgeTitle": drudge_title,
                    "newsUrl": article_url,
                    "newsContent": "", # Placeholder for content
                    "newsRank": str(current_base_unix + position_tag),
                    "newsNewTitle": "", # When admin updates the title
                    "isScrapeContent": False,
                    "isJokesGenerated": False,
                    "isRender": self._allow_iframe(article_url),
                    "newsImageURL": "", # Added by admin,
                    "createdTimeStamp": int(time.time())
            }
            if item["isRender"]:
                print("item added")
                self.drudge_news_table.put_item(Item=item)
            else :    
                article_info = self._scrape_the_article(article_url, drudge_title)
                item["newsOriginalTitle"] = article_info["title"]
                item["newsContent"] = article_info["content"]
                self.drudge_news_table.put_item(Item=item)
            position_tag = position_tag - 1
        print ("scraped news successfully")
