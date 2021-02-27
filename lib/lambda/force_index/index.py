import yfinance as yf
from ta.volume import ForceIndexIndicator
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

    startDate = endDate - timedelta(weeks=156)
    stock_data = stock.history(end=endDate, start=startDate, interval="1d")

    # Get Force Index result
    indicator_fi = ForceIndexIndicator(
        stock_data["Close"], stock_data["Volume"], 2, fillna=True).force_index()
    shouldGoLong = indicator_fi.iloc[-1] < 0 and indicator_fi.iloc[-2] > 0

    dailyData = stock_data.iloc[-1]

    openValue = dailyData["Open"]
    openPrice = Decimal(openValue)
    roundedOpenPrice = round(openPrice, 2)
    highValue = dailyData["High"]
    highPrice = Decimal(highValue)
    roundedHighPrice = round(highPrice, 2)

    lowValue = dailyData["Low"]
    lowPrice = Decimal(lowValue)
    roundedLowPrice = round(lowPrice, 2)

    closeValue = dailyData["Close"]
    closePrice = Decimal(closeValue)
    roundedClosePrice = round(closePrice, 2)

    volumeValue = dailyData["Volume"]
    volumePrice = Decimal(volumeValue)
    roundedVolumePrice = round(volumePrice, 2)

    dailyEntry = {
        'type': 'force_index',
        'result': 'long' if shouldGoLong else 'short',
        'open': roundedOpenPrice,
        'high': roundedHighPrice,
        'low': roundedLowPrice,
        'close': roundedClosePrice,
        'volume': roundedVolumePrice
    }

    # Write to database
    table.update_item(
        Key={
            'symbol': event['symbol'],
            'date': event['date']
        },
        UpdateExpression='SET daily = :dailyEntry',
        ExpressionAttributeValues={
            ':dailyEntry': dailyEntry
        }
    )

    # Return for next step in step functions
    return dailyEntry
