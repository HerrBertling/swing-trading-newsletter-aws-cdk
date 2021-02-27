import yfinance as yf
from ta.trend import MACD, EMAIndicator
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
import os
import uuid


def handler(event, context):
    # DynamoDb
    dynamodb = boto3.resource('dynamodb')
    tableName = os.environ['DATABASE']
    table = dynamodb.Table(tableName)

    # Get stock data
    stock = yf.Ticker(event['symbol'])

    if(event['date']):
        endDate = datetime.strptime(event['date'], "%Y-%m-%d")
    else:
        endDate = datetime.utcnow()

    startDate = endDate - timedelta(weeks=260)
    stock_data = stock.history(end=endDate, start=startDate, interval="5d")

    # Calculate impulse system
    macd_hist = MACD(stock_data["Close"], fillna=True).macd_diff()
    ema = EMAIndicator(stock_data["Close"], n=13, fillna=True).ema_indicator()
    shouldBeGreen = ema.iloc[-1] > ema.iloc[-2] and macd_hist.iloc[-1] > macd_hist.iloc[-2]
    shouldBeRed = ema.iloc[-1] < ema.iloc[-2] and macd_hist.iloc[-1] < macd_hist.iloc[-2]
    color = 'green' if shouldBeGreen else 'red' if shouldBeRed else 'blue'

    dateString = endDate.strftime("%Y-%m-%d")

    id = str(uuid.uuid4())

    entry = {
        'symbol': event['symbol'],
        'security': event['security'],
        'sector': event['sector'],
        'id': id,
        'date': dateString,
        'weekly': {
            'type': 'impulse_system',
            'result': color,
        }
    }

    table.put_item(Item=entry)

    return entry
