import csv
import pandas as pd

from binance.client import Client
from datetime import datetime

API_KEY = 'Bxvd9MTLCNxp01d6hJ7nLEGhtNDDSSJNl7io7X4RwahNXJH87JfJKYWrfB0WarsV'
API_SECRET = 'JoDTNnajREzxntRNuB4STqyfQPRuNAu9kEmTS0Ifunw1K35gexbebUATdfovFKSs'

client = Client(API_KEY, API_SECRET)

histDF = pd.DataFrame(columns=['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'NumberOfTrades'])
# csvFile = open('2021_15minutes.csv', 'w', newline='')
# candlestick_writer = csv.writer(csvFile, delimiter=',')

candlesticks = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, "26 Apr, 2021", datetime.now())
# candlesticks = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, "1 Jan, 2020", "12 Jul, 2020")

for candlestick in candlesticks:
    openTimeStamp = datetime.fromtimestamp(candlestick[0]/1000).strftime("%Y%m%d %H:%M:%S")
    closeTimeStamp = datetime.fromtimestamp(candlestick[6]/1000).strftime("%Y%m%d %H:%M:%S")
    dict = {"Open_Time": openTimeStamp, "Open": candlestick[1], "High": candlestick[2], "Low": candlestick[3],
            "Close": candlestick[4], "Volume": candlestick[5], 'Close_Time': closeTimeStamp, 'NumberOfTrades': candlestick[8]}
    histDF.append(dict, ignore_index=True)

print('histDF: ', histDF)

histDF.to_csv('2021_15minutes.csv')
# csvFile.close()
