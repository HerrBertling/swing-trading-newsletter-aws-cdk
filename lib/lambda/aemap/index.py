import yfinance as yf
from ta.trend import EMAIndicator
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
import os


def handler(event, context):

    # Setup dynamodb table
    dynamodb = boto3.resource('dynamodb')
    tableName = os.environ['DATABASE']
    table = dynamodb.Table(tableName)

    # Get stock data
    stock = yf.Ticker(event['symbol'])
    if(event['date']):
        endDate = datetime.strptime(event['date'], "%Y-%m-%d")
    else:
        endDate = datetime.utcnow()

    startDate = endDate - timedelta(weeks=104)
    stock_data = stock.history(end=endDate, start=startDate, interval="1d")

    # Calculate AEMAp
    stock_data['EMA'] = EMAIndicator(
        stock_data["Close"], n=13, fillna=True).ema_indicator()
    stock_data['diff'] = stock_data["EMA"] - stock_data["Low"]
    lastEntries = stock_data.tail(20)
    negativeDiffEntries = lastEntries[lastEntries['diff'] < 0]
    numberOfEntries = max(1, len(negativeDiffEntries.index))
    average = negativeDiffEntries['diff'].sum(
    ) / numberOfEntries

    lastPrice = stock_data.iloc[-1]["Close"]
    entryPrice = Decimal(lastPrice + average)
    roundedEntryPrice = round(entryPrice, 2)
    lastPriceDecimal = Decimal(lastPrice)
    roundedLastPrice = round(lastPriceDecimal, 2)

    entryValue = {
        'type': 'aemap',
        'result': roundedEntryPrice,
        'close': roundedLastPrice,
    }

    # Write to database
    table.update_item(
        Key={
            'symbol': event['symbol'],
            'date': event['date']
        },
        UpdateExpression='SET entry = :entryValue',
        ExpressionAttributeValues={
            ':entryValue': entryValue
        }
    )

    return entryValue
