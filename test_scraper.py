import logging
from news_processor.scraper import NewsScraper
from news_processor.jokers import Joker
from news_processor.LLMs import LLMModule

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def test_llm_module():
    try:
        llm = LLMModule()
        logging.info("LLMModule initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize LLMModule: {e}")

def test_news_scraper():
    try:
        scraper = NewsScraper()
        logging.info("NewsScraper initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize NewsScraper: {e}")

def test_joker():
    try:
        joker = Joker()
        logging.info("Joker initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Joker: {e}")

if __name__ == "__main__":
    logging.info("Starting tests...")
    test_llm_module()
    test_news_scraper()
    test_joker()
    logging.info("Tests completed.")
