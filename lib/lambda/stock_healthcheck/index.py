import yfinance as yf
from datetime import datetime, timedelta


def handler(event, context):
    # Get stock data
    stock = yf.Ticker(event['symbol'])

    if(event['date']):
        endDate = datetime.strptime(event['date'], "%Y-%m-%d")
    else:
        endDate = datetime.utcnow()

    startDate = endDate - timedelta(days=5)
    stock_data = stock.history(end=endDate, start=startDate, interval="1d")

    # Check average volume of last 5 days
    average = stock_data['Volume'].sum(
    ) / len(stock_data.index)

    isVolumeAboveAMillion = average > 1000000

    shouldProceed = 'true' if isVolumeAboveAMillion else 'false'

    healthCheck = {
        'shouldProceed': shouldProceed
    }

    return healthCheck
