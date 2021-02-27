from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import json
import uuid


def getNextDates(start, days=1):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    dates = []
    next_date = start_date + timedelta(days)
    weekdays = [5, 6]
    while len(dates) <= days:
        if next_date.weekday() not in weekdays:
            dates.append(next_date.strftime("%Y-%m-%d"))
            next_date = next_date + timedelta(days)
    return dates


def handler(event, context):
    # setup sqs queue
    sqs = boto3.resource('sqs')
    queueName = os.environ['QUEUENAME']
    queue = sqs.get_queue_by_name(QueueName=queueName)

    # collect data from dynamodb
    dynamodb = boto3.resource('dynamodb')
    tableName = os.environ['DATABASE']
    table = dynamodb.Table(tableName)

    scan_kwargs = {
        'FilterExpression': Attr('entry').exists(),
    }
    done = False
    start_key = None
    items = []

    # get all items with an entry record
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        validEntries = table.scan(**scan_kwargs)
        foundItems = validEntries['Items']
        items.extend(foundItems)
        start_key = validEntries.get('LastEvaluatedKey', None)
        done = start_key is None

    resultCount = len(items)

    print(resultCount)

    id = str(uuid.uuid4())

    for item in items:
        nameString = item['symbol'] + '-' + item['date'] + id
        message = {**item, "name": nameString}
        jsonMessage = json.dumps(message)

        queue.send_message(MessageBody=jsonMessage)
