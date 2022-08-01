import math

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *
from OrderSamples import OrderSamples

import pandas as pd
import numpy as np
import threading
import time
import datetime


class IBApi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        # self.posDF = pd.DataFrame(columns=['account', 'symbol', 'position', 'avg_cost', 'contract'])
        self.tickerArr = {}
        self.nextOrderId = 0
        self.orderIdArr = {}

        self.oneLowArr = {}  # low price array for 1 min
        self.oneHighArr = {}  # high price array for 1 min
        self.oneHistData = {}  # dataframe data for 1 min
        self.fiveLowArr = {}
        self.fiveHighArr = {}
        self.fiveHistData = {}
        self.fifteenHistData = {}
        self.fifteenLowArr = {}
        self.fifteenHighArr = {}
        self.sixthLowArr = {}
        self.sixthHighArr = {}
        self.sixthHistData = {}

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                            whyHeld, mktCapPrice)
        print("OrderStatus - Id:", orderId, "Status:", status, "Filled:", filled, "Remaining:", remaining)

        reqId = self.orderIdArr[orderId]
        ticker = self.tickerArr[reqId]
        if self.tickerArr[reqId]['orderStatus'] == 1:
            if status == "Cancelled":
                print(ticker['symbol'], ticker['action'], "order is Cancelled")
                self.nextOrderId = self.nextOrderId + 1
                self.placeOrder(self.nextOrderId, usTechStk(ticker['symbol']),
                                OrderSamples.MarketOrder(ticker['action'], remaining))
                print("Retry", ticker['action'], "order for", ticker['symbol'], "shares: ", remaining)
                self.orderIdArr[self.nextOrderId] = reqId
                time.sleep(3)
            elif status == "Filled" and filled > 0:
                self.tickerArr[reqId]['count'] = remaining
                if self.tickerArr[reqId]['count'] == 0:
                    print(ticker['symbol'], ticker['action'], "order is filled completely")
                    self.tickerArr[reqId]['orderStatus'] = 2

    def historicalData(self, reqId, bar):
        if reqId not in self.oneHistData:
            self.oneHistData[reqId] = [
                {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                 "volume": bar.volume}]
        else:
            self.oneHistData[reqId].append(
                {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                 "volume": bar.volume})

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.reqRealTimeBars(reqId, usTechStk(tickers[reqId]), 5, "TRADES", False, [])

    def realtimeBar(self, reqId: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqId, time_, open_, high, low, close, volume, wap, count)

        symbol = self.tickerArr[reqId]['symbol']
        orderStatus = self.tickerArr[reqId]['orderStatus']  # 0: init, 1: placed order, 2: order filled

        logFileName = symbol+'_'+self.tickerArr[reqId]['startTime']+'.csv'

        if orderStatus == 2:
            self.cancelRealTimeBars(reqId)
            return

        self.appendHistData(reqId, time_, high, low, open_, close, volume)

        if time_ % 60 == 0:
            self.reqPositions()
            time.sleep(3)               # delay for avg cost calculation

            firstTrade = self.tickerArr[reqId]['firstTrade']
            shareCount = self.tickerArr[reqId]['count']
            avgCost = self.tickerArr[reqId]['avgCost']

            rawProfit = 100 * (close - avgCost) / avgCost
            profit = abs(rawProfit)
            if 0 <= profit < 3:
                atrFactor = 10
                atrPeriod = 10
            elif 3 <= profit < 5:
                atrFactor = 7
                atrPeriod = 7
            elif 5 <= profit < 15:
                atrFactor = 5
                atrPeriod = 5
            elif 15 <= profit < 25:
                atrFactor = 3
                atrPeriod = 3
            elif 25 <= profit < 50:
                atrFactor = 2
                atrPeriod = 2
            else:
                atrFactor = initAtrFactor
                atrPeriod = initAtrPeriod
                
            # calculate and store Trail Stop values
            dfData = pd.DataFrame(self.oneHistData[reqId])
            trailDF = calcAtrTrailStop(dfData, atrPeriod, atrFactor, firstTrade)
            trailDF.to_csv(logFileName)
            trailStopVal = trailDF.tail(1)['trail'].values[0]
            print("Ticker:", symbol, "| Avg cost:", round(avgCost, 2), "| Close:", round(close, 2), "| Profit:", round(rawProfit, 1), "| Trail Stop:", round(trailStopVal, 2))
            if orderStatus == 0:
                if firstTrade == 'long' and close <= trailStopVal:
                    print("%s Sell Signal" % symbol)
                    self.tickerArr[reqId]['firstTrade'] = 'short'
                    if shareCount > 0:
                        self.tickerArr[reqId]['orderStatus'] = 1    # placed order status
                        self.tickerArr[reqId]['action'] = 'SELL'
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, usTechStk(tickers[reqId]), OrderSamples.IOC("SELL", shareCount, math.ceil(close)))
                        print("Placed SELL order for %s shares: %d " % (symbol, shareCount))
                        self.orderIdArr[self.nextOrderId] = reqId
                        time.sleep(3)
                elif firstTrade == 'short' and close >= trailStopVal:
                    print("%s Buy Signal" % symbol)
                    self.tickerArr[reqId]['firstTrade'] = 'long'
                    if shareCount > 0:
                        self.tickerArr[reqId]['orderStatus'] = 1    # placed order status
                        self.tickerArr[reqId]['action'] = 'BUY'
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, usTechStk(tickers[reqId]), OrderSamples.IOC("BUY", shareCount, math.ceil(close)))
                        print("Placed BUY order for %s shares: %d " % (symbol, shareCount))
                        self.orderIdArr[self.nextOrderId] = reqId
                        time.sleep(3)

    def appendHistData(self, reqId, time_, high, low, open_, close, volume):
        dateStamp = datetime.datetime.fromtimestamp(time_)
        if time_ % 3600 == 0:
            if len(self.sixthHighArr[reqId]) > 0:
                high_ = np.max(self.sixthHighArr[reqId])
            else:
                high_ = high
            if len(self.sixthLowArr[reqId]) > 0:
                low_ = np.min(self.sixthLowArr[reqId])
            else:
                low_ = high

            self.sixthLowArr[reqId].clear()
            self.sixthHighArr[reqId].clear()

            if reqId not in self.fiveHistData:
                self.sixthHistData[reqId] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.sixthHistData[reqId].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})
        else:
            if reqId not in self.sixthLowArr:
                self.sixthLowArr[reqId] = [low]
            else:
                self.sixthLowArr[reqId].append(low)

            if reqId not in self.sixthHighArr:
                self.sixthHighArr[reqId] = [high]
            else:
                self.sixthHighArr[reqId].append(high)

        if time_ % 900 == 0:
            if len(self.fifteenHighArr[reqId]) > 0:
                high_ = np.max(self.fifteenHighArr[reqId])
            else:
                high_ = high
            if len(self.fifteenLowArr[reqId]) > 0:
                low_ = np.min(self.fifteenLowArr[reqId])
            else:
                low_ = high

            self.fifteenLowArr[reqId].clear()
            self.fifteenHighArr[reqId].clear()

            if reqId not in self.fiveHistData:
                self.fifteenHistData[reqId] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.fifteenHistData[reqId].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})
        else:
            if reqId not in self.fifteenLowArr:
                self.fifteenLowArr[reqId] = [low]
            else:
                self.fifteenLowArr[reqId].append(low)

            if reqId not in self.fifteenHighArr:
                self.fifteenHighArr[reqId] = [high]
            else:
                self.fifteenHighArr[reqId].append(high)

        if time % 300 == 0:
            if len(self.fiveHighArr[reqId]) > 0:
                high_ = np.max(self.fiveHighArr[reqId])
            else:
                high_ = high
            if len(self.fiveLowArr[reqId]) > 0:
                low_ = np.min(self.fiveLowArr[reqId])
            else:
                low_ = high

            self.fiveLowArr[reqId].clear()
            self.fiveHighArr[reqId].clear()

            if reqId not in self.fiveHistData:
                self.fiveHistData[reqId] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.fiveHistData[reqId].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})
        else:
            if reqId not in self.fiveLowArr:
                self.fiveLowArr[reqId] = [low]
            else:
                self.fiveLowArr[reqId].append(low)

            if reqId not in self.fiveHighArr:
                self.fiveHighArr[reqId] = [high]
            else:
                self.fiveHighArr[reqId].append(high)

        if time_ % 60 == 0:
            if len(self.oneHighArr[reqId]) > 0:
                high_ = np.max(self.oneHighArr[reqId])
            else:
                high_ = high
            if len(self.oneLowArr[reqId]) > 0:
                low_ = np.min(self.oneLowArr[reqId])
            else:
                low_ = high

            self.oneLowArr[reqId].clear()
            self.oneHighArr[reqId].clear()

            if reqId not in self.oneHistData:
                self.oneHistData[reqId] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.oneHistData[reqId].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})
        else:
            if reqId not in self.oneLowArr:
                self.oneLowArr[reqId] = [low]
            else:
                self.oneLowArr[reqId].append(low)

            if reqId not in self.oneHighArr:
                self.oneHighArr[reqId] = [high]
            else:
                self.oneHighArr[reqId].append(high)

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)

        symbol = contract.symbol
        if symbol in tickers and position != 0:
            reqId = tickers.index(symbol)
            if reqId not in self.tickerArr:
                if position > 0:
                    firstTrade = 'long'
                else:
                    firstTrade = 'short'

                self.tickerArr[reqId] = {"symbol": symbol, "count": abs(position),
                                         "firstTrade": firstTrade, 'orderStatus': 0, 'action': '',
                                         'avgCost': avgCost, 'startTime': datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}
                self.reqHistoricalData(reqId=reqId, contract=usTechStk(symbol),
                                       endDateTime='', durationStr='2 D', barSizeSetting='1 min',
                                       whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])
            else:
                self.tickerArr[reqId]['avgCost'] = avgCost


# function to calculate True Range, Average True Range, Trailing stop
def calcAtrTrailStop(DF, atrPeriod, atrFactor, firstTrade):
    df = DF.copy()
    df['h-l'] = abs(df['high'] - df['low'])  # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))  # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))  # Abs of difference between Low and previous period's close
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['atr'] = df['tr'].ewm(alpha=(1 / atrPeriod), adjust=False).mean()  # Calculate WILDERS moving Average True Range calculated from previous step.

    for i in range(1, len(df)):
        loss = df.loc[i, 'atr'] * atrFactor
        if i == 1:
            df.loc[i, 'state'] = firstTrade
            if firstTrade == 'long':
                df.loc[i, 'trail'] = df.loc[i, 'close'] - loss
            if firstTrade == 'short':
                df.loc[i, 'trail'] = df.loc[i, 'close'] + loss
        else:
            pState = df.loc[i - 1, 'state']
            pTrail = df.loc[i - 1, 'trail']
            if pState == 'long':
                if df.loc[i, 'close'] > pTrail:
                    df.loc[i, 'trail'] = max(pTrail, (df.loc[i, 'close'] - loss))
                    df.loc[i, 'state'] = 'long'
                else:
                    df.loc[i, 'trail'] = df.loc[i, 'close'] + loss
                    df.loc[i, 'state'] = 'short'
            elif pState == 'short':
                if df.loc[i, 'close'] < pTrail:
                    df.loc[i, 'trail'] = min(pTrail, (df.loc[i, 'close'] + loss))
                    df.loc[i, 'state'] = 'short'
                else:
                    df.loc[i, 'trail'] = df.loc[i, 'close'] - loss
                    df.loc[i, 'state'] = 'long'
    return df


# RSI calculation
def calcRSI(DF, n=14):
    df = DF.copy()
    df['delta'] = df['Close'] - df['Close'].shift(1)
    df['gain'] = np.where(df['delta'] >= 0, df['delta'], 0)
    df['loss'] = np.where(df['delta'] < 0, abs(df['delta']), 0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean()[n])
            avg_loss.append(df['loss'].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n - 1) * avg_gain[i - 1] + gain[i]) / n)
            avg_loss.append(((n - 1) * avg_loss[i - 1] + loss[i]) / n)
    df['avg_gain'] = np.array(avg_gain)
    df['avg_loss'] = np.array(avg_loss)
    df['RS'] = df['avg_gain'] / df['avg_loss']
    df['RSI'] = 100 - (100 / (1 + df['RS']))
    return df['RSI']


# Bollinger Band calculation
def calcBollBnd(DF, n=20):
    df = DF.copy()
    df["MA"] = df['Close'].ewm(span=n, min_periods=n).mean()
    df["BB_up"] = df["MA"] + 2 * df['Close'].ewm(span=n, min_periods=n).std(ddof=0)  # ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - 2 * df['Close'].ewm(span=n, min_periods=n).std(ddof=0)  # ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)
    return df


# Volume Weighted Average Price
def calcVWAP(DF, n=5):
    df = DF.copy()
    df['Avg'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['Cum_Vol'] = df['Volume'].cumsum()
    df["Vol_Price"] = df['Volume'] * df['Avg']
    df["Vol_Price2"] = df['Volume'] * df['Avg'] * df['Avg']
    df["Cum_VP"] = df["Vol_Price"].cumsum()
    df["Cum_VP2"] = df["Vol_Price2"].cumsum()
    df["VWAP"] = df['Cum_VP'] / df['Cum_Vol']
    df["Dev"] = math.sqrt(max((df["Cum_VP2"] / df['Cum_Vol']) - (df["VWAP"] * df["VWAP"]), 0))
    df["VWAP_up1"] = df["VWAP"] + 1 * df["Dev"]
    df["VWAP_dn1"] = df["VWAP"] - 1 * df["Dev"]
    df["VWAP_up2"] = df["VWAP"] + 2 * df["Dev"]
    df["VWAP_dn2"] = df["VWAP"] - 2 * df["Dev"]
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
app.connect(host='127.0.0.1', port=7497,
            clientId=23)  # port 4002 for ib gateway paper trading / 7497 for TWS paper trading

# Taking multiple ticker symbols at a time
while True:
    tickers = input("Enter multiple ticker symbols space-separated: ").split()
    if len(tickers) > 0:
        break

while True:
    initAtrPeriod = input("Enter ATR period: ")
    if initAtrPeriod.isdigit():
        initAtrPeriod = int(initAtrPeriod)
        break

while True:
    initAtrFactor = input("Enter atr factor: ")
    if initAtrFactor.isdigit():
        initAtrFactor = int(initAtrFactor)
        break

app.reqPositions()

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
