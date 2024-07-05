import pandas as pd
import numpy as np
from decimal import Decimal
import boto3

df = pd.read_csv("unique_drudge_urls_scrape.csv", sep=';')
dynamodb = boto3.resource('dynamodb')
news_table = dynamodb.Table('themasonnetwork_drudgescrape')


for index, row in df.iterrows():
    createdTimeStamp = 0
    if row['createdTimeStamp'] is not np.NAN:
        createdTimeStamp = row['createdTimeStamp']

    news_table.put_item(Item={
        'createdTimeStamp': Decimal(createdTimeStamp),
        'newsUrl': row['newsUrl'],
        'newsContent': '',
        'newsOriginalTitle': '',
        'newsRank': str(row['newsRank']),
        'isScrapeContent': row['isScrapeContent'],
        'isJokesGenerated': row['isJokesGenerated'],
        'newsImageURL': '',
        'newsNewTitle': '',
        'isRender': row['isRender'],
        'newsId': str(row['newsId']),
        'newsDrudgeTitle': row['newsDrudgeTitle']
    })
