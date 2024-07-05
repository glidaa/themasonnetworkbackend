from scraper import (
    NewsScraper,
    ContentScraper
)
from jokers import Joker


if __name__ == "__main__":
    # news_scraper = NewsScraper()
    # news_scraper.scrape_news()

    content_scraper = ContentScraper()
    content_scraper.format_articles()
    
    # the_joker = Joker()
    # the_joker.make_jokes()
