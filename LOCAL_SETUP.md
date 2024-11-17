# Local Development Setup for News Scraper

This guide explains how to set up and run the news scraper locally for testing purposes.

## Prerequisites

1. Docker Desktop installed
2. Python 3.x installed
3. Required Python packages:
   ```
   pip install boto3 selenium beautifulsoup4
   ```

## Setup Steps

1. Start the local DynamoDB:
   ```
   docker-compose up -d
   ```

2. Create the required tables:
   ```
   python setup_local_db.py
   ```

3. Run the local scraper:
   ```
   python news_processor/local_scraper.py
   ```

4. Check the scraped data:
   ```
   python setup_local_db.py
   ```

## Database Tables Structure

### 1. themasonnetwork_drudgescrape
News articles table storing scraped content.
Fields:
- newsId (String, Primary Key)
- newsDrudgeTitle (String)
- newsUrl (String)
- newsContent (String)
- timestamp (String)

### 2. themasonnetwork_jokes
Jokes storage table.
Fields:
- jokeId (String, Primary Key)
- jokeContent (String)
- timestamp (String)

### 3. themasonnetwork_subscribers
Email subscribers table.
Fields:
- subscriber_id (String, Primary Key)
- user_email (String)

## How it Works

- The local setup uses DynamoDB Local running in a Docker container
- Data is stored locally and persists between runs
- The scraper uses the same logic as production but writes to local DynamoDB
- You can check the scraped data using setup_local_db.py

## Stopping the Local Environment

To stop the local DynamoDB:
```
docker-compose down
