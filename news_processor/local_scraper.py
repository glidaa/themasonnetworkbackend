from scraper import NewsScraper
import boto3

class LocalNewsScraper(NewsScraper):
    def __init__(self) -> None:
        super().__init__()
        # Override DynamoDB client to use local instance
        self.dynamodb_client = boto3.resource('dynamodb',
                                            endpoint_url='http://localhost:8000',
                                            region_name='local',
                                            aws_access_key_id='dummy',
                                            aws_secret_access_key='dummy')
        self.drudge_news_table = self.dynamodb_client.Table('themasonnetwork_drudgescrape')
        self.visited_site = {}

if __name__ == "__main__":
    print("Starting local news scraper...")
    scraper = LocalNewsScraper()
    scraper.scrape_news()
    print("Scraping complete!")
