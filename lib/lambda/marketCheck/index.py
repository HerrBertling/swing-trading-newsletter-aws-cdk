import yfinance as yf
from ta.trend import MACD, EMAIndicator
from ta.volume import ForceIndexIndicator
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
    stock = yf.Ticker('^GSPC')
    stock_data_weekly = stock.history(period="5y", interval="5d")
    stock_data_daily = stock.history(period="2y", interval="1d")

    # Calculate impulse system weekly
    macd_hist = MACD(stock_data_weekly["Close"], fillna=True).macd_diff()
    ema = EMAIndicator(
        stock_data_weekly["Close"], n=13, fillna=True).ema_indicator()
    shouldBeGreen = ema.iloc[-1] > ema.iloc[-2] and macd_hist.iloc[-1] > macd_hist.iloc[-2]
    shouldBeRed = ema.iloc[-1] < ema.iloc[-2] and macd_hist.iloc[-1] < macd_hist.iloc[-2]
    colorWeekly = 'green' if shouldBeGreen else 'red' if shouldBeRed else 'blue'

    # Calculate impulse system daily
    macd_hist = MACD(stock_data_daily["Close"], fillna=True).macd_diff()
    ema = EMAIndicator(
        stock_data_daily["Close"], n=13, fillna=True).ema_indicator()
    shouldBeGreen = ema.iloc[-1] > ema.iloc[-2] and macd_hist.iloc[-1] > macd_hist.iloc[-2]
    shouldBeRed = ema.iloc[-1] < ema.iloc[-2] and macd_hist.iloc[-1] < macd_hist.iloc[-2]
    colorDaily = 'green' if shouldBeGreen else 'red' if shouldBeRed else 'blue'

    # Caculate ForceIndex 13 days
    indicator_fi = ForceIndexIndicator(
        stock_data_daily["Close"], stock_data_daily["Volume"], 13, fillna=True).force_index()

    lastForceIndexValue = indicator_fi.iloc[-1]

    lastFIDecimal = Decimal(lastForceIndexValue)

    lastFI = round(lastFIDecimal, 0)

    lastCloseData = stock_data_daily.iloc[-1]["Close"]

    lastCloseDecimal = Decimal(lastCloseData)
    lastClose = round(lastCloseDecimal, 2)

    # daily timestamp
    date = datetime.utcnow()
    future = date + timedelta(days=14)
    expiryDate = round(future.timestamp() * 1000)
    dateString = date.strftime("%Y-%m-%d")

    id = str(uuid.uuid4())

    entry = {
        'symbol': '^GSPC',
        'id': id,
        'date': dateString,
        'ttl': expiryDate,
        'weeklyImpulse': colorWeekly,
        'dailyImpulse': colorDaily,
        'forceIndex13': lastFI,
        'lastClose': lastClose,
    }

    table.put_item(Item=entry)

    return entry
