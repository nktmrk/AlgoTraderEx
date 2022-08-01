import collections

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *

import pandas as pd
import numpy as np
import threading
import datetime
import plotly.graph_objects as go


class IBApi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.lowArr = []  # low price array
        self.highArr = []  # high price array
        self.histData = []  # history data

    def historicalData(self, reqID, bar):
        self.histData.append({"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                              "volume": bar.volume})

    def historicalDataEnd(self, reqID: int, start: str, end: str):
        dfData = pd.DataFrame(self.histData)
        analysisDF = calcTTMSqueeze(dfData)
        if len(analysisDF.index) > 0:
            logFileName = ticker + '_' + repr(timeFrame) + '_TTM.csv'
            analysisDF.to_csv(logFileName)

        # self.reqRealTimeBars(reqID, usTechStk(ticker), 5, "TRADES", False, [])

    def realtimeBar(self, reqID: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqID, time_, open_, high, low, close, volume, wap, count)

        dateStamp = datetime.datetime.fromtimestamp(time_)

        if (timeFrame == 1 and time_ % 60 == 0) or (timeFrame == 5 and time_ % 300 == 0) or (
                timeFrame == 15 and time_ % 900 == 0) or (timeFrame == 60 and time_ % 3600 == 0):
            if len(self.highArr) > 0:
                high_ = np.max(self.highArr)
            else:
                high_ = high
            if len(self.lowArr) > 0:
                low_ = np.min(self.lowArr)
            else:
                low_ = high

            self.lowArr.clear()
            self.highArr.clear()

            self.histData.append(
                {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                 "close": close, "volume": volume})

            print("Ticker:", ticker, "| High:", round(high, 2), "| Low:", round(low, 2), "| Open:", round(open_, 2),
                  "| Close:", round(close, 2), "| Volume:", round(volume, 2))

            dfData = pd.DataFrame(self.histData)
            analysisDF = calcTTMSqueeze(dfData)
            if len(analysisDF.index) > 0:
                logFileName = ticker + '_' + repr(timeFrame) + '_TTM.csv'
                analysisDF.to_csv(logFileName)
        else:
            self.lowArr.append(low)
            self.highArr.append(high)


def calcTTMSqueeze(DF, n=20):
    df = DF.copy()

    df['20sma'] = df['close'].rolling(window=n).mean()
    df['sDev'] = df['close'].rolling(window=n).std()
    df['LowerBandBB'] = df['20sma'] - (2 * df['sDev'])
    df['UpperBandBB'] = df['20sma'] + (2 * df['sDev'])

    df['h-l'] = abs(df['high'] - df['low'])                 # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))     # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))      # Abs of difference between Low and previous period's close
    df['TR'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['ATR_20'] = df['TR'].rolling(window=n).mean()

    df['UpperBandKCLow'] = df['20sma'] + 2.0 * df['ATR_20']
    df['LowerBandKCLow'] = df['20sma'] - 2.0 * df['ATR_20']

    df['UpperBandKCMid'] = df['20sma'] + 1.5 * df['ATR_20']
    df['LowerBandKCMid'] = df['20sma'] - 1.5 * df['ATR_20']

    df['UpperBandKCHigh'] = df['20sma'] + 1.0 * df['ATR_20']
    df['LowerBandKCHigh'] = df['20sma'] - 1.0 * df['ATR_20']

    def pre_squeeze(df):
        return df['LowerBandBB'] > df['LowerBandKCLow'] and df['UpperBandBB'] < df['UpperBandKCLow']

    def original_squeeze(df):
        return df['LowerBandBB'] > df['LowerBandKCMid'] and df['UpperBandBB'] < df['UpperBandKCMid']

    def extr_squeeze(df):
        return df['LowerBandBB'] > df['LowerBandKCHigh'] and df['UpperBandBB'] < df['UpperBandKCHigh']

    df['preSqueeze'] = df.apply(pre_squeeze, axis=1)
    df['originalSqueeze'] = df.apply(original_squeeze, axis=1)
    df['extrSqueeze'] = df.apply(extr_squeeze, axis=1)

    for i in range(1, len(df)):
        df.loc[i, 'preSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCLow'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'preSqueezeOut'] = df.loc[i, 'LowerBandKCLow'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow']

        df.loc[i, 'originalSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCMid'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'originalSqueezeOut'] = df.loc[i, 'LowerBandKCMid'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid']

        df.loc[i, 'extrSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCHigh'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCHigh'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'extrSqueezeOut'] = df.loc[i, 'LowerBandKCHigh'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCHigh']

    # momo calculation
    df['max_high'] = df['high'].rolling(window=n).max()
    df['min_low'] = df['low'].rolling(window=n).min()
    df["MA_20"] = df["close"].ewm(span=n, min_periods=n).mean()
    df['K'] = (df['max_high'] + df['min_low']) / 2 + df["MA_20"]
    df['x'] = df.index
    df['y'] = df["close"] - df['K'] / 2
    df['x2'] = df['x'] * df['x']
    df['xy'] = df['x'] * df['y']

    a = (n * df['xy'].rolling(n).sum() - df['x'].rolling(n).sum() * df['y'].rolling(n).sum()) / (
                n * df['x2'].rolling(n).sum() - df['x'].rolling(n).sum() * df['x'].rolling(n).sum())
    b = (df['x2'].rolling(n).sum() * df['y'].rolling(n).sum() - df['x'].rolling(n).sum() * df['xy'].rolling(
        n).sum()) / (n * df['x2'].rolling(n).sum() - df['x'].rolling(n).sum() * df['x'].rolling(n).sum())

    df['momo'] = 100 * (a * df["x"] + b)

    df['pos'] = df['momo'] >= 0
    df['neg'] = df['momo'] < 0
    df['up'] = df['momo'] >= df['momo'].shift(1)
    df['dn'] = df['momo'] < df['momo'].shift(1)

    df.dropna(inplace=True)
    return df


def usTechStk(symbol, sec_type="STK", currency="USD", exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def websocket_con():
    app.run()


print("Welcome to Algorithms Trading")
print("")

app = IBApi()
app.connect(host='127.0.0.1', port=4002,
            clientId=23)  # port 4002 for ib gateway paper trading / 7497 for TWS paper trading

while True:
    ticker = input("Enter ticker symbol: ")
    if len(ticker) > 0:
        break

while True:
    timeFrameOptions = collections.OrderedDict()
    timeFrameOptions["1"] = "1 min"
    timeFrameOptions["2"] = "5 mins"
    timeFrameOptions["3"] = "15 mins"
    timeFrameOptions["4"] = "1 hour"
    options = timeFrameOptions.keys()
    for entry in options:
        print(entry + ")\t" + timeFrameOptions[entry])
    timeFrameSelection = input("Select timeframe: ")
    if timeFrameSelection == "1":
        timeFrame = 1
        print("")
        break
    elif timeFrameSelection == "2":
        timeFrame = 5
        print("")
        break
    elif timeFrameSelection == "3":
        timeFrame = 15
        print("")
        break
    elif timeFrameSelection == "4":
        timeFrame = 60
        print("")
        break

app.reqHistoricalData(reqId=0, contract=usTechStk(ticker), endDateTime='', durationStr='1 D',
                      barSizeSetting=timeFrameOptions[timeFrameSelection], whatToShow='TRADES', useRTH=0, formatDate=1,
                      keepUpToDate=1, chartOptions=[])

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
