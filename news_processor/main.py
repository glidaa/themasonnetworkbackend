from scraper import (
    NewsScraper
)
from jokers import Joker


if __name__ == "__main__":
    news_scraper = NewsScraper()
    news_scraper.scrape_news()
    
    the_joker = Joker()
    the_joker.make_jokes()
