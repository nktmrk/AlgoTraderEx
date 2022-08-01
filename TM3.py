from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *

import pandas as pd
import numpy as np
import threading
import datetime
import math
import plotly.graph_objects as go


class IBApi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.tickerArr = {}
        self.oneLowArr = {}     # low price array for 1 min
        self.oneHighArr = {}    # high price array for 1 min
        self.oneHistData = {}   # history data for 1 min
        self.oneHistVWAPData = {}  # history data for vwap calculation
        self.fiveLowArr = {}
        self.fiveHighArr = {}
        self.fiveHistData = {}
        self.fifteenHistData = {}
        self.fifteenLowArr = {}
        self.fifteenHighArr = {}
        self.sixthLowArr = {}
        self.sixthHighArr = {}
        self.sixthHistData = {}

    def historicalData(self, reqID, bar):
        # time_ = int(datetime.datetime.strptime(bar.date, "%Y%m%d %H:%M:%S").timestamp())
        realReqId = reqID // 5

        if reqID % 5 == 0:
            if realReqId not in self.oneHistData:
                self.oneHistData[realReqId] = [
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume}]
            else:
                self.oneHistData[realReqId].append(
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume})
        if reqID % 5 == 1:
            if realReqId not in self.fiveHistData:
                self.fiveHistData[realReqId] = [
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume}]
            else:
                self.fiveHistData[realReqId].append(
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume})
        if reqID % 5 == 2:
            if realReqId not in self.fifteenHistData:
                self.fifteenHistData[realReqId] = [
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume}]
            else:
                self.fifteenHistData[realReqId].append(
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume})
        if reqID % 5 == 3:
            if realReqId not in self.sixthHistData:
                self.sixthHistData[realReqId] = [
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume}]
            else:
                self.sixthHistData[realReqId].append(
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume})
        # store 1 min historical data for vwap calculation
        if reqID % 5 == 4:
            if realReqId not in self.oneHistVWAPData:
                self.oneHistVWAPData[realReqId] = [
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume}]
            else:
                self.oneHistVWAPData[realReqId].append(
                    {"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close,
                     "volume": bar.volume})

    def historicalDataEnd(self, reqID: int, start: str, end: str):
        realReqId = reqID // 5

        if reqID % 5 == 0:
            dfData = pd.DataFrame(self.oneHistData[realReqId])
            analysisDF = calcTopBreakOut(dfData)
            if len(analysisDF.index) > 0:
                logFileName = 'TopBreakOut.csv'
                analysisDF.to_csv(logFileName)

        if self.tickerArr[realReqId]['histCallCount'] >= 4:
            print('realReqId: ', realReqId, ' ticker: ', tickers[realReqId])
            self.reqRealTimeBars(realReqId, usTechStk(tickers[realReqId]), 5, "TRADES", False, [])
        else:
            self.tickerArr[realReqId]['histCallCount'] = self.tickerArr[realReqId]['histCallCount'] + 1

    def realtimeBar(self, reqID: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqID, time_, open_, high, low, close, volume, wap, count)

        self.appendRealData(reqID, time_, high, low, open_, close, volume)

    def appendRealData(self, reqID, time_, high, low, open_, close, volume):
        dateStamp = datetime.datetime.fromtimestamp(time_)

        if time_ % 60 == 0:
            if len(self.oneHighArr[reqID]) > 0:
                high_ = np.max(self.oneHighArr[reqID])
            else:
                high_ = high
            if len(self.oneLowArr[reqID]) > 0:
                low_ = np.min(self.oneLowArr[reqID])
            else:
                low_ = high

            self.oneLowArr[reqID].clear()
            self.oneHighArr[reqID].clear()

            if reqID not in self.oneHistData:
                self.oneHistData[reqID] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
                self.oneHistVWAPData[reqID] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.oneHistData[reqID].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})
                self.oneHistVWAPData[reqID].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})

            self.analysisDataFrame(reqID, high, low, open_, close, volume, 1)
        else:
            if reqID not in self.oneLowArr:
                self.oneLowArr[reqID] = [low]
            else:
                self.oneLowArr[reqID].append(low)

            if reqID not in self.oneHighArr:
                self.oneHighArr[reqID] = [high]
            else:
                self.oneHighArr[reqID].append(high)

        if time_ % 300 == 0:
            if len(self.fiveHighArr[reqID]) > 0:
                high_ = np.max(self.fiveHighArr[reqID])
            else:
                high_ = high
            if len(self.fiveLowArr[reqID]) > 0:
                low_ = np.min(self.fiveLowArr[reqID])
            else:
                low_ = high

            self.fiveLowArr[reqID].clear()
            self.fiveHighArr[reqID].clear()

            if reqID not in self.fiveHistData:
                self.fiveHistData[reqID] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.fiveHistData[reqID].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})

            self.analysisDataFrame(reqID, high, low, open_, close, volume, 5)
        else:
            if reqID not in self.fiveLowArr:
                self.fiveLowArr[reqID] = [low]
            else:
                self.fiveLowArr[reqID].append(low)

            if reqID not in self.fiveHighArr:
                self.fiveHighArr[reqID] = [high]
            else:
                self.fiveHighArr[reqID].append(high)

        if time_ % 900 == 0:
            if len(self.fifteenHighArr[reqID]) > 0:
                high_ = np.max(self.fifteenHighArr[reqID])
            else:
                high_ = high
            if len(self.fifteenLowArr[reqID]) > 0:
                low_ = np.min(self.fifteenLowArr[reqID])
            else:
                low_ = high

            self.fifteenLowArr[reqID].clear()
            self.fifteenHighArr[reqID].clear()

            if reqID not in self.fiveHistData:
                self.fifteenHistData[reqID] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.fifteenHistData[reqID].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})

            self.analysisDataFrame(reqID, high, low, open_, close, volume, 15)
        else:
            if reqID not in self.fifteenLowArr:
                self.fifteenLowArr[reqID] = [low]
            else:
                self.fifteenLowArr[reqID].append(low)

            if reqID not in self.fifteenHighArr:
                self.fifteenHighArr[reqID] = [high]
            else:
                self.fifteenHighArr[reqID].append(high)

        if time_ % 3600 == 0:
            if len(self.sixthHighArr[reqID]) > 0:
                high_ = np.max(self.sixthHighArr[reqID])
            else:
                high_ = high
            if len(self.sixthLowArr[reqID]) > 0:
                low_ = np.min(self.sixthLowArr[reqID])
            else:
                low_ = high

            self.sixthLowArr[reqID].clear()
            self.sixthHighArr[reqID].clear()

            if reqID not in self.fiveHistData:
                self.sixthHistData[reqID] = [
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume}]
            else:
                self.sixthHistData[reqID].append(
                    {"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_,
                     "close": close, "volume": volume})

            self.analysisDataFrame(reqID, high, low, open_, close, volume, 60)
        else:
            if reqID not in self.sixthLowArr:
                self.sixthLowArr[reqID] = [low]
            else:
                self.sixthLowArr[reqID].append(low)

            if reqID not in self.sixthHighArr:
                self.sixthHighArr[reqID] = [high]
            else:
                self.sixthHighArr[reqID].append(high)

    def analysisDataFrame(self, reqID, high, low, open_, close, volume, timeFrame):
        firstTrade = self.tickerArr[reqID]['firstTrade']
        symbol = self.tickerArr[reqID]['symbol']

        if timeFrame == 1:
            dfData = pd.DataFrame(self.oneHistData[reqID])
        elif timeFrame == 5:
            dfData = pd.DataFrame(self.fiveHistData[reqID])
        elif timeFrame == 15:
            dfData = pd.DataFrame(self.fifteenHistData[reqID])
        elif timeFrame == 60:
            dfData = pd.DataFrame(self.sixthHistData[reqID])

        print("Ticker:", symbol, "| High:", round(high, 2), "| Low:", round(low, 2), "| Open:", round(open_, 2),
              "| Close:", round(close, 2), "| Volume:", round(volume, 2))

        # calculate and store trail stop values
        analysisDF = calcAtrTrailStop(dfData, initAtrPeriod, initAtrFactor, firstTrade)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_ATR_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)
            trailStopVal = analysisDF.tail(1)['trail'].values[0]
            print("Trail Stop: ", round(trailStopVal, 2))

        analysisDF = calcRSI(dfData)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_RSI_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)
            rsiVal = analysisDF.tail(1)['RSI'].values[0]
            print("RSI: ", round(rsiVal, 2))

        analysisDF = calcBollBnd(dfData)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_BB_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)
            bbVal = analysisDF.tail(1)['BB_width'].values[0]
            print("Bollinger Bands: ", round(bbVal, 2))

        analysisDF = calcIchimoku(dfData)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_ichimoku_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)
            tenkan_sen = analysisDF.tail(1)['tenkan_sen'].values[0]
            kijun_sen = analysisDF.tail(1)['kijun_sen'].values[0]
            senkou_span_a = analysisDF.tail(1)['senkou_span_a'].values[0]
            senkou_span_b = analysisDF.tail(1)['senkou_span_b'].values[0]
            chikou_span = analysisDF.tail(1)['chikou_span'].values[0]
            print("tenkan_sen: ", round(tenkan_sen, 2), "| kijun_sen: ", round(kijun_sen, 2),
                  "| senkou_span_a: ", round(senkou_span_a, 2), "| senkou_span_b: ", round(senkou_span_b, 2),
                  "| chikou_span: ", round(chikou_span, 2))

        analysisDF = calcTTMSqueeze(dfData)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_TTM_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)
            momo = analysisDF.tail(1)['momo'].values[0]
            print("Momo: ", momo)

        dfData = pd.DataFrame(dfData)
        analysisDF = calcTopBreakOut(dfData)
        if len(analysisDF.index) > 0:
            logFileName = symbol + '_' + repr(timeFrame) + '_TopBreakOut_' + self.tickerArr[reqID]['startTime'] + '.csv'
            analysisDF.to_csv(logFileName)

        if timeFrame == 1:
            dfData = pd.DataFrame(self.oneHistVWAPData[reqID])
            analysisDF = calcVWAP(dfData)
            if len(analysisDF.index) > 0:
                logFileName = symbol + '_' + repr(timeFrame) + '_VWAP_' + self.tickerArr[reqID]['startTime'] + '.csv'
                analysisDF.to_csv(logFileName)
                vwapVal = analysisDF.tail(1)['VWAP'].values[0]
                print('VWAP: ', round(vwapVal, 2))


def calcEMA(DF):
    df = DF.copy()

    df["MA_9"] = df["close"].ewm(span=9, min_periods=9).mean()
    df["MA_27"] = df["close"].ewm(span=27, min_periods=27).mean()
    df["MA_54"] = df["close"].ewm(span=54, min_periods=54).mean()

    df.dropna(inplace=True)
    return df


# function to calculate True Range, Average True Range, Trailing stop
def calcAtrTrailStop(DF, atrPeriod, atrFactor, firstTrade):
    df = DF.copy()

    df['h-l'] = abs(df['high'] - df['low'])  # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))  # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))  # Abs of difference between Low and previous period's close
    df['TR'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['ATR'] = df['TR'].ewm(alpha=(1 / atrPeriod), adjust=False).mean()

    for i in range(1, len(df)):
        loss = df.loc[i, 'ATR'] * atrFactor
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

    df.dropna(inplace=True)
    return df


# RSI calculation
def calcRSI(DF, n=14):
    df = DF.copy()

    df['delta'] = df['close'] - df['close'].shift(1)
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

    df.dropna(inplace=True)
    return df


# Bollinger Band calculation
def calcBollBnd(DF, n=20):
    df = DF.copy()

    df["MA"] = df['close'].ewm(span=n, min_periods=n).mean()
    df["BB_up"] = df["MA"] + 2 * df['close'].ewm(span=n, min_periods=n).std(
        ddof=0)  # ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - 2 * df['close'].ewm(span=n, min_periods=n).std(
        ddof=0)  # ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]

    df.dropna(inplace=True)
    return df


# Volume Weighted Average Price
def calcVWAP(DF, n=5):
    df = DF.copy()

    df['Avg'] = (df['high'] + df['low'] + df['close']) / 3
    df['Cum_Vol'] = df['volume'].cumsum()
    df["Vol_Price"] = df['volume'] * df['Avg']
    df["Vol_Price2"] = df['volume'] * df['Avg'] * df['Avg']
    df["Cum_VP"] = df["Vol_Price"].cumsum()
    df["Cum_VP2"] = df["Vol_Price2"].cumsum()
    df["VWAP"] = df['Cum_VP'] / df['Cum_Vol']

    for i in range(len(df)):
        vwap = df.loc[i, 'VWAP']
        df.loc[i, 'Dev'] = math.sqrt(max((df.loc[i, 'Cum_VP2'] / df.loc[i, 'Cum_Vol']) - (vwap * vwap), 0))

    df["VWAP_up1"] = df["VWAP"] + 1 * df["Dev"]
    df["VWAP_dn1"] = df["VWAP"] - 1 * df["Dev"]
    df["VWAP_up2"] = df["VWAP"] + 2 * df["Dev"]
    df["VWAP_dn2"] = df["VWAP"] - 2 * df["Dev"]

    df.dropna(inplace=True)
    return df


def calcIchimoku(DF):
    df = DF.copy()

    high_9 = df['high'].rolling(window=9).max()
    low_9 = df['low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['high'].rolling(window=26).max()
    low_26 = df['low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)

    high_52 = df['high'].rolling(window=52).max()
    low_52 = df['low'].rolling(window=52).min()
    df['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)
    df['chikou_span'] = df['close'].shift(-26)

    df.dropna(inplace=True)
    return df


# TTM Squeeze Calculation
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


def calcTopBreakOut(DF):
    df = DF.copy()

    buyEntry = 3
    sellEntry = 3
    buyExit = 20
    sellExit = 20

    atrLength = 50
    targetATRMulti = 1

    buyOrSell = 'buy'

    df['HH'] = df['high'].rolling(window=sellExit).max()
    df['LL'] = df['low'].rolling(window=buyExit).min()

    df['QB'] = df['high'].rolling(window=buyEntry).max()
    df['QS'] = df['low'].rolling(window=sellEntry).min()

    # ATR calculation
    df['h-l'] = abs(df['high'] - df['low'])                     # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))         # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))          # Abs of difference between Low and previous period's close
    df['TR'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)        # Max of H-L, H-PC, L-PC
    df['ATR'] = df['TR'].ewm(alpha=(1 / atrLength), adjust=False).mean()
    df['mATR'] = df['ATR'].rolling(window=atrLength).max()
    df['co'] = df.index > max(sellExit, buyExit)

    df.loc[1, 'pos'] = 0
    df.loc[1, 'EntryPr'] = np.NaN
    df.loc[1, 'BTarget'] = np.NaN
    df.loc[1, 'BTarget2'] = np.NaN

    for i in range(2, len(df)):
        if buyOrSell == 'buy':
            df.loc[i, 'Entry'] = df.loc[i-1, 'QB']
            df.loc[i, 'Exit'] = df.loc[i-1, 'LL']

            if df.loc[i, 'co'] and df.loc[i, 'high'] > df.loc[i-1, 'QB']:
                df.loc[i, 'pos'] = 1
            elif df.loc[i, 'low'] < df.loc[i-1, 'LL']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i-1, 'pos']

            if df.loc[i, 'high'] > df.loc[i-1, 'QB'] and df.loc[i, 'pos'] == 1 and df.loc[i-1, 'pos'] < 1:
                df.loc[i, 'EntryPr'] = df.loc[i-1, 'QB']
            elif df.loc[i, 'pos'] == 0:
                df.loc[i, 'EntryPr'] = np.NaN
            else:
                df.loc[i, 'EntryPr'] = df.loc[i-1, 'EntryPr']

            if df.loc[i, 'pos'] == 1 and df.loc[i-1, 'pos'] < 1:
                df.loc[i, 'BTarget'] = df.loc[i, 'EntryPr'] + targetATRMulti * 2 * df.loc[i, 'mATR']
                df.loc[i, 'BTarget2'] = df.loc[i, 'EntryPr'] + 2 * targetATRMulti * 2 * df.loc[i, 'mATR']
            elif df.loc[i, 'pos'] == 1:
                df.loc[i, 'BTarget'] = df.loc[i-1, 'BTarget']
                df.loc[i, 'BTarget2'] = df.loc[i-1, 'BTarget2']
            else:
                df.loc[i, 'BTarget'] = np.NaN
                df.loc[i, 'BTarget2'] = np.NaN

            if (i > buyExit) and df.loc[i, 'EntryPr'] != np.NaN and (df.loc[i, 'LL'] < df.loc[i, 'EntryPr']):
                df.loc[i, 'EntryLine'] = df.loc[i, 'EntryPr']
            else:
                df.loc[i, 'EntryLine'] = np.NaN
            
            if i > buyExit and df.loc[i, 'EntryPr'] != np.NaN:
                df.loc[i, 'TradeRisk'] = (df.loc[i, 'EntryPr'] - df.loc[i, 'LL']) / df.loc[i, 'mATR']

            if df.loc[i, 'co']:
                df.loc[i, 'pBTarget'] = df.loc[i, 'BTarget']
                df.loc[i, 'pBTarget2'] = df.loc[i, 'BTarget2']
                df.loc[i, 'pEntryLine'] = df.loc[i, 'EntryLine']
            else:
                df.loc[i, 'pBTarget'] = np.NaN
                df.loc[i, 'pBTarget2'] = np.NaN
                df.loc[i, 'pEntryLine'] = np.NaN
        elif buyOrSell == 'sell':
            df.loc[i, 'Entry'] = df.loc[i-1, 'QS']
            df.loc[i, 'Exit'] = df.loc[i-1, 'HH']

            if df.loc[i-1, 'QS'] != np.NaN and df.loc[i, 'co'] and df.loc[i, 'low'] < df.loc[i-1, 'QS']:
                df.loc[i, 'pos'] = -1
            elif df.loc[i-1, 'high'] > df.loc[i-2, 'HH']:
                df.loc[i, 'pos'] = 0
            else:
                df.loc[i, 'pos'] = df.loc[i-1, 'pos']

            if df.loc[i, 'low'] > df.loc[i-1, 'QS'] and df.loc[i, 'pos'] == -1 and df.loc[i-1, 'pos'] > -1:
                df.loc[i, 'EntryPr'] = df.loc[i-1, 'QS']
            elif df.loc[i, 'pos'] == 0:
                df.loc[i, 'EntryPr'] = np.NaN
            else:
                df.loc[i, 'EntryPr'] = df.loc[i-1, 'EntryPr']

            if df.loc[i, 'pos'] == -1 and df.loc[i-1, 'pos'] > -1:
                df.loc[i, 'BTarget'] = df.loc[i, 'EntryPr'] - targetATRMulti * 2 * df.loc[i, 'mATR']
                df.loc[i, 'BTarget2'] = df.loc[i, 'EntryPr'] - 2 * targetATRMulti * 2 * df.loc[i, 'mATR']
            elif df.loc[i, 'pos'] == -1:
                df.loc[i, 'BTarget'] = df.loc[i-1, 'BTarget']
                df.loc[i, 'BTarget2'] = df.loc[i-1, 'BTarget2']
            else:
                df.loc[i, 'BTarget'] = np.NaN
                df.loc[i, 'BTarget2'] = np.NaN

            if i > sellExit and df.loc[i, 'EntryPr'] != np.NaN and df.loc[i, 'HH'] > df.loc[i, 'EntryPr']:
                df.loc[i, 'EntryLine'] = df.loc[i, 'EntryPr']
            else:
                df.loc[i, 'EntryLine'] = np.NaN

            if df.loc[i, 'HH'] != np.NaN and df.loc[i, 'EntryPr'] != np.NaN:
                df.loc[i, 'TradeRisk'] = (df.loc[i, 'HH'] - df.loc[i, 'EntryPr']) / df.loc[i, 'mATR']

    candlestick = go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])
    if buyOrSell == 'buy':
        entry = go.Scatter(x=df['date'], y=df['Entry'], name='Entry', line={'color': 'green'})
    else:
        entry = go.Scatter(x=df['date'], y=df['Entry'], name='Entry', line={'color': 'red'})
    exitLine = go.Scatter(x=df['date'], y=df['Exit'], name='Exit Line', line={'color': 'cyan'})
    entryLine = go.Scatter(x=df['date'], y=df['pEntryLine'], name='Entry Line', line={'color': 'white'})
    bTargetLine = go.Scatter(x=df['date'], y=df['BTarget'], name='BTarget Line', line={'color': 'yellow'})
    bTarget2Line = go.Scatter(x=df['date'], y=df['BTarget2'], name='BTarget2 Line', line={'color': 'magenta'})

    fig = go.Figure(data=[candlestick, entry, exitLine, entryLine, bTargetLine, bTarget2Line])
    fig.layout.xaxis.type = 'category'
    fig.layout.xaxis.rangeslider.visible = False
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
    initAtrFactor = input("Enter ATR factor: ")
    if initAtrFactor.isdigit():
        initAtrFactor = int(initAtrFactor)
        break

histReqId = 0
for ticker in tickers:
    reqId = tickers.index(ticker)
    if reqId not in app.tickerArr:
        app.tickerArr[reqId] = {"symbol": ticker, "firstTrade": 'long', 'startTime': datetime.datetime.now().strftime('%m%d_%H%M%S'), 'histCallCount': 0}
        app.reqHistoricalData(reqId=histReqId, contract=usTechStk(ticker), endDateTime='', durationStr='2 D',
                              barSizeSetting='1 min', whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1,
                              chartOptions=[])
        histReqId = histReqId + 1
        app.reqHistoricalData(reqId=histReqId, contract=usTechStk(ticker), endDateTime='', durationStr='2 D',
                              barSizeSetting='5 mins', whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1,
                              chartOptions=[])
        histReqId = histReqId + 1
        app.reqHistoricalData(reqId=histReqId, contract=usTechStk(ticker), endDateTime='', durationStr='2 D',
                              barSizeSetting='15 mins', whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1,
                              chartOptions=[])
        histReqId = histReqId + 1
        app.reqHistoricalData(reqId=histReqId, contract=usTechStk(ticker), endDateTime='', durationStr='2 D',
                              barSizeSetting='1 hour', whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1,
                              chartOptions=[])
        histReqId = histReqId + 1
        app.reqHistoricalData(reqId=histReqId, contract=usTechStk(ticker), endDateTime='', durationStr='1 D',
                              barSizeSetting='1 min', whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1,
                              chartOptions=[])
        histReqId = histReqId + 1

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()

