import collections
import pandas as pd
import numpy as np
import math
import datetime
import csv
import threading

from ibapi.client import EClient
from ibapi.contract import *
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.scanner import ScannerSubscription
from ibapi.tag_value import TagValue

from OrderSamples import OrderSamples
from Strategies import Strategies


class IBPy(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        self.originalTickers = []
        self.originalHistData = {}
        self.originalHistEndCount = 0
        self.originalHistTotalCount = 0

        self.pickedTickers = []
        self.lowArr = {}  # low price array
        self.highArr = {}  # high price array
        self.pickedHistData = {}  # history data
        self.nextOrderId = 0
        self.orderIdArr = {}
        self.pickedStatusArr = {}
        self.orderDF = pd.DataFrame(columns=['Symbol', 'Action', 'Order', 'Position', 'Time', 'Avg Price'])
        self.lastClose = 0

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        super().error(reqId, errorCode, errorString)

        # ERROR handling for 162 Historical Market Data Service error message:HMDS query returned no data
        if reqId != 5000 and reqId < 1000 and errorCode == 162:
            if self.originalHistTotalCount > 0:
                self.originalHistTotalCount = self.originalHistTotalCount - 1
                if self.originalHistEndCount == self.originalHistTotalCount:
                    self.sortOriginalStocks()
        # print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)

    def historicalData(self, reqID, bar):
        if reqID < 1000:
            # store historical data for all tickers
            if reqID not in self.originalHistData:
                self.originalHistData[reqID] = [
                    {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                     "Volume": bar.volume}]
            else:
                self.originalHistData[reqID].append(
                    {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                     "Volume": bar.volume})
        else:
            # store historical data for picked tickers
            reqIndex = reqID - 1000
            if reqIndex not in self.pickedHistData:
                self.pickedHistData[reqIndex] = [
                    {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                     "Volume": bar.volume}]
            else:
                self.pickedHistData[reqIndex].append(
                    {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close,
                     "Volume": bar.volume})

    def historicalDataEnd(self, reqID: int, start: str, end: str):
        if reqID < 1000:
            print('Received Historical data for', self.originalTickers[reqID])
            # check if received historical data for all tickers
            self.originalHistEndCount = self.originalHistEndCount + 1
            if self.originalHistEndCount == self.originalHistTotalCount:
                self.sortOriginalStocks()
        else:
            reqIndex = reqID - 1000
            self.reqRealTimeBars(reqIndex, usTechStk(self.pickedTickers[reqIndex]), 5, "TRADES", False, [])

    def sortOriginalStocks(self):
        filterTickers = []
        for ticker in self.originalTickers:
            reqID = self.originalTickers.index(ticker)
            if reqID in self.originalHistData:
                dfData = pd.DataFrame(self.originalHistData[reqID])

                firstClose = dfData.head(1)['Close'].values[0]
                close = dfData.tail(1)['Close'].values[0]

                if firstClose != 0 and close != 0:
                    if biasSelection == '1':        # Percent Gain for Long
                        percentChange = 100 * (close - firstClose) / firstClose
                    elif biasSelection == '2':      # Percent Lose for Short
                        percentChange = 100 * (firstClose - close) / firstClose
                    filterTickers.append({'ticker': ticker, 'percentChange': percentChange})

        def sortByPercentChange(tickers):
            return tickers.get('percentChange')

        def sortByATRDistance(ticker):
            return abs(ticker.get('atrDist'))

        def sortByVWAPDistance(ticker):
            return abs(ticker.get('vwapDist'))

        def sortByMomo(ticker):
            return abs(ticker.get('momo'))

        def sortByDistance(ticker):
            return abs(ticker.get('distance'))

        filterTickers.sort(key=sortByPercentChange, reverse=True)

        if not advancedFilter:
            if len(filterTickers) > 5:
                for arrayIndex in range(0, 5):
                    self.pickedTickers.append(filterTickers[arrayIndex]['ticker'])
            else:
                for ticker in filterTickers:
                    self.pickedTickers.append(ticker['ticker'])
        else:
            tmpPickedTickers = []

            if len(filterTickers) > 20:
                for arrayIndex in range(0, 20):
                    tmpPickedTickers.append(filterTickers[arrayIndex]['ticker'])
            else:
                for ticker in filterTickers:
                    tmpPickedTickers.append(ticker['ticker'])

            if strategySelection == '1':  # ATR
                atrFilterTickers = []

                for ticker in tmpPickedTickers:
                    reqID = self.originalTickers.index(ticker)
                    dfData = pd.DataFrame(self.originalHistData[reqID])
                    close = dfData.tail(1)['Close'].values[0]

                    try:
                        atrDF = Strategies.ATR(dfData, close, biasOptions[biasSelection])
                        atrVal = atrDF.tail(1)['ATR'].values[0]
                        close = atrDF.tail(1)['Close'].values[0]
                        atrDist = float(atrDF.tail(1)['ATR_dist'].values[0])

                        if (biasSelection == '1' and close < atrVal) or (biasSelection == '2' and close > atrVal):
                            atrFilterTickers.append({'ticker': ticker, 'atrDist': atrDist})
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'ATR except: ', e)
                        continue

                if len(atrFilterTickers) > 0:
                    atrFilterTickers.sort(key=sortByATRDistance)

                    if len(atrFilterTickers) > 5:
                        for arrayIndex in range(0, 5):
                            self.pickedTickers.append(atrFilterTickers[arrayIndex]['ticker'])
                    else:
                        for ticker in atrFilterTickers:
                            self.pickedTickers.append(ticker['ticker'])
            elif strategySelection == '2':  # EMA
                for ticker in tmpPickedTickers:
                    reqID = self.originalTickers.index(ticker)
                    dfData = pd.DataFrame(self.originalHistData[reqID])

                    try:
                        emaDF = Strategies.EMA(dfData, biasOptions[biasSelection])
                        zone = emaDF.tail(1)['Zone'].values[0]

                        if (biasSelection == '1' and zone == 'Squeeze In') or (biasSelection == '2' and zone == 'Squeeze Out'):
                            self.pickedTickers.append(ticker)
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'EMA except: ', e)
                        continue
            elif strategySelection == '3':  # VWAP
                vwapFilterTickers = []

                for ticker in tmpPickedTickers:
                    reqID = self.originalTickers.index(ticker)
                    dfData = pd.DataFrame(self.originalHistData[reqID])

                    try:
                        vwapDF = Strategies.VWAP(dfData, biasOptions[biasSelection])
                        vwapVal = vwapDF.tail(1)['VWAP'].values[0]
                        vwapDist = float(vwapDF.tail(1)['VWAP_distance'].values[0])

                        if (biasSelection == '1' and close > vwapVal) or (biasSelection == '2' and close < vwapVal):
                            vwapFilterTickers.append({'ticker': ticker, 'vwapDist': vwapDist})
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'VWAP except: ', e)
                        continue

                if len(vwapFilterTickers) > 0:
                    vwapFilterTickers.sort(key=sortByVWAPDistance)

                    if len(vwapFilterTickers) > 5:
                        for arrayIndex in range(0, 5):
                            self.pickedTickers.append(vwapFilterTickers[arrayIndex]['ticker'])
                    else:
                        for ticker in vwapFilterTickers:
                            self.pickedTickers.append(ticker['ticker'])
            elif strategySelection == '4':  # TTM Squeeze
                ttmFilterTickers = []

                for ticker in tmpPickedTickers:
                    reqID = self.originalTickers.index(ticker)
                    dfData = pd.DataFrame(self.originalHistData[reqID])

                    try:
                        ttmDF = Strategies.TTMSqueeze(dfData, bias=biasOptions[biasSelection])
                        momentum = ttmDF.tail(1)['momentum'].values[0]
                        momo = float(ttmDF.tail(1)['momo'].values[0])

                        if (biasSelection == '1' and momentum == 'yellow') or (
                                biasSelection == '2' and momentum == 'blue'):
                            ttmFilterTickers.append({'ticker': ticker, 'momo': momo})
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'TTMSqueeze except: ', e)

                if len(ttmFilterTickers) > 0:
                    ttmFilterTickers.sort(key=sortByMomo)

                    if len(ttmFilterTickers) > 5:
                        for arrayIndex in range(0, 5):
                            self.pickedTickers.append(ttmFilterTickers[arrayIndex]['ticker'])
                    else:
                        for ticker in ttmFilterTickers:
                            self.pickedTickers.append(ticker['ticker'])
            elif strategySelection == '5':  # Top Break out
                topFilterTickers = []
                for ticker in tmpPickedTickers:
                    reqID = self.originalTickers.index(ticker)
                    dfData = pd.DataFrame(self.originalHistData[reqID])
                    try:
                        topDF = Strategies.TopBreakOut(dfData, bias=biasOptions[biasSelection])
                        distance = float(topDF.tail(1)['Distance'].values[0])
                        if distance != np.NAN:
                            topFilterTickers.append({'ticker': ticker, 'distance': distance})
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'TopBreakOut except: ', e)

                if len(topFilterTickers) > 0:
                    topFilterTickers.sort(key=sortByDistance)

                    if len(topFilterTickers) > 5:
                        for arrayIndex in range(0, 5):
                            self.pickedTickers.append(topFilterTickers[arrayIndex]['ticker'])
                    else:
                        for ticker in topFilterTickers:
                            self.pickedTickers.append(ticker['ticker'])
        if len(self.pickedTickers) > 0:
            # release variables for original tickers
            self.originalTickers = []
            self.originalHistData = {}
            self.originalHistEndCount = 0

            for ticker in self.pickedTickers:
                arrIndex = self.pickedTickers.index(ticker)
                self.pickedStatusArr[arrIndex] = {'symbol': ticker, 'orderCount': 0, 'orderPlaced': False,
                                                  'lastAction': 'start', 'position': 0, 'tradeCount': 0,
                                                  'startTime': datetime.datetime.now().strftime('%m%d_%H%M'),
                                                  'endTrade': False}

            self.reqPositions()
        else:
            print('No picked tickers')

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                            whyHeld, mktCapPrice)
        # print("OrderStatus - Id:", orderId, "Status:", status, "Filled:", filled, "Remaining:", remaining)

        if orderId in self.orderIdArr:
            reqID = self.orderIdArr[orderId]
            tickerObj = self.pickedStatusArr[reqID]
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
                        self.pickedStatusArr[reqID]['orderPlaced'] = False
                        self.pickedStatusArr[reqID]['tradeCount'] = self.pickedStatusArr[reqID]['tradeCount'] + 1
                        dictionary = {'Symbol': tickerObj['symbol'], 'Action': tickerObj['lastAction'],
                                      'Order': tickerObj['orderCount'],
                                      'Position': self.pickedStatusArr[reqID]['position'],
                                      'Time': datetime.datetime.now().strftime('%Y%m%d  %H:%M:%S'),
                                      'Avg Price': avgFillPrice}
                        self.orderDF = self.orderDF.append(dictionary, ignore_index=True)
                        self.orderDF.set_index("Time", inplace=True)
                        logFileName = 'log/orders_' + self.pickedStatusArr[reqID]['startTime'] + '.csv'
                        self.orderDF.to_csv(logFileName)

                        if self.pickedStatusArr[reqID]['endTrade']:
                            self.cancelRealTimeBars(reqID)
                            print(tickerObj['symbol'], 'trade ended')

    def realtimeBar(self, reqID: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqID, time_, open_, high, low, close, volume, wap, count)

        symbol = self.pickedStatusArr[reqID]['symbol']
        if self.pickedStatusArr[reqID]['tradeCount'] < maxOrderCount:
            if datetime.datetime.now() < endTimeDate:
                self.appendRealData(reqID, time_, high, low, open_, close, volume)
            else:
                print('Time is up for', symbol)
                self.endTrade(reqID)
        else:
            print('Max number of trades for', symbol, 'has been reached')
            self.endTrade(reqID)

    def endTrade(self, reqID):
        self.pickedStatusArr[reqID]['endTrade'] = True
        tickerObj = self.pickedStatusArr[reqID]
        remaining = tickerObj['position']
        ticker = tickerObj['symbol']
        if remaining == 0:
            self.cancelRealTimeBars(reqID)
            print(ticker, 'trade ended')
        elif remaining > 0:
            self.nextOrderId = self.nextOrderId + 1
            self.placeOrder(self.nextOrderId, usTechStk(tickerObj['symbol']),
                            OrderSamples.IOC("SELL", remaining, math.floor(self.lastClose)))
        elif remaining < 0:
            self.nextOrderId = self.nextOrderId + 1
            self.placeOrder(self.nextOrderId, usTechStk(tickerObj['symbol']),
                            OrderSamples.IOC("BUY", abs(remaining), math.floor(self.lastClose)))

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

            if reqID not in self.pickedHistData:
                self.pickedHistData[reqID] = [
                    {"Date": dateString, "Open": open_, "High": high_, "Low": low_, "Close": close, "Volume": volume}]
            else:
                self.pickedHistData[reqID].append(
                    {"Date": dateString, "Open": open_, "High": high_, "Low": low_, "Close": close, "Volume": volume})

            print("Ticker:", self.pickedStatusArr[reqID]['symbol'], "| High:", round(high_, 2), "| Low:",
                  round(low_, 2), "| Open:", round(open_, 2), "| Close:", round(close, 2), "| Volume:", round(volume, 2))

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
        dfData = pd.DataFrame(self.pickedHistData[reqID])

        if strategySelection == '1':  # ATR Trail Stop
            atrDF = Strategies.ATR(dfData, close, bias=biasOptions[biasSelection])

            if len(atrDF.index) > 0:
                logFileName = 'log/' + self.pickedStatusArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_ATR_' + self.pickedStatusArr[reqID]['startTime'] + '.csv'
                atrDF.to_csv(logFileName)

                atrVal = atrDF.tail(1)['Trail'].values[0]
                ema = atrDF.tail(1)['EMA_200'].values[0]
                Zone = atrDF.tail(1)['Zone'].values[0]
                signal = atrDF.tail(1)['ACTION'].values[0]

                print("ATR value =", atrVal, "EMA =", ema, "Zone =", Zone, "Signal =", signal)
                print('')

                if biasSelection == '1':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasSelection == '2':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '2':  # Exponential moving average
            emaDF = Strategies.EMA(dfData, bias=biasOptions[biasSelection])

            if len(emaDF.index) > 0:
                logFileName = 'log/' + self.pickedStatusArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_EMA_' + self.pickedStatusArr[reqID]['startTime'] + '.csv'
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
                      MA_27_dist, "MA_54_dist =", MA_54_dist, "MA_fast =", MA_fast, "MA_slow =", MA_slow, "MA_med =", MA_med)
                print('')

                if biasSelection == '1':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasSelection == '2':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '3':  # VWAP
            vwapDF = Strategies.VWAP(dfData, bias=biasOptions[biasSelection])

            if len(vwapDF.index) > 0:
                logFileName = 'log/' + self.pickedStatusArr[reqID]['symbol'] + '_VWAP_' + self.pickedStatusArr[reqID][
                    'startTime'] + '.csv'
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
                      "Zone =", Zone, "MA_ratio =", MA_ratio, "Cum_vol =", Cum_vol, "VWAP =", VWAP, "VWAP up1 =",
                      VWAP_up1, "VWAP_dn1 =", VWAP_dn1)
                print('')

                if biasSelection == '1':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasSelection == '2':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '4':  # TTM Squeeze
            ttmDF = Strategies.TTMSqueeze(dfData, bias=biasOptions[biasSelection])
            if len(ttmDF.index) > 0:
                logFileName = 'log/' + self.pickedStatusArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_TTM_' + self.pickedStatusArr[reqID]['startTime'] + '.csv'
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
                print('')

                if biasSelection == '1':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasSelection == '2':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)
        elif strategySelection == '5':  # Top Breakout
            analyseDF = Strategies.TopBreakOut(dfData, bias=biasOptions[biasSelection])
            if len(analyseDF.index) > 0:
                logFileName = 'log/' + self.pickedStatusArr[reqID]['symbol'] + '_' + timeFrameStr() + \
                              '_TopBreakOut_' + self.pickedStatusArr[reqID]['startTime'] + '.csv'
                analyseDF.to_csv(logFileName)

                signal = analyseDF.tail(1)['ACTION'].values[0]
                Direction = analyseDF.tail(1)['pos'].values[0]
                QB = analyseDF.tail(1)['QB'].values[0]
                QS = analyseDF.tail(1)['QS'].values[0]
                HH = analyseDF.tail(1)['HH'].values[0]
                LL = analyseDF.tail(1)['LL'].values[0]

                Entry = analyseDF.tail(1)['Entry_ratio'].values[0]
                Exit = analyseDF.tail(1)['Exit_ratio'].values[0]
                distance = analyseDF.tail(1)['Distance'].values[0]

                print("Direction =", Direction, "Signal =", signal, "QB =", QB, "HH =", HH, "QS =", QS, "LL =", LL,
                      "Entry Ratio =", Entry, "Exit Ratio =", Exit, "Distance =", distance)
                print('')

                if biasSelection == '1':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'close':
                        print("Received close Signal")
                        self.orderAction(signal, reqID, close)
                if biasSelection == '2':
                    if signal == 'sell':
                        print("Received sell Signal")
                        self.orderAction(signal, reqID, close)
                    if signal == 'cover':
                        print("Received cover Signal")
                        self.orderAction(signal, reqID, close)

    def orderAction(self, action, reqID, price):
        self.lastClose = price
        statusObj = self.pickedStatusArr[reqID]
        if not statusObj['orderPlaced']:
            if (action == 'buy') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'close') and statusObj['position'] == 0:
                count = buyPrice // price
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(self.pickedTickers[reqID]), OrderSamples.IOC("BUY", count, math.ceil(price)))
                    print("Placed buy order for %s shares: %d " % (self.pickedTickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.pickedStatusArr[reqID]['orderCount'] = count
                    self.pickedStatusArr[reqID]['orderPlaced'] = True
                    self.pickedStatusArr[reqID]['lastAction'] = 'buy'
            if (action == 'close') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'buy') and statusObj['position'] > 0:
                count = abs(statusObj['position'])
                self.nextOrderId = self.nextOrderId + 1
                self.placeOrder(self.nextOrderId, usTechStk(self.pickedTickers[reqID]),
                                OrderSamples.IOC("SELL", count, math.floor(price)))
                print("Closing order for %s shares: %d " % (self.pickedTickers[reqID], count))
                self.orderIdArr[self.nextOrderId] = reqID
                self.pickedStatusArr[reqID]['orderCount'] = count
                self.pickedStatusArr[reqID]['orderPlaced'] = True
                self.pickedStatusArr[reqID]['lastAction'] = 'close'
            if (action == 'sell') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'cover') and statusObj['position'] == 0:
                count = buyPrice // price
                if count > 0:
                    self.nextOrderId = self.nextOrderId + 1
                    self.placeOrder(self.nextOrderId, usTechStk(self.pickedTickers[reqID]),
                                    OrderSamples.IOC("SELL", count, math.floor(price)))
                    print("Placed sell order for %s shares: %d " % (self.pickedTickers[reqID], count))
                    self.orderIdArr[self.nextOrderId] = reqID
                    self.pickedStatusArr[reqID]['orderCount'] = count
                    self.pickedStatusArr[reqID]['orderPlaced'] = True
                    self.pickedStatusArr[reqID]['lastAction'] = 'sell'
            if (action == 'cover') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'sell') and statusObj['position'] < 0:
                count = abs(statusObj['position'])
                self.nextOrderId = self.nextOrderId + 1
                self.placeOrder(self.nextOrderId, usTechStk(self.pickedTickers[reqID]),
                                OrderSamples.IOC("BUY", count, math.ceil(price)))
                print("Covering order for %s shares: %d " % (self.pickedTickers[reqID], count))
                self.orderIdArr[self.nextOrderId] = reqID
                self.pickedStatusArr[reqID]['orderCount'] = count
                self.pickedStatusArr[reqID]['orderPlaced'] = True
                self.pickedStatusArr[reqID]['lastAction'] = 'cover'

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)

        if contract.symbol in self.pickedTickers:
            reqID = self.pickedTickers.index(contract.symbol)
            self.pickedStatusArr[reqID]['position'] = position

    def positionEnd(self):
        for ticker in self.pickedTickers:
            reqId = self.pickedTickers.index(ticker)
            self.reqHistoricalData(reqId=1000 + reqId, contract=usTechStk(ticker), endDateTime='',
                                   durationStr='2 D', barSizeSetting=timeFrameOptions[timeFrameSelection],
                                   whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])

    def getHistDatas(self):
        self.originalHistTotalCount = len(self.originalTickers)
        for ticker in self.originalTickers:
            self.reqHistoricalData(reqId=self.originalTickers.index(ticker), contract=usTechStk(ticker), endDateTime='',
                                   durationStr='1 D', barSizeSetting='1 min', whatToShow='TRADES',
                                   useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])

    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails, distance: str, benchmark: str,
                    projection: str, legsStr: str):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark, projection, legsStr)

        if len(
                self.originalTickers) < 40:  # Error handling for 322 error processing request.Only 50 simultaneous API historical data requests allowed.
            self.originalTickers.append(contractDetails.contract.symbol)

    def scannerDataEnd(self, reqId: int):
        super().scannerDataEnd(reqId)

        print('Most active stocks are: ', self.originalTickers)
        self.getHistDatas()
        self.cancelScannerSubscription(5000)


def timeFrameStr():
    if timeFrameSelection == '1':
        return '1'
    elif timeFrameSelection == '2':
        return '5'
    elif timeFrameSelection == '3':
        return '15'
    elif timeFrameSelection == '4':
        return '60'


def usTechStk(symbol, sec_type="STK", currency="USD", exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def startScan():
    if inputMethodSelection == '1' or inputMethodSelection == '3':
        app.getHistDatas()
    elif inputMethodSelection == '2':
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "MOST_ACTIVE"

        tagValues = [TagValue("usdMarketCapAbove", "500000"), TagValue("priceAbove", "2"),
                     TagValue("priceBelow", "1000"), TagValue("volumeAbove", "1000")]

        app.reqScannerSubscription(5000, scanSub, [], tagValues)


print("Welcome to Algorithms Trading")
print("")

buyPrice = 1000

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
while True:
    options = timeFrameOptions.keys()
    for entry in options:
        print(entry + ")\t" + timeFrameOptions[entry])
    timeFrameSelection = input("Select timeframe: ")
    if timeFrameSelection == '1' or timeFrameSelection == '2' or timeFrameSelection == '3' or timeFrameSelection == '4':
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

# Enter start time
while True:
    startOption = input('Start now?(Y/N)')

    if startOption.lower() == 'y':
        print('')
        break
    elif startOption.lower() == 'n':
        startTimeStr = input("Enter a start time in MM/DD/YYYY HH:MM format: ")
        try:
            startTimeDate = datetime.datetime.strptime(startTimeStr, '%m/%d/%Y %H:%M')
            if startTimeDate > datetime.datetime.now():
                print('')
                break
            else:
                print('Invalid time')
        except ValueError:
            print("Incorrect format. It should be MM/DD/YYYY HH:MM")

# Enter end time
while True:
    endOption = input('Run forever?(Y/N)')

    if endOption.lower() == 'y':
        endTimeDate = datetime.datetime.max
        print('')
        break
    elif endOption.lower() == 'n':
        endTimeStr = input("Enter an end time in MM/DD/YYYY HH:MM format: ")
        try:
            endTimeDate = datetime.datetime.strptime(endTimeStr, '%m/%d/%Y %H:%M')
            if endTimeDate > datetime.datetime.now():
                print('')
                break
            else:
                print('Invalid time')
        except ValueError:
            print("Incorrect format. It should be MM/DD/YYYY HH:MM")

app = IBPy()
app.connect("127.0.0.1", 4002, 1001)

inputOptions = collections.OrderedDict()
inputOptions['1'] = 'Input list from CSV'
inputOptions['2'] = 'IB Scanner'
inputOptions['3'] = 'Input list from user'
while True:
    options = inputOptions.keys()
    for entry in options:
        print(entry + ")\t" + inputOptions[entry])
    inputMethodSelection = input("Select Input Stock Method: ")
    if inputMethodSelection == '1':
        filenames = input("Enter csv filenames space-separated: ").split()
        if len(filenames) > 0:
            for filename in filenames:
                csvFile = 'tickers/' + filename + '.csv'
                with open(csvFile) as f:
                    reader = csv.DictReader(f, delimiter=',')
                    for row in reader:
                        if len(app.originalTickers) < 40:
                            app.originalTickers.append(row['Symbol'])
            print('')
            break
        else:
            print('No tickers!!!')
    elif inputMethodSelection == '2':
        print('')
        break
    elif inputMethodSelection == '3':
        tickers = input("Enter multiple ticker symbols space-separated: ").split()
        if len(tickers) > 0:
            for ticker in tickers:
                app.originalTickers.append(ticker)
            print('')
            break

# Enter maximum number of trades per ticker
while True:
    maxOrderCount = input('Enter maximum number of orders per ticker: ')
    if maxOrderCount.isdigit():
        maxOrderCount = int(maxOrderCount)
        if maxOrderCount > 0:
            print('')
            break

# Input advanced filter
while True:
    advancedFilterInput = input('Advanced Filter?(Y/N)')
    print('')
    if advancedFilterInput.lower() == 'y':
        advancedFilter = True
        break
    elif advancedFilterInput.lower() == 'n':
        advancedFilter = False
        break

if startOption.lower() == 'y':
    startScan()
elif startOption.lower() == 'n':
    delay = (startTimeDate - datetime.datetime.now()).total_seconds()
    print('delay: ', delay)
    threading.Timer(delay, startScan).start()

app.run()