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
        analysisDF = calcTopBreakOut(dfData)
        if len(analysisDF.index) > 0:
            logFileName = ticker + '_' + repr(timeFrame) + '_TopBreakOut.csv'
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
            analysisDF = calcTopBreakOut(dfData)
            if len(analysisDF.index) > 0:
                logFileName = ticker + '_' + repr(timeFrame) + '_TopBreakOut.csv'
                analysisDF.to_csv(logFileName)
        else:
            self.lowArr.append(low)
            self.highArr.append(high)


def calcTopBreakOut(DF):
    df = DF.copy()

    df['HH'] = df['high'].rolling(window=sellExit).max()
    df['LL'] = df['low'].rolling(window=buyExit).min()

    df['QB'] = df['high'].rolling(window=buyEntry).max()
    df['QS'] = df['low'].rolling(window=sellEntry).min()

    # ATR calculation
    df['h-l'] = abs(df['high'] - df['low'])  # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))  # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))  # Abs of difference between Low and previous period's close
    df['TR'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['ATR'] = df['TR'].ewm(alpha=(1 / atrLength), adjust=False).mean()
    df['mATR'] = df['ATR'].rolling(window=atrLength).max()
    df['co'] = df.index > max(sellExit, buyExit)

    df.loc[1, 'pos'] = 0
    df.loc[1, 'EntryPr'] = np.NaN
    df.loc[1, 'BTarget'] = np.NaN
    df.loc[1, 'BTarget2'] = np.NaN
    for i in range(2, len(df)):
        if buyOrSell == 'buy':
            df.loc[i, 'Entry'] = df.loc[i - 1, 'QB']
            df.loc[i, 'Exit'] = df.loc[i - 1, 'LL']

            if df.loc[i, 'co'] and df.loc[i, 'high'] > df.loc[i - 1, 'QB']:
                df.loc[i, 'pos'] = 1
            elif df.loc[i, 'low'] < df.loc[i - 1, 'LL']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i - 1, 'pos']

            if df.loc[i, 'high'] > df.loc[i - 1, 'QB'] and df.loc[i, 'pos'] == 1 and df.loc[i - 1, 'pos'] < 1:
                df.loc[i, 'EntryPr'] = df.loc[i - 1, 'QB']
            elif df.loc[i, 'pos'] == 0:
                df.loc[i, 'EntryPr'] = np.NaN
            else:
                df.loc[i, 'EntryPr'] = df.loc[i - 1, 'EntryPr']

            if df.loc[i, 'pos'] == 1 and df.loc[i - 1, 'pos'] < 1:
                df.loc[i, 'BTarget'] = df.loc[i, 'EntryPr'] + targetATRMulti * 2 * df.loc[i, 'mATR']
                df.loc[i, 'BTarget2'] = df.loc[i, 'EntryPr'] + 2 * targetATRMulti * 2 * df.loc[i, 'mATR']
            elif df.loc[i, 'pos'] == 1:
                df.loc[i, 'BTarget'] = df.loc[i - 1, 'BTarget']
                df.loc[i, 'BTarget2'] = df.loc[i - 1, 'BTarget2']
            else:
                df.loc[i, 'BTarget'] = np.NaN
                df.loc[i, 'BTarget2'] = np.NaN

            if (i > buyExit) and df.loc[i, 'EntryPr'] != np.NaN and (df.loc[i, 'LL'] < df.loc[i, 'EntryPr']):
                df.loc[i, 'EntryLine'] = df.loc[i, 'EntryPr']
            else:
                df.loc[i, 'EntryLine'] = np.NaN

            if i > buyExit and df.loc[i, 'EntryPr'] != np.NaN:
                df.loc[i, 'TradeRisk'] = (df.loc[i, 'EntryPr'] - df.loc[i, 'LL']) / df.loc[i, 'mATR']
        elif buyOrSell == 'sell':
            df.loc[i, 'Entry'] = df.loc[i - 1, 'QS']
            df.loc[i, 'Exit'] = df.loc[i - 1, 'HH']

            if df.loc[i - 1, 'QS'] != np.NaN and df.loc[i, 'co'] and df.loc[i, 'low'] < df.loc[i - 1, 'QS']:
                df.loc[i, 'pos'] = -1
            elif df.loc[i - 1, 'high'] > df.loc[i - 2, 'HH']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i - 1, 'pos']

            if df.loc[i, 'low'] > df.loc[i - 1, 'QS'] and df.loc[i, 'pos'] == -1 and df.loc[i - 1, 'pos'] > -1:
                df.loc[i, 'EntryPr'] = df.loc[i - 1, 'QS']
            elif df.loc[i, 'pos'] == 0:
                df.loc[i, 'EntryPr'] = np.NaN
            else:
                df.loc[i, 'EntryPr'] = df.loc[i - 1, 'EntryPr']

            if df.loc[i, 'pos'] == -1 and df.loc[i - 1, 'pos'] > -1:
                df.loc[i, 'BTarget'] = df.loc[i, 'EntryPr'] - targetATRMulti * 2 * df.loc[i, 'mATR']
                df.loc[i, 'BTarget2'] = df.loc[i, 'EntryPr'] - 2 * targetATRMulti * 2 * df.loc[i, 'mATR']
            elif df.loc[i, 'pos'] == -1:
                df.loc[i, 'BTarget'] = df.loc[i - 1, 'BTarget']
                df.loc[i, 'BTarget2'] = df.loc[i - 1, 'BTarget2']
            else:
                df.loc[i, 'BTarget'] = np.NaN
                df.loc[i, 'BTarget2'] = np.NaN

            if i > sellExit and df.loc[i, 'EntryPr'] != np.NaN and df.loc[i, 'HH'] > df.loc[i, 'EntryPr']:
                df.loc[i, 'EntryLine'] = df.loc[i, 'EntryPr']
            else:
                df.loc[i, 'EntryLine'] = np.NaN

            if df.loc[i, 'HH'] != np.NaN and df.loc[i, 'EntryPr'] != np.NaN:
                df.loc[i, 'TradeRisk'] = (df.loc[i, 'HH'] - df.loc[i, 'EntryPr']) / df.loc[i, 'mATR']

    for i in range(2, len(df)):
        if df.loc[i, 'co']:
            df.loc[i, 'pBTarget'] = df.loc[i, 'BTarget']
            df.loc[i, 'pBTarget2'] = df.loc[i, 'BTarget2']
            df.loc[i, 'pEntryLine'] = df.loc[i, 'EntryLine']
        else:
            df.loc[i, 'pBTarget'] = np.NaN
            df.loc[i, 'pBTarget2'] = np.NaN
            df.loc[i, 'pEntryLine'] = np.NaN

    candlestick = go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])
    if buyOrSell == 'buy':
        entryL = go.Scatter(x=df['date'], y=df['Entry'], name='Entry', line={'color': 'green'})
    else:
        entryL = go.Scatter(x=df['date'], y=df['Entry'], name='Entry', line={'color': 'red'})
    exitLine = go.Scatter(x=df['date'], y=df['Exit'], name='Exit Line', line={'color': 'cyan'})
    entryLine = go.Scatter(x=df['date'], y=df['pEntryLine'], name='Entry Line', line={'color': 'white'})
    bTargetLine = go.Scatter(x=df['date'], y=df['BTarget'], name='BTarget Line', line={'color': 'yellow'})
    bTarget2Line = go.Scatter(x=df['date'], y=df['BTarget2'], name='BTarget2 Line', line={'color': 'magenta'})

    fig = go.Figure(data=[candlestick, entryL, exitLine, entryLine, bTargetLine, bTarget2Line])
    fig.layout.xaxis.rangeslider.visible = False

    for i in range(1, len(df)):
        valco = df.loc[i, 'co'] and (df.loc[i, 'pos'] == 1 or df.loc[i, 'pos'] == -1) and df.loc[i - 1, 'pos'] == 0
        if valco:
            if df.loc[i, 'BTarget'] != np.NaN:
                fig.add_annotation(x=df.loc[i, 'date'], y=df.loc[i, 'BTarget'], text=round(df.loc[i, 'BTarget'], 2),
                                   showarrow=False, bgcolor='yellow')
            # if df.loc[i, 'BTarget2'] != np.NaN:
            #    fig.add_annotation(x=df.loc[i, 'date'], y=df.loc[i, 'BTarget2'], text=round(df.loc[i, 'BTarget2'], 2),
            #                       showarrow=False, bgcolor='magenta')
            if df.loc[i, 'EntryPr'] != np.NaN:
                fig.add_annotation(x=df.loc[i, 'date'], y=df.loc[i, 'EntryPr'], text=round(df.loc[i, 'EntryPr'], 2),
                                   showarrow=False, bgcolor='white')
            if buyOrSell == 'buy':
                if df.loc[i, 'LL'] != np.NaN:
                    fig.add_annotation(x=df.loc[i, 'date'], y=df.loc[i, 'LL'], text=round(df.loc[i, 'LL'], 2),
                                       showarrow=False, bgcolor='cyan')
            else:
                if df.loc[i, 'HH'] != np.NaN:
                    fig.add_annotation(x=df.loc[i, 'date'], y=df.loc[i, 'HH'], text=round(df.loc[i, 'HH'], 2),
                                       showarrow=False, bgcolor='cyan')
    fig.show()

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

while True:
    actionOptions = collections.OrderedDict()
    actionOptions["1"] = "Buy"
    actionOptions["2"] = "Sell"
    options = actionOptions.keys()
    for entry in options:
        print(entry + ")\t" + actionOptions[entry])
    actionSelection = input("Select what would you like do today: ")
    if actionSelection == "1":
        buyOrSell = 'buy'
        print("You have selected ", actionOptions[actionSelection])
        print("")
        break
    elif actionSelection == "2":
        buyOrSell = 'sell'
        print("You have selected ", actionOptions[actionSelection])
        print("")
        break

while True:
    buyEntry = input("Enter buy entry: ")
    if buyEntry.isdigit():
        buyEntry = int(buyEntry)
        break

while True:
    sellEntry = input("Enter sell entry: ")
    if sellEntry.isdigit():
        sellEntry = int(sellEntry)
        break

while True:
    buyExit = input("Enter buy exit: ")
    if buyExit.isdigit():
        buyExit = int(buyExit)
        break

while True:
    sellExit = input("Enter sell exit: ")
    if sellExit.isdigit():
        sellExit = int(sellExit)
        break

while True:
    atrLength = input("Enter atr length: ")
    if atrLength.isdigit():
        atrLength = int(atrLength)
        break

while True:
    targetATRMulti = input("Enter target atr multi: ")
    if targetATRMulti.isdigit():
        targetATRMulti = int(targetATRMulti)
        break

app.reqHistoricalData(reqId=0, contract=usTechStk(ticker), endDateTime='', durationStr='1 D',
                      barSizeSetting=timeFrameOptions[timeFrameSelection], whatToShow='TRADES', useRTH=0, formatDate=1,
                      keepUpToDate=1, chartOptions=[])

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
