FROM umihico/aws-lambda-selenium-python:latest
COPY ./requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY scrape_news.py ./

CMD [ "scrape_news.scrape_news" ] 