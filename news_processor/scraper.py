import os
# Suppress TensorFlow messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Disable Hugging Face warning messages
logging.getLogger('transformers').setLevel(logging.ERROR)

# Your existing imports
import requests
from bs4 import BeautifulSoup
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import boto3
import urllib3
import time
from news_processor.LLMs import LLMModule
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from requests.exceptions import SSLError
from boto3.dynamodb.conditions import Attr
from urllib.parse import urlparse
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import List, Dict, Any
from news_processor.exludedlinks import exclude_links
from news_processor.wontrender import wontrender_sites
from selenium.common.exceptions import WebDriverException
import socket

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging to file and console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(f'logs/scraper_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                        logging.StreamHandler()
                    ])

class ArticleInfo(BaseModel):
    content: str = Field(description="The content of the article")
    title: str = Field(description="The title of the article")

    @classmethod
    def get_format_instructions(cls) -> str:
        return json.dumps(cls.schema(), indent=4)

class Scraper():
    
    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36'
        self.options.add_argument('user-agent={0}'.format(user_agent))
        self.browser = self.start_browser()
        self.llm_module = LLMModule(
            prompt_template=self.article_extractor_template
        )
    def start_browser(self):
        try:
            logging.info("Starting WebDriver")
            return webdriver.Chrome(options=self.options)
        except WebDriverException as e:
            logging.error(f"Failed to start WebDriver: {e}")
            raise

    def restart_browser(self):
        try:
            logging.info("Restarting WebDriver")
            self.browser.quit()
            self.browser = self.start_browser()
        except Exception as e:
            logging.error(f"Error restarting WebDriver: {e}")

    def check_port(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                logging.info(f"Port {port} is open")
            else:
                logging.warning(f"Port {port} is not open")

    def get_page(self, url, wait_time=10, retries=3):
        for attempt in range(retries):
            try:
                logging.info(f"Attempt {attempt + 1}: Navigating to {url}")
                self.browser.implicitly_wait(wait_time)
                self.browser.set_page_load_timeout(wait_time + 30)
                self.browser.get(url)
                WebDriverWait(self.browser, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                current_url = self.browser.current_url
                if current_url != url:
                    logging.warning(f"Redirected to {current_url}")
                return True
            except TimeoutException:
                logging.warning(f"Timeout on attempt {attempt + 1}. Retrying...")
            except WebDriverException as e:
                logging.error(f"WebDriverException encountered: {e}")
                self.restart_browser()
            except Exception as e:
                logging.error(f"Error loading {url}: {e}")
        logging.error(f"Failed to load {url} after {retries} attempts.")
        return False

class NewsScraper(Scraper):
    
    def __init__(self) -> None:
        super().__init__()
        self.drudge_url = 'https://drudgereport.com/'
        self.dynamodb_client = boto3.resource('dynamodb', region_name='ap-southeast-2')
        self.drudge_news_table = self.dynamodb_client.Table('themasonnetwork_drudgescrape')
        self.visited_site = {}
        self.site_behaviors = {
            "france24.com": {
                "has_iframe": False,
                "consent_button": {"by": By.ID, "value": "didomi-notice-agree-button"}
            },
            "yahoo.com": {
                "has_iframe": True,
                "iframe_selector": {"by": By.CLASS_NAME, "value": "consent-iframe"},
                "consent_button": {"by": By.CLASS_NAME, "value": "accept-all"}
            }
        }
        self.iframe_sites = {}
        self.article_extractor_template = """
            You will be given html code of a page of a news article.
            I want you to write a new punchy article in the voice of a Fox News reporter, providing solid opinions on what has happened.
            Here is the html code: {html_content}
            Return the results as json in the following format: {format_instruction}
        """
        self.LLMModule = LLMModule(
            prompt_template=self.article_extractor_template
        )

    def _is_article(self, drudge_title, article_url):
        if article_url in exclude_links.values() or drudge_title in exclude_links:
            logging.info(f"Excluding link: {drudge_title} - {article_url}")
            return False
        return True
    
    def _detect_iframe_rendering(self, url):
        try:
            domain = self._get_domain(url)
            logging.info(f"Checking iframe rendering for {domain}")
            
            if domain in self.iframe_sites:
                return self.iframe_sites[domain]
                
            iframes = self.browser.find_elements(By.TAG_NAME, "iframe")
            has_content_iframe = False
            
            for iframe in iframes:
                try:
                    self.browser.switch_to.frame(iframe)
                    content_markers = self.browser.find_elements(By.TAG_NAME, "article")
                    if content_markers:
                        has_content_iframe = True
                        break
                except:
                    pass
                finally:
                    self.browser.switch_to.default_content()
            
            self.iframe_sites[domain] = has_content_iframe
            logging.info(f"Iframe rendering detected: {has_content_iframe}")
            return has_content_iframe
            
        except Exception as e:
            logging.error(f"Error detecting iframe rendering for {url}: {str(e)}")
            return False
            
    def _get_domain(self, url):
        domain = urlparse(url).netloc
        logging.info(f"Extracted domain: {domain}")
        return domain
        
    def _click_allow(self, article_url):
        domain = self._get_domain(article_url)
        logging.info(f"Handling consent for {domain}")
        
        if domain in self.site_behaviors:
            behavior = self.site_behaviors[domain]
            
            if domain not in self.visited_site:
                try:
                    wait = WebDriverWait(self.browser, 20)
                    
                    if behavior["has_iframe"]:
                        iframe = wait.until(EC.presence_of_element_located(
                            (behavior["iframe_selector"]["by"], behavior["iframe_selector"]["value"])
                        ))
                        self.browser.switch_to.frame(iframe)
                    
                    element = wait.until(EC.element_to_be_clickable(
                        (behavior["consent_button"]["by"], behavior["consent_button"]["value"])
                    ))
                    element.click()
                    
                    if behavior["has_iframe"]:
                        self.browser.switch_to.default_content()
                        
                    self.visited_site[domain] = 1
                    logging.info(f"Consent handled for {domain}")
                    
                except TimeoutException:
                    logging.error(f"Timeout waiting for consent button on {article_url}")
                except Exception as e:
                    logging.error(f"Error handling consent for {article_url}: {str(e)}")
                finally:
                    if behavior["has_iframe"]:
                        self.browser.switch_to.default_content()
        else:
            try:
                has_iframe = self._detect_iframe_rendering(article_url)
                self.site_behaviors[domain] = {
                    "has_iframe": has_iframe,
                    "consent_button": {"by": By.CLASS_NAME, "value": "accept-all"}
                }
                self._try_common_consent_patterns(article_url, has_iframe)
            except Exception as e:
                logging.error(f"Error handling unknown site {article_url}: {str(e)}")
    
    def _try_common_consent_patterns(self, url, check_iframes=False):
        logging.info(f"Trying common consent patterns for {url}")
        common_patterns = [
            {"by": By.CLASS_NAME, "value": "accept-all"},
            {"by": By.ID, "value": "accept-cookies"},
            {"by": By.XPATH, "value": "//button[contains(text(), 'Accept')]"},
            {"by": By.XPATH, "value": "//button[contains(text(), 'Allow')]"},
        ]
        
        wait = WebDriverWait(self.browser, 10)
        
        if check_iframes:
            iframes = self.browser.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    self.browser.switch_to.frame(iframe)
                    for pattern in common_patterns:
                        try:
                            element = wait.until(EC.element_to_be_clickable(
                                (pattern["by"], pattern["value"])
                            ))
                            element.click()
                            logging.info(f"Clicked consent button in iframe for {url}")
                            return True
                        except:
                            continue
                finally:
                    self.browser.switch_to.default_content()
        
        for pattern in common_patterns:
            try:
                element = wait.until(EC.element_to_be_clickable(
                    (pattern["by"], pattern["value"])
                ))
                element.click()
                logging.info(f"Clicked consent button for {url}")
                return True
            except:
                continue
                
        logging.warning(f"No consent button clicked for {url}")
        return False

    def _should_render(self, url):
        domain = self._get_domain(url)
        logging.info(f"Checking if site should render: {domain}")
        
        if any(site in domain for site in wontrender_sites):
            logging.info(f"Site {domain} in wontrender_sites list")
            return False
            
        try:
            http = urllib3.PoolManager()
            response = http.request('HEAD', url=url, timeout=2)
            headers = response.headers
            x_frame_options = headers.get('X-Frame-Options')
            content_security_policy = headers.get('Content-Security-Policy')
            
            if x_frame_options or (content_security_policy and 'frame-ancestors' in content_security_policy):
                logging.info(f"Site {domain} has frame restrictions")
                return False
                
        except Exception as e:
            logging.error(f"Error checking headers for {url}: {e}")
            return False
            
        logging.info(f"Site {domain} can be rendered")
        return True
    
    def _check_duplicate(self, article_url):
        try:
            logging.info(f"Checking for duplicates in database for {article_url}")
            self.drudge_news_table.load()
            filter_expression = Attr('newsUrl').eq(article_url)
            scan_params = {
                'FilterExpression': filter_expression,
            }
            response = self.drudge_news_table.scan(**scan_params)
            filtered_news = response.get('Items', [])
            logging.info(f"Checked for duplicates: {len(filtered_news)} found for {article_url}")
            return len(filtered_news) > 0
        except self.dynamodb_client.meta.client.exceptions.ResourceNotFoundException:
            logging.error("DynamoDB table not found.")
            return False

    def _get_deplicate(self, article_url):
        logging.info(f"Retrieving duplicate entry for {article_url}")
        filter_expression = Attr('newsUrl').eq(article_url)
        scan_params = {
            'FilterExpression': filter_expression,
        }
        response = self.drudge_news_table.scan(**scan_params)
        filtered_news = response.get('Items', [])
        return filtered_news[0]
    
    def update_table(self, table: any, primary_key: tuple, attributes: list):
        logging.info(f"Updating table for {primary_key[1]}")
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
        logging.info(f"UpdateItem succeeded for {primary_key[1]}: {response}")

    def _format_title(self, input_string):
        pattern = re.compile('[\W_]+')
        formatted_title = pattern.sub('', input_string)
        logging.info(f"Formatted title: {formatted_title}")
        return formatted_title

    def _check_llm_server(self):
        try:
            logging.info("Checking LLM server status")
            response = requests.get("http://127.0.0.1:1234/health")
            if response.status_code == 200:
                logging.info("LLM server is running.")
                return True
            else:
                logging.error("LLM server is not responding correctly.")
                return False
        except requests.ConnectionError:
            logging.error("LLM server is not reachable.")
            return False

    def _scrape_the_article(self, article_url, drudge_title):
        logging.info(f"Scraping article: {drudge_title} - {article_url}")
        if not self.get_page(url=article_url, wait_time=3):
            return None
            
        self._click_allow(article_url)
        self.browser.set_page_load_timeout(600)
        
        try:
            html_content = self.browser.page_source
            logging.info(f"HTML content length: {len(html_content)}")
            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup(['style', 'script', 'link', 'meta', 'button', 'svg', 'img', 'iframe', 'span']):
                tag.decompose()
            clean_html = soup.prettify("utf-8")
            logging.info(f"Clean HTML content length: {len(clean_html)}")
            
            drudge_title = self._format_title(drudge_title)
            output_parser = PydanticOutputParser(pydantic_object=ArticleInfo)
            
            input_to_llm = {
                "html_content": clean_html.decode("utf-8") if isinstance(clean_html, bytes) else clean_html,
                "format_instruction": output_parser.get_format_instructions()
            }

            logging.info("Input to LLM:")
            logging.info(json.dumps(input_to_llm, ensure_ascii=False, indent=4))

            if not self._check_llm_server():
                logging.error("LLM server not available")
                return None

            try:
                logging.info("Sending data to LLM")
                response_llm = self.LLMModule.prompt_to_json(
                    input_json=input_to_llm,
                    output_parser=output_parser
                )
                if response_llm:
                    logging.info(f"LLM response received: {response_llm}")
                    logging.info(f"Full article content: {response_llm.get('content', 'No content returned')}")
                    return response_llm
                else:
                    logging.error("No response received from LLM")
            except Exception as e:
                logging.error(f"LLM API call failed: {e}")

            # Use OpenAI if LLM fails
            logging.info("Using OpenAI to generate article")
            logging.info(f"Requesting OpenAI for URL: {article_url}")
            article_content = self.openai_generator.generate_article(article_url)
            logging.info(f"Generated article content: {article_content}")
            return {"title": drudge_title, "content": article_content}
                
        except Exception as e:
            logging.error(f"Error scraping article: {e}")
            # Use OpenAI if scraping fails
            logging.info("Using OpenAI to generate article")
            logging.info(f"Requesting OpenAI for URL: {article_url}")
            article_content = self.openai_generator.generate_article(article_url)
            logging.info(f"Generated article content: {article_content}")
            return {"title": drudge_title, "content": article_content}

    def scrape_news(self):
        logging.info("Starting news scraping process")
        
        # Clear the database without deleting the table
        try:
            scan = self.drudge_news_table.scan()
            with self.drudge_news_table.batch_writer() as batch:
                for each in scan['Items']:
                    batch.delete_item(
                        Key={
                            'newsId': each['newsId']
                        }
                    )
            logging.info("Cleared the database successfully.")
        except Exception as e:
            logging.error(f"Failed to clear the database: {e}")
            return
        
        if not self._check_llm_server():
            logging.error("LLM server not available. Cannot process non-rendered articles.")
            return
            
        if not self.get_page(url=self.drudge_url, wait_time=2):
            logging.error("Failed to load Drudge Report page")
            return
            
        drudge_page_structure = []
        try:
            article_tags = WebDriverWait(self.browser, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
            
            for article_tag in article_tags:
                try:
                    drudge_title = article_tag.text
                    article_url = article_tag.get_attribute('href')
                    
                    if self._is_article(drudge_title, article_url):
                        drudge_page_structure.append([drudge_title, article_url])
                        logging.info(f"Article found: {drudge_title} - {article_url}")
                        
                except StaleElementReferenceException:
                    logging.warning("Stale element encountered, skipping")
                    continue
                except Exception as e:
                    logging.error(f"Error processing article tag: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error finding article tags: {e}")
            return
            
        current_base_unix = int(time.time())
        position_tag = len(drudge_page_structure)
        
        for drudge_tag in drudge_page_structure:
            drudge_title = drudge_tag[0]
            article_url = drudge_tag[1]
            logging.info(f"Processing article: {drudge_title} - {article_url}")
            
            if self._check_duplicate(article_url):
                entry = self._get_deplicate(article_url)
                self.update_table(
                    self.drudge_news_table,
                    ("newsId", entry["newsId"]),
                    [("newsRank", entry["newsRank"], str(current_base_unix + position_tag))]
                )
                continue
                
            item = {
                "newsId": str(hash(article_url)),
                "newsOriginalTitle": "",
                "newsDrudgeTitle": drudge_title,
                "newsUrl": article_url,
                "newsContent": "",
                "newsRank": str(current_base_unix + position_tag),
                "newsNewTitle": "",
                "isScrapeContent": False,
                "isJokesGenerated": False,
                "isRender": self._should_render(article_url),
                "newsImageURL": "",
                "createdTimeStamp": int(time.time())
            }
            
            if not item["isRender"]:
                article_info = self._scrape_the_article(article_url, drudge_title)
                if article_info:
                    item["newsOriginalTitle"] = article_info.get("title", "Unknown Title")
                    item["newsContent"] = article_info.get("content", "Content unavailable.")
                    item["isScrapeContent"] = True
                    logging.info(f"Article scraped successfully: {article_info}")
                else:
                    logging.error(f"Failed to scrape content for {article_url}")
                    
            try:
                self.drudge_news_table.put_item(Item=item)
                logging.info(f"Saved article to database: {item['newsId']}")
                logging.info(f"Article content: {item['newsContent']}")
            except Exception as e:
                logging.error(f"Failed to save article to database: {e}")
                
            position_tag = position_tag - 1
            
        logging.info("Scraped news successfully")
