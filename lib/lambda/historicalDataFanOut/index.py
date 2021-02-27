from datetime import datetime, timedelta
import boto3
import os
import json
import uuid


def handler(event, context):
    sqs = boto3.resource('sqs')
    queueName = os.environ['QUEUENAME']
    queue = sqs.get_queue_by_name(QueueName=queueName)

    symbols = ['AAPL', 'NFLX', 'GOOG', 'AMZN', 'MSFT', 'KO', 'ABBV', 'NVDA', 'MMM',
               'KHC', 'UAA', 'FB', 'GM', 'MOS', 'BLK', 'V', 'FLS', 'AMT', 'CCL', 'GILD', 'BBY', 'EMN', 'NKE', 'LMT', 'VZ', 'MCD', 'HON', 'CAT', 'KMB', 'TSN', 'NRG']

    def daterange(date1, date2):
        for n in range(int((date2 - date1).days)+1):
            yield date1 + timedelta(n)

    start_date = datetime.strptime(event['date'], "%Y-%m-%d")
    end_date = start_date + timedelta(days=event['daysToProcess'])

    allWeekdays = []

    weekdays = [5, 6]
    for dt in daterange(start_date, end_date):
        if dt.weekday() not in weekdays:
            allWeekdays.append(dt.strftime("%Y-%m-%d"))

    id = str(uuid.uuid4())
    for symbol in symbols:
        for weekday in allWeekdays:
            nameString = weekday + '-' + symbol + '-' + id
            message = {"symbol": symbol, "date": weekday, "name": nameString}
            jsonMessage = json.dumps(message)

            queue.send_message(MessageBody=jsonMessage)
