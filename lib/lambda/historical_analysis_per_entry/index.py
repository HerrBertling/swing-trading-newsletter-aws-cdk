from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import json


def getNextDates(start, requestedDays=1):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    dates = []
    next_date = start_date + timedelta(days=1)
    excludedWeekdays = [5, 6]
    while len(dates) <= requestedDays:
        if next_date.weekday() not in excludedWeekdays:
            dates.append(next_date.strftime("%Y-%m-%d"))
            next_date = next_date + timedelta(days=1)
    return dates


def handler(event, context):
    # collect data from dynamodb
    dynamodb = boto3.resource('dynamodb')
    tableName = os.environ['DATABASE']
    table = dynamodb.Table(tableName)

    for record in event['Records']:
        message = json.loads(record["body"])

        nextDays = getNextDates(message['date'], 5)
        symbol = message['symbol']

        print(nextDays)

        entries = []

        for date in nextDays:
            entry = table.get_item(Key={'symbol': symbol, 'date': date})
            entries.append(entry)

        print(entries)
        # priceWasMatched = nextEntry['low'] < entryPrice and entryPrice < nextEntry['high']
        # if priceWasMatched:
        #     itemsWithPriceMatch.extend(item)

    # print(itemsWithPriceMatch)

    # from THAT set, check whether prices went up by… 20%? within the next week or so
