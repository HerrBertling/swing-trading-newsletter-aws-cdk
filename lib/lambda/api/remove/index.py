from bs4 import BeautifulSoup
from datetime import datetime
import pickle
import requests
import boto3
import os
import json
import uuid


def handler(event, context):
    sqs = boto3.resource('sqs')
    queueName = os.environ['QUEUENAME']
    queue = sqs.get_queue_by_name(QueueName=queueName)

    resp = requests.get(
        'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.strip()
        security = row.findAll('td')[1].text.strip()
        sector = row.findAll('td')[3].text.strip()
        tickers.append(
            {"ticker": ticker, "security": security, "sector": sector})

    date = datetime.now()
    dateString = date.strftime("%Y-%m-%d")

    for entry in tickers:
        id = str(uuid.uuid4())
        nameString = dateString + '-' + entry["ticker"] + '-' + id
        message = {"symbol": entry["ticker"], "security": entry["security"],
                   "sector": entry["sector"], "date": dateString, "name": nameString}
        jsonMessage = json.dumps(message)

        queue.send_message(MessageBody=jsonMessage)
