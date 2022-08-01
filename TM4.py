import collections
import pandas as pd
import numpy as np
import math
import datetime

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from ibapi.common import *
from OrderSamples import OrderSamples


class IBPy(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.lowArr = {}                # low price array
        self.highArr = {}               # high price array
        self.histData = {}              # history data
        self.nextOrderId = 0
        self.orderIdArr = {}
        self.tickerArr = {}
        self.orderDF = pd.DataFrame(columns=['Symbol', 'Action', 'Order', 'Position', 'Time'])
        self.lastClose = 0

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def historicalData(self, reqID, bar):
        if bar.date == yesterdayCloseTime:
            self.tickerArr[reqID]['yesterdayLastClose'] = bar.close
        if reqID not in self.histData:
            self.histData[reqID] = [
                {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                 "Volume": bar.volume}]
        else:
            self.histData[reqID].append(
                {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                 "Volume": bar.volume})

    def historicalDataEnd(self, reqID: int, start: str, end: str):
        self.reqRealTimeBars(reqID, usTechStk(tickers[reqID]), 5, "TRADES", False, [])

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                            whyHeld, mktCapPrice)
        # print("OrderStatus - Id:", orderId, "Status:", status, "Filled:", filled, "Remaining:", remaining)

        if orderId in self.orderIdArr:
            reqID = self.orderIdArr[orderId]
            tickerObj = self.tickerArr[reqID]
            if tickerObj['orderPlaced']:
                if status == "Cancelled":
                    print(tickerObj['symbol'], tickerObj['lastAction'], 'order is cancelled')
                    self.nextOrderId = self.nextOrderId + 1
                    if tickerObj['lastAction'] == 'buy' or tickerObj['lastAction'] == 'sell':
                        self.placeOrder(self.nextOrderId, usTechStk(tickerObj['symbol']),
                                        OrderSamples.IOC(tickerObj['lastAction'], remaining, math.ceil(self.lastClose)))
                    elif tickerObj['lastAction'] == 'cover':
                        self.placeOrder(self.nextOrderId, usTechStk(tickerObj['symbol']),
                                        OrderSamples.IOC("BUY", remaining, math.ceil(self.lastClose)))
                    elif tickerObj['lastAction'] == 'close':
                        self.placeOrder(self.nextOrderId, usTechStk(tickerObj['symbol']),
                                        OrderSamples.IOC("SELL", remaining, math.floor(self.lastClose)))
                    print("Retry", tickerObj['lastAction'], "order for", tickerObj['symbol'], "shares: ", remaining)
                    self.orderIdArr[self.nextOrderId] = reqID
                elif status == "Filled" and filled > 0:
                    if remaining == 0:
                        print(tickerObj['symbol'], tickerObj['lastAction'], 'order is filled completely')
                        self.tickerArr[reqID]['orderPlaced'] = False

                        dictionary = {'Symbol': tickerObj['symbol'], 'Action': tickerObj['lastAction'],
                                      'Order': tickerObj['orderCount'], 'Position': self.tickerArr[reqID]['position'],
                                      'Time': datetime.datetime.now().strftime('%Y%m%d  %H:%M:%S'),
                                      'Avg Price': avgFillPrice, 'strategy': strategySelection}
                        self.orderDF = self.orderDF.append(dictionary, ignore_index=True)
                        self.orderDF.set_index("Time", inplace=True)
                        logFileName = 'orders_' + self.tickerArr[reqID]['startTime'] + '.csv'
                        self.orderDF.to_csv(logFileName)

    def realtimeBar(self, reqID: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqID, time_, open_, high, low, close, volume, wap, count)

        self.appendRealData(reqID, time_, high, low, open_, close, volume)

    def appendRealData(self, reqID, time_, high, low, open_, close, volume):
        dateStamp = datetime.datetime.fromtimestamp(time_)
        dateString = dateStamp.strftime('%Y%m%d  %H:%M:%S')

        if (timeFrameSelection == '1' and time_ % 60 == 0) or (timeFrameSelection == '2' and time_ % 300 == 0) or (
                timeFrameSelection == '3' and time_ % 900 == 0) or (timeFrameSelection == '4' and time_ % 3600 == 0):
            if reqID in self.highArr and len(self.highArr[reqID]) > 0:
                high_ = np.max(self.highArr[reqID])
                self.highArr[reqID].clear()
            else:
                high_ = high

            if reqID in self.lowArr and len(self.lowArr[reqID]) > 0:
                low_ = np.min(self.lowArr[reqID])
                self.lowArr[reqID].clear()
            else:
                low_ = low

            if reqID not in self.histData:
                self.histData[reqID] = [
                    {"Date": dateString, "Open": open_, "High": high_, "Low": low_, "Close": close, "Volume": volume}]
            else:
                self.histData[reqID].append(
                    {"Date": dateString, "Open": open_, "High": high_, "Low": low_, "Close": close, "Volume": volume})

            print("Ticker:", self.tickerArr[reqID]['symbol'], "| High:", round(high, 2), "| Low:", round(low, 2),
                  "| Open:", round(open_, 2), "| Close:", round(close, 2), "| Volume:", round(volume, 2))

            self.analysisDataFrame(reqID, close)
        else:
            if reqID not in self.lowArr:
                self.lowArr[reqID] = [low]
            else:
                self.lowArr[reqID].append(low)

            if reqID not in self.highArr:
                self.highArr[reqID] = [low]
            else:
                self.highArr[reqID].append(low)

    def analysisDataFrame(self, reqID, close):
        dfData = pd.DataFrame(self.histData[reqID])
        firstClose = dfData.head(1)['Close'].values[0]

        if firstClose != 0:
            todayPercentChange = 100 * (close - firstClose) / firstClose
            print("Today's percent change: ", round(todayPercentChange, 2), '%')

        yesterdayLastClose = self.tickerArr[reqID]['yesterdayLastClose']
        if yesterdayLastClose != 0:
            yesterdayPercentChange = 100 * (close - yesterdayLastClose) / yesterdayLastClose
            print("Yesterday's percent change: ", round(yesterdayPercentChange, 2), '%')

        if strategySelection == '1':                                                        # ATR Trail Stop
            if close < 10:
                atrPeriod = 14
                atrFactor = 12
            elif 10 < close < 20:
                atrPeriod = 14
                atrFactor = 10
            elif 20 < close < 30:
                atrPeriod = 7
                atrFactor = 8
            elif 30 < close < 50:
                atrPeriod = 7
                atrFactor = 6
            elif close > 50:
                atrPeriod = 7
                atrFactor = 5

            atrDF = calcAtrTrailStop(dfData, atrPeriod, atrFactor, biasOptions[biasSelection])
            if len(atrDF.index) > 0:
                logFileName = self.tickerArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_ATR_' + self.tickerArr[reqID]['startTime'] + '.csv'
                atrDF.to_csv(logFileName)

                atrVal = atrDF.tail(1)['Trail'].values[0]
                ema = atrDF.tail(1)['EMA_200'].values[0]
                Zone = atrDF.tail(1)['Zone'].values[0]
                signal = atrDF.tail(1)['ACTION'].values[0]

                print("ATR value =", atrVal, "EMA =", ema, "Zone =", Zone, "Signal =", signal)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '2':                                              # Exponential moving average
            emaDF = calcEMA(dfData)

            if len(emaDF.index) > 0:
                logFileName = self.tickerArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_EMA_' + self.tickerArr[reqID]['startTime'] + '.csv'
                emaDF.to_csv(logFileName)

                ema9 = emaDF.tail(1)['MA_9'].values[0]
                ema27 = emaDF.tail(1)['MA_27'].values[0]
                ema54 = emaDF.tail(1)["MA_54"].values[0]

                MA_9_dist = emaDF.tail(1)["MA_9_dist"].values[0]
                MA_27_dist = emaDF.tail(1)["MA_27_dist"].values[0]
                MA_54_dist = emaDF.tail(1)["MA_54_dist"].values[0]

                MA_fast = emaDF.tail(1)["MA_fast"].values[0]
                MA_slow = emaDF.tail(1)["MA_slow"].values[0]
                MA_med = emaDF.tail(1)["MA_med"].values[0]
                signal = emaDF.tail(1)['ACTION'].values[0]

                print("ema9 =", ema9, "ema27 =", ema27, "ema54 =", ema54, "MA_9_dist =", MA_9_dist, "MA_27_dist =",
                      MA_27_dist, "MA_54_dist =", MA_54_dist, "MA_fast", MA_fast, "MA_slow", MA_slow, "MA_med", MA_med)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '3':                                                              # VWAP
            vwapDF = calcVWAP(dfData)

            if len(vwapDF.index) > 0:
                logFileName = self.tickerArr[reqID]['symbol'] + '_VWAP_' + self.tickerArr[reqID]['startTime'] + '.csv'
                vwapDF.to_csv(logFileName)

                ema9 = vwapDF.tail(1)['MA_9'].values[0]
                ema27 = vwapDF.tail(1)['MA_27'].values[0]

                VWAP_distance = vwapDF.tail(1)['VWAP_distance'].values[0]
                Zone = vwapDF.tail(1)['Zone'].values[0]
                MA_ratio = vwapDF.tail(1)['MA_ratio'].values[0]
                Cum_vol = vwapDF.tail(1)['Cum_Vol'].values[0]
                VWAP = vwapDF.tail(1)['VWAP'].values[0]
                VWAP_up1 = vwapDF.tail(1)['VWAP_up1'].values[0]
                VWAP_dn1 = vwapDF.tail(1)['VWAP_dn1'].values[0]
                signal = vwapDF.tail(1)['ACTION'].values[0]

                print("ema9 =", ema9, "ema27 =", ema27, "signal =", signal, "VWAP distance =", VWAP_distance,
                      "Zone =", Zone, "MA_ratio", MA_ratio, "Cum_vol =", Cum_vol, "VWAP =", VWAP, "VWAP up1 =",
                      VWAP_up1, "VWAP_dn1", VWAP_dn1)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '4':                                                      # TTM Squeeze
            ttmDF = calcTTMSqueeze(dfData)
            if len(ttmDF.index) > 0:
                logFileName = self.tickerArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_TTM_' + self.tickerArr[reqID]['startTime'] + '.csv'
                ttmDF.to_csv(logFileName)

                squeeze = ttmDF.tail(1)['squeeze'].values[0]
                momentum = ttmDF.tail(1)['momentum'].values[0]
                signal = ttmDF.tail(1)['ACTION'].values[0]
                ema9 = ttmDF.tail(1)['MA_9'].values[0]
                ema27 = ttmDF.tail(1)['MA_27'].values[0]
                momo = ttmDF.tail(1)['momo'].values[0]
                dir = ttmDF.tail(1)['dir'].values[0]
                val = ttmDF.tail(1)['val'].values[0]

                print("squeeze =", squeeze, 'momo =', momo, 'dir =', dir, 'val =', val, "momentum =", momentum,
                      "signal =", signal, "ema9 =", ema9, "ema27 =", ema27)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '5':                                                      # Top Breakout
            analyseDF = calcTopBreakOut(dfData, biasOptions[biasSelection])
            if len(analyseDF.index) > 0:
                logFileName = self.tickerArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_TopBreakOut_' + self.tickerArr[reqID]['startTime'] + '.csv'
                analyseDF.to_csv(logFileName)

                signal = analyseDF.tail(1)['ACTION'].values[0]
                Direction = analyseDF.tail(1)['pos'].values[0]
                QB = analyseDF.tail(1)['QB'].values[0]
                QS = analyseDF.tail(1)['QS'].values[0]
                HH = analyseDF.tail(1)['HH'].values[0]
                LL = analyseDF.tail(1)['LL'].values[0]

                Entry = analyseDF.tail(1)['Entry_ratio'].values[0]
                Exit = analyseDF.tail(1)['Exit_ratio'].values[0]

                print("Direction =", Direction, "Signal =", signal, "QB =", QB, "HH =", HH, "QS =", QS, "LL =", LL, "Entry Ratio = ", Entry,"Exit Ratio = ", Exit )

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)

    def orderAction(self, action, reqID, price):
        self.lastClose = price
        if not self.tickerArr[reqID]['orderPlaced']:
            if (action == 'buy') and (
                    self.tickerArr[reqID]['lastAction'] == 'start' or self.tickerArr[reqID]['lastAction'] == 'close'):
                count = buyPrice // price
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(tickers[reqID]),
                                    OrderSamples.IOC("BUY", count, math.ceil(price)))
                    print("Placed buy order for %s shares: %d " % (tickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.tickerArr[reqID]['orderCount'] = count
                    self.tickerArr[reqID]['orderPlaced'] = True
                    self.tickerArr[reqID]['lastAction'] = 'buy'
            if (action == 'close') and (
                    self.tickerArr[reqID]['lastAction'] == 'start' or self.tickerArr[reqID]['lastAction'] == 'buy'):
                count = abs(self.tickerArr[reqID]['position'])
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(tickers[reqID]),
                                    OrderSamples.IOC("SELL", count, math.floor(price)))
                    print("Closing order for %s shares: %d " % (tickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.tickerArr[reqID]['orderCount'] = count
                    self.tickerArr[reqID]['orderPlaced'] = True
                    self.tickerArr[reqID]['lastAction'] = 'close'
            if (action == 'sell') and (
                    self.tickerArr[reqID]['lastAction'] == 'start' or self.tickerArr[reqID]['lastAction'] == 'cover'):
                count = buyPrice // price
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(tickers[reqID]),
                                    OrderSamples.IOC("SELL", count, math.floor(price)))
                    print("Placed sell order for %s shares: %d " % (tickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.tickerArr[reqID]['orderCount'] = count
                    self.tickerArr[reqID]['orderPlaced'] = True
                    self.tickerArr[reqID]['lastAction'] = 'sell'
            if (action == 'cover') and (
                    self.tickerArr[reqID]['lastAction'] == 'start' or self.tickerArr[reqID]['lastAction'] == 'sell'):
                count = abs(self.tickerArr[reqID]['position'])
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(tickers[reqID]),
                                    OrderSamples.IOC("BUY", count, math.ceil(price)))
                    print("Covering order for %s shares: %d " % (tickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.tickerArr[reqID]['orderCount'] = count
                    self.tickerArr[reqID]['orderPlaced'] = True
                    self.tickerArr[reqID]['lastAction'] = 'cover'

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)

        if contract.symbol in tickers:
            reqID = tickers.index(contract.symbol)
            self.tickerArr[reqID]['position'] = position

    def positionEnd(self):
        if strategySelection == '3':
            for symbol in tickers:
                print("Requesting 1D historic data for VWAP")
                self.reqHistoricalData(reqId=tickers.index(symbol), contract=usTechStk(symbol), endDateTime='',
                                       durationStr='1 D',
                                       barSizeSetting=timeFrameOptions[timeFrameSelection], whatToShow='TRADES',
                                       useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])
        else:
            for symbol in tickers:
                self.reqHistoricalData(reqId=tickers.index(symbol), contract=usTechStk(symbol), endDateTime='',
                                       durationStr='2 D',
                                       barSizeSetting=timeFrameOptions[timeFrameSelection], whatToShow='TRADES',
                                       useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])


def timeFrameStr():
    if timeFrameSelection == '1':
        return '1'
    elif timeFrameSelection == '2':
        return '5'
    elif timeFrameSelection == '3':
        return '15'
    elif timeFrameSelection == '4':
        return '60'


# calculate Exponential moving average
def calcEMA(DF):
    df = DF.copy()

    df["MA_9"] = df["Close"].ewm(span=9, min_periods=9).mean()
    df["MA_27"] = df["Close"].ewm(span=27, min_periods=27).mean()
    df["MA_54"] = df["Close"].ewm(span=54, min_periods=54).mean()

    df["MA_9_dist"] = df["Close"] / df["MA_9"]
    df["MA_27_dist"] = df["Close"] / df["MA_27"]
    df["MA_54_dist"] = df["Close"] / df["MA_54"]

    df["MA_fast"] = df["MA_9"] / df["MA_27"]
    df["MA_slow"] = df["MA_9"] / df["MA_54"]
    df["MA_med"] = df["MA_27"] / df["MA_54"]

    for i in range(1, len(df)):
        df.loc[i, 'Zone'] = ''
        if df.loc[i, 'MA_9'] > df.loc[i, 'MA_27'] > df.loc[i, 'MA_54']:
            df.loc[i, 'Zone'] = "Squeeze Out"
        if df.loc[i, 'MA_9'] < df.loc[i, 'MA_27'] < df.loc[i, 'MA_54']:
            df.loc[i, 'Zone'] = "Squeeze In"

        df.loc[i, 'ACTION'] = 'NO'
        # pos
        if biasOptions[biasSelection] == 'Long':
            # Action
            if df.loc[i, 'Zone'] == 'Squeeze Out' and df.loc[i - 1, 'Zone'] == 'Squeeze In':
                df.loc[i, 'ACTION'] = 'buy'
            if df.loc[i, 'Zone'] == 'Squeeze in' and df.loc[i - 1, 'Zone'] == 'Squeeze out':
                df.loc[i, 'ACTION'] = 'close'

        if biasOptions[biasSelection] == 'Short':
            # Action
            if df.loc[i, 'Zone'] == 'Squeeze Out' and df.loc[i - 1, 'Zone'] == 'Squeeze In':
                df.loc[i, 'ACTION'] = 'cover'
            if df.loc[i, 'Zone'] == 'Squeeze in' and df.loc[i - 1, 'Zone'] == 'Squeeze out':
                df.loc[i, 'ACTION'] = 'sell'

    return df


# calculate True Range, Average True Range, Trailing stop
def calcAtrTrailStop(DF, atrPeriod, atrFactor, firstTrade):
    df = DF.copy()

    df['H-L'] = abs(df['High'] - df['Low'])  # Abs of difference between High and Low
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))  # Abs of difference between High and previous period's close
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))  # Abs of difference between Low and previous period's close
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['ATR'] = df['TR'].ewm(alpha=(1 / atrPeriod), adjust=False).mean()
    df['EMA_200'] = df["Close"].ewm(span=200, min_periods=200).mean()

    for i in range(1, len(df)):
        loss = df.loc[i, 'ATR'] * atrFactor
        if i == 1:
            df.loc[i, 'State'] = firstTrade
            if firstTrade == 'Long':
                df.loc[i, 'Trail'] = df.loc[i, 'Close'] - loss
            if firstTrade == 'Short':
                df.loc[i, 'Trail'] = df.loc[i, 'Close'] + loss
        else:
            pState = df.loc[i - 1, 'State']
            pTrail = df.loc[i - 1, 'Trail']
            if pState == 'Long':
                if df.loc[i, 'Close'] > pTrail:
                    df.loc[i, 'Trail'] = max(pTrail, (df.loc[i, 'Close'] - loss))
                    df.loc[i, 'State'] = 'Long'
                else:
                    df.loc[i, 'Trail'] = df.loc[i, 'Close'] + loss
                    df.loc[i, 'State'] = 'Short'
            elif pState == 'Short':
                if df.loc[i, 'Close'] < pTrail:
                    df.loc[i, 'Trail'] = min(pTrail, (df.loc[i, 'Close'] + loss))
                    df.loc[i, 'State'] = 'Short'
                else:
                    df.loc[i, 'Trail'] = df.loc[i, 'Close'] - loss
                    df.loc[i, 'State'] = 'Long'

        df.loc[i, 'Zone'] = 'no'
        if df.loc[i, 'Close'] > df.loc[i, 'Trail']:
            df.loc[i, 'Zone'] = 'above ATR'
        elif df.loc[i, 'Close'] < df.loc[i, 'Trail']:
            df.loc[i, 'Zone'] = 'below ATR'

        df.loc[i, 'ACTION'] = 'NO'
        # pos
        if biasOptions[biasSelection] == 'Long':
            # Action
            if df.loc[i, 'Zone'] == 'above ATR' and df.loc[i - 1, 'Zone'] == 'below ATR':
                df.loc[i, 'ACTION'] = 'buy'
            if df.loc[i, 'Zone'] == 'below ATR' and df.loc[i - 1, 'Zone'] == 'above ATR':
                df.loc[i, 'ACTION'] = 'close'

        if biasOptions[biasSelection] == 'Short':
            # Action
            if df.loc[i, 'Zone'] == 'below ATR' and df.loc[i - 1, 'Zone'] == 'above ATR':
                df.loc[i, 'ACTION'] = 'sell'
            if df.loc[i, 'Zone'] == 'above ATR' and df.loc[i - 1, 'Zone'] == 'below ATR':
                df.loc[i, 'ACTION'] = 'cover'

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

    df["MA_9"] = df["Close"].ewm(span=9, min_periods=9).mean()
    df["MA_27"] = df["Close"].ewm(span=27, min_periods=27).mean()

    df["MA_ratio"] = df["MA_9"] / df["MA_27"]

    for i in range(3, len(df)):
        vwap = df.loc[i, 'VWAP']
        df.loc[i, 'Dev'] = math.sqrt(max((df.loc[i, 'Cum_VP2'] / df.loc[i, 'Cum_Vol']) - (vwap * vwap), 0))
        df.loc[i, 'VWAP_up1'] = df.loc[i, 'VWAP'] + 1 * df.loc[i, 'Dev']
        df.loc[i, 'VWAP_dn1'] = df.loc[i, 'VWAP'] - 1 * df.loc[i, 'Dev']
        df.loc[i, 'VWAP_up2'] = df.loc[i, 'VWAP'] + 2 * df.loc[i, 'Dev']
        df.loc[i, 'VWAP_dn2'] = df.loc[i, 'VWAP'] - 2 * df.loc[i, 'Dev']

        df.loc[i, 'Zone'] = ''
        if (df.loc[i, 'Close'] < df.loc[i, 'VWAP_up1']) and (df.loc[i, 'Close'] > df.loc[i, 'VWAP']):
            df.loc[i, 'Zone'] = 'pos_slow'
        if (df.loc[i, 'Close'] < df.loc[i, 'VWAP_up2']) and (df.loc[i, 'Close'] > df.loc[i, 'VWAP_up1']):
            df.loc[i, 'Zone'] = 'pos_fast'
        if (df.loc[i, 'Close'] < df.loc[i, 'VWAP']) and (df.loc[i, 'Close'] > df.loc[i, 'VWAP_dn1']):
            df.loc[i, 'Zone'] = 'neg_slow'
        if (df.loc[i, 'Close'] < df.loc[i, 'VWAP_dn1']) and (df.loc[i, 'Close'] > df.loc[i, 'VWAP_dn2']):
            df.loc[i, 'Zone'] = 'neg_fast'

        df.loc[i,'VWAP_distance'] = 100 * (df.loc[i, 'Close'] - df.loc[i, 'VWAP']) / df.loc[i, 'Dev']
        df.loc[i, 'ACTION'] = 'NO'
        # pos
        if biasOptions[biasSelection] == 'Long':
            # Action
            if df.loc[i, 'Zone'] == 'pos_fast' and df.loc[i - 1, 'Zone'] == 'pos_fast' and df.loc[i - 2, 'Zone'] == 'pos_slow':
                df.loc[i, 'ACTION'] = 'buy'
            if df.loc[i, "MA_9"] < .99 * df.loc[i, "MA_27"]:
                df.loc[i, 'ACTION'] = 'close'

        if biasOptions[biasSelection] == 'Short':
            # Action
            if df.loc[i, 'Zone'] == 'neg_fast' and df.loc[i - 1, 'Zone'] == 'neg_fast' and df.loc[i - 2, 'Zone'] == 'neg_slow':
                df.loc[i, 'ACTION'] = 'sell'
            if df.loc[i, "MA_9"] > 1.01 * df.loc[i, "MA_27"]:
                df.loc[i, 'ACTION'] = 'cover'

    return df


# TTM Squeeze Calculation
def calcTTMSqueeze(DF, n=20):
    df = DF.copy()

    df["MA_9"] = df["Close"].ewm(span=9, min_periods=9).mean()
    df["MA_27"] = df["Close"].ewm(span=27, min_periods=27).mean()

    df['20sma'] = df['Close'].rolling(window=n).mean()
    df['sDev'] = df['Close'].rolling(window=n).std()
    df['LowerBandBB'] = df['20sma'] - (2 * df['sDev'])
    df['UpperBandBB'] = df['20sma'] + (2 * df['sDev'])

    df['H-L'] = abs(df['High'] - df['Low'])  # Abs of difference between High and Low
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))  # Abs of difference between High and previous period's close
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))  # Abs of difference between Low and previous period's close
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
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
        df.loc[i, 'preSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCLow'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'preSqueezeOut'] = df.loc[i, 'LowerBandKCLow'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow']

        df.loc[i, 'originalSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCMid'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'originalSqueezeOut'] = df.loc[i, 'LowerBandKCMid'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid']

        df.loc[i, 'extrSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCHigh'] and df.loc[
            i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCHigh'] and df.loc[i, 'LowerBandBB'] > df.loc[i - 1, 'LowerBandBB']
        df.loc[i, 'extrSqueezeOut'] = df.loc[i, 'LowerBandKCHigh'] < df.loc[i, 'LowerBandBB'] < df.loc[
            i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCHigh']

        if df.loc[i, 'extrSqueezeIn']:
            df.loc[i, 'squeeze'] = 'dark_red'
        elif df.loc[i, 'extrSqueezeOut']:
            df.loc[i, 'squeeze'] = 'dark_red'
        elif df.loc[i, 'originalSqueezeIn']:
            df.loc[i, 'squeeze'] = 'red'
        elif df.loc[i, 'originalSqueezeOut']:
            df.loc[i, 'squeeze'] = 'red'
        elif df.loc[i, 'preSqueezeIn']:
            df.loc[i, 'squeeze'] = 'pink'
        elif df.loc[i, 'preSqueezeOut']:
            df.loc[i, 'squeeze'] = 'yellow'
        else:
            df.loc[i, 'squeeze'] = 'green'

    # momo calculation
    df['max_high'] = df['High'].rolling(window=n).max()
    df['min_low'] = df['Low'].rolling(window=n).min()
    df["MA_20"] = df['Close'].ewm(span=n, min_periods=n).mean()
    df['K'] = (df['max_high'] + df['min_low']) / 2 + df["MA_20"]
    df['x'] = df.index
    df['y'] = df['Close'] - df['K'] / 2
    df['x2'] = df['x'] * df['x']
    df['xy'] = df['x'] * df['y']

    a = (n * df['xy'].rolling(n).sum() - df['x'].rolling(n).sum() * df['y'].rolling(n).sum()) / (
            n * df['x2'].rolling(n).sum() - df['x'].rolling(n).sum() * df['x'].rolling(n).sum())
    b = (df['x2'].rolling(n).sum() * df['y'].rolling(n).sum() - df['x'].rolling(n).sum() * df['xy'].rolling(
        n).sum()) / (n * df['x2'].rolling(n).sum() - df['x'].rolling(n).sum() * df['x'].rolling(n).sum())

    df['momo'] = 100 * (a * df["x"] + b)

    for i in range(1, len(df)):
        if df.loc[i, 'momo'] >= 0:
            df.loc[i, 'val'] = 'pos'
        if df.loc[i, 'momo'] < 0:
            df.loc[i, 'val'] = 'neg'
        if df.loc[i, 'momo'] >= df.loc[i - 1, 'momo']:
            df.loc[i, 'dir'] = 'up'
        if df.loc[i, 'momo'] < df.loc[i - 1, 'momo']:
            df.loc[i, 'dir'] = 'dn'
    for i in range(1, len(df)):
        if df.loc[i, 'val'] == 'pos' and df.loc[i, 'dir'] == 'up':
            df.loc[i, 'momentum'] = 'cyan'
        if df.loc[i, 'val'] == 'pos' and df.loc[i, 'dir'] == 'dn':
            df.loc[i, 'momentum'] = 'blue'
        if df.loc[i, 'val'] == 'neg' and df.loc[i, 'dir'] == 'dn':
            df.loc[i, 'momentum'] = 'red'
        if df.loc[i, 'val'] == 'neg' and df.loc[i, 'dir'] == 'up':
            df.loc[i, 'momentum'] = 'yellow'
    for i in range(1, len(df)):
        df.loc[i, 'ACTION'] = 'NO'
        df.loc[i, 'Trigger'] = 'NO'
        # pos
        if biasOptions[biasSelection] == 'Long':
            # Action
            if df.loc[i, 'squeeze'] == 'yellow' and df.loc[i, 'momentum'] == 'cyan' and df.loc[i, 'MA_9'] > df.loc[i, 'MA_27']:
                df.loc[i, 'ACTION'] = 'buy'
            if df.loc[i, 'MA_9'] < df.loc[i, 'MA_27']:
                df.loc[i, 'ACTION'] = 'close'

        if biasOptions[biasSelection] == 'Short':
            # Action
            if df.loc[i, 'squeeze'] == 'yellow' and df.loc[i, 'momentum'] == 'red' and df.loc[i, 'MA_9'] < df.loc[i, 'MA_27']:
                df.loc[i, 'ACTION'] = 'sell'
            if df.loc[i, 'MA_9'] > df.loc[i, 'MA_27']:
                df.loc[i, 'ACTION'] = 'cover'

    return df


# Top Ultimate Breakout Indicator
def calcTopBreakOut(DF, buyOrSell):
    df = DF.copy()

    buyEntry = 3
    sellEntry = 3
    buyExit = 50
    sellExit = 50

    df['HH'] = df['High'].rolling(window=sellExit).max()
    df['LL'] = df['Low'].rolling(window=buyExit).min()
    df['QB'] = df['High'].rolling(window=buyEntry).max()
    df['QS'] = df['Low'].rolling(window=sellEntry).min()

    df['co'] = df.index > max(sellExit, buyExit)

    df.loc[1, 'pos'] = 0
    for i in range(2, len(df)):
        df.loc[i, 'ACTION'] = 'NO'
        # pos
        df.loc[i, 'Entry_ratio'] = df.loc[i, 'High'] / df.loc[i - 1, 'QB']
        df.loc[i, 'Exit_ratio'] = df.loc[i, 'Low'] / df.loc[i - 1, 'QS']

        if buyOrSell == 'Long':
            if df.loc[i, 'co'] and df.loc[i, 'High'] > df.loc[i - 1, 'QB']:
                df.loc[i, 'pos'] = 1
            elif df.loc[i, 'Low'] < df.loc[i - 1, 'LL']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i - 1, 'pos']
            # Action
            if df.loc[i, 'pos'] == 1 and df.loc[i - 1, 'pos'] == 0:
                df.loc[i, 'ACTION'] = 'buy'
            if df.loc[i, 'pos'] == 0 and df.loc[i - 1, 'pos'] == 1:
                df.loc[i, 'ACTION'] = 'close'
            # Scan

        elif buyOrSell == 'Short':
            # pos
            if df.loc[i - 1, 'QS'] != np.NaN and df.loc[i, 'co'] and df.loc[i, 'Low'] < df.loc[i - 1, 'QS']:
                df.loc[i, 'pos'] = -1
            elif df.loc[i - 1, 'High'] > df.loc[i - 2, 'HH']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i - 1, 'pos']
            # Action
            if df.loc[i, 'pos'] == -1 and df.loc[i - 1, 'pos'] == 0:
                df.loc[i, 'ACTION'] = 'sell'
            if df.loc[i, 'pos'] == 0 and df.loc[i - 1, 'pos'] == -1:
                df.loc[i, 'ACTION'] = 'cover'
            # Scan
    return df


def usTechStk(symbol, sec_type="STK", currency="USD", exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


print("Welcome to Algorithms Trading")
print("")

app = IBPy()
app.connect("127.0.0.1", 4002, 1001)

buyPrice = 5000
# buyPrice = 3000

# enter tickers
while True:
    tickers = input("Enter multiple ticker symbols space-separated: ").split()
    if len(tickers) > 0:
        print('')
        break

# strategy Selection
while True:
    strategyOptions = collections.OrderedDict()
    strategyOptions["1"] = "ATR super trend strategy"
    strategyOptions["2"] = "Exp Moving Avg"
    strategyOptions["3"] = "VWAP"
    strategyOptions["4"] = "TTM Squeeze"
    strategyOptions["5"] = "Top Breakout"
    options = strategyOptions.keys()
    for entry in options:
        print(entry + ")\t" + strategyOptions[entry])
    strategySelection = input("Select trading strategy: ")
    if strategySelection == '1' or strategySelection == '2' or strategySelection == '3' or strategySelection == '4' or strategySelection == '5':
        print('')
        break

# short/long selection
while True:
    biasOptions = collections.OrderedDict()
    biasOptions["1"] = "Long"
    biasOptions["2"] = "Short"
    options = biasOptions.keys()
    for entry in options:
        print(entry + ")\t" + biasOptions[entry])
    biasSelection = input("Select Long or Short: ")
    if biasSelection == "1" or biasSelection == "2":
        print('')
        break

timeFrameOptions = collections.OrderedDict()
timeFrameOptions["1"] = "1 min"
timeFrameOptions["2"] = "5 mins"
timeFrameOptions["3"] = "15 mins"
timeFrameOptions["4"] = "1 hour"
# time frame selection except VWAP
if strategySelection != '3':
    while True:
        options = timeFrameOptions.keys()
        for entry in options:
            print(entry + ")\t" + timeFrameOptions[entry])
        timeFrameSelection = input("Select timeframe: ")
        if timeFrameSelection == '1' or timeFrameSelection == '2' or timeFrameSelection == '3' or timeFrameSelection == '4':
            print('')
            break
else:
    timeFrameSelection = '1'

for ticker in tickers:
    reqId = tickers.index(ticker)
    app.tickerArr[reqId] = {'symbol': ticker, 'orderCount': 0, 'orderPlaced': False, 'lastAction': 'start', 'position': 0,
                            'startTime': datetime.datetime.now().strftime('%m%d_%H%M'), 'yesterdayLastClose': 0}

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
yesterdayCloseTime = yesterday.strftime("%Y%m%d")+"  13:00:00"

app.reqPositions()

app.run()