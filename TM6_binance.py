import collections
import sys
import threading
import pandas as pd
import datetime
import csv

from datetime import datetime
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *

from Strategies import Strategies


def timeFrameStr():
    if timeFrameSelection == '1':
        return '1'
    elif timeFrameSelection == '2':
        return '5'
    elif timeFrameSelection == '3':
        return '15'
    elif timeFrameSelection == '4':
        return '60'


def realTimeBar(msg):
    # data = msg['data']
    # candle = data['k']
    candle = msg['k']
    candleClosed = candle['x']
    if candleClosed:
        symbol = candle['s']
        ticker = symbol.lower()

        if statusArr[ticker]['tradeCount'] < maxOrderCount:
            if datetime.now() < endTimeDate:
                openTimeStr = datetime.fromtimestamp(candle['t'] / 1000).strftime("%Y%m%d %H:%M:%S")
                closeTimeStr = datetime.fromtimestamp(candle['T'] / 1000).strftime("%Y%m%d %H:%M:%S")

                if ticker not in histData:
                    histData[ticker] = [{"Open_Time": openTimeStr, "Open": float(candle['o']), "High": float(candle['h']),
                                         "Low": float(candle['l']), "Close": float(candle['c']), "Volume": float(candle['v']),
                                         'Close_Time': closeTimeStr}]
                else:
                    histData[ticker].append({"Open_Time": openTimeStr, "Open": float(candle['o']), "High": float(candle['h']),
                                             "Low": float(candle['l']), "Close": float(candle['c']), "Volume": float(candle['v']),
                                             'Close_Time': closeTimeStr})
                print("Coin= ", symbol, "Open Time =", openTimeStr, "Close =", candle['c'], "Open =", candle['o'], "High =", candle['h'], "Low =", candle['l'])
                analysisDataFrame(ticker, candle['c'])
            else:
                print('Time is up for', symbol)
                endTrade(ticker)
        else:
            print('Max number of trades for', symbol, 'has been reached')
            endTrade(ticker)


def analysisDataFrame(ticker, close):
    dfData = pd.DataFrame(histData[ticker])

    if strategySelection == '1':
        try:
            atrDF = Strategies.ATR(dfData, close, bias=biasOptions[biasSelection])

            if len(atrDF.index) > 0:
                logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_ATR_' + statusArr[ticker]['startTime'] + '.csv'
                atrDF.to_csv(logFileName)

                atrVal = atrDF.tail(1)['Trail'].values[0]
                ema = atrDF.tail(1)['EMA_200'].values[0]
                Zone = atrDF.tail(1)['Zone'].values[0]
                signal = atrDF.tail(1)['ACTION'].values[0]
                distance = atrDF.tail(1)['ATR_dist'].values[0]
                print('Symbol =', ticker, 'ATR value =', atrVal, 'EMA =', ema, 'Zone =', Zone, 'Signal =', signal, 'Distance = ', distance)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'close':
                        print("Received Close Signal")
                        orderAction(signal, ticker, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received Short Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'cover':
                        print("Received Cover Signal")
                        orderAction(signal, ticker, close)
        except KeyError:
            e = sys.exc_info()[0]
            print(ticker, 'ATR exception: ', e)
    elif strategySelection == '2':
        try:
            emaDF = Strategies.EMA(dfData, bias=biasOptions[biasSelection])

            if len(emaDF.index) > 0:
                logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_EMA_' + statusArr[ticker]['startTime'] + '.csv'
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

                print('Symbol =', ticker, 'ema9 =', ema9, 'ema27 =', ema27, 'ema54 =', ema54, 'MA_9_dist =', MA_9_dist, 'MA_27_dist =',
                      MA_27_dist, 'MA_54_dist =', MA_54_dist, 'MA_fast =', MA_fast, 'MA_slow =', MA_slow, 'MA_med =', MA_med)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'close':
                        print("Received Close Signal")
                        orderAction(signal, ticker, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received Short Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'cover':
                        print("Received Cover Signal")
                        orderAction(signal, ticker, close)
        except KeyError:
            e = sys.exc_info()[0]
            print(ticker, 'EMA exception: ', e)
    elif strategySelection == '3':
        try:
            vwapDF = Strategies.VWAP(dfData, bias=biasOptions[biasSelection])

            if len(vwapDF.index) > 0:
                logFileName = 'log/' + ticker + '_VWAP_' + statusArr[ticker]['startTime'] + '.csv'
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

                print('Symbol =', ticker, "ema9 =", ema9, "ema27 =", ema27, "signal =", signal, "VWAP distance =", VWAP_distance,
                      "Zone =", Zone, "MA_ratio", MA_ratio, "Cum_vol =", Cum_vol, "VWAP =", VWAP, "VWAP up1 =",
                      VWAP_up1, "VWAP_dn1 =", VWAP_dn1)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'close':
                        print("Received Close Signal")
                        orderAction(signal, ticker, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received Short Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'cover':
                        print("Received Cover Signal")
                        orderAction(signal, ticker, close)
        except KeyError:
            e = sys.exc_info()[0]
            print(ticker, 'VWAP exception: ', e)
    elif strategySelection == '4':
        try:
            ttmDF = Strategies.TTMSqueeze(dfData, bias=biasOptions[biasSelection])

            if len(ttmDF.index) > 0:
                logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_TTM_' + statusArr[ticker]['startTime'] + '.csv'
                ttmDF.to_csv(logFileName)

                squeeze = ttmDF.tail(1)['squeeze'].values[0]
                momentum = ttmDF.tail(1)['momentum'].values[0]
                signal = ttmDF.tail(1)['ACTION'].values[0]
                ema9 = ttmDF.tail(1)['MA_9'].values[0]
                ema27 = ttmDF.tail(1)['MA_27'].values[0]
                momo = ttmDF.tail(1)['momo'].values[0]
                dir = ttmDF.tail(1)['dir'].values[0]
                val = ttmDF.tail(1)['val'].values[0]

                print('Symbol =', ticker, "squeeze =", squeeze, 'momo =', momo, 'dir =', dir, 'val =', val, "momentum =", momentum,
                      "signal =", signal, "ema9 =", ema9, "ema27 =", ema27)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'close':
                        print("Received Close Signal")
                        orderAction(signal, ticker, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received Short Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'cover':
                        print("Received Cover Signal")
                        orderAction(signal, ticker, close)
        except KeyError:
            e = sys.exc_info()[0]
            print(ticker, 'TTMSqueeze except: ', e)
    elif strategySelection == '5':
        try:
            analyseDF = Strategies.TopBreakOut(dfData, bias=biasOptions[biasSelection])

            if len(analyseDF.index) > 0:
                logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_TopBreakOut_' + statusArr[ticker]['startTime'] + '.csv'
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
                      "Entry Ratio = ", Entry, "Exit Ratio = ", Exit, "Distance = ", distance)

                if biasOptions[biasSelection] == 'Long':
                    if signal == 'buy':
                        print("Received Buy Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'close':
                        print("Received Close Signal")
                        orderAction(signal, ticker, close)
                if biasOptions[biasSelection] == 'Short':
                    if signal == 'sell':
                        print("Received Short Signal")
                        orderAction(signal, ticker, close)
                    if signal == 'cover':
                        print("Received Cover Signal")
                        orderAction(signal, ticker, close)
        except KeyError:
            e = sys.exc_info()[0]
            print(ticker, 'TopBreakOut except: ', e)


def order(side, quantity, ticker, order_type=ORDER_TYPE_MARKET, endTrade=False):
    try:
        # orderRes = client.create_order(symbol=ticker, side=side, type=order_type, quantity=quantity)
        orderRes = client.create_test_order(symbol=ticker.upper(), side=side, type=order_type, quantity=quantity)
        if orderRes['status'] == 'FILLED':
            statusArr[ticker]['orderPlaced'] = False
            statusArr[ticker]['tradeCount'] = statusArr[ticker]['tradeCount'] + 1
            if endTrade:
                bm.stop_socket(statusArr[ticker]['conn'])
                print(ticker, 'trade ended')
        else:
            print(orderRes['status'])
    except Exception as e:
        print("create_order exception occured - {}".format(e))


def getLastSymbolCount(asset):
    accountInfo = client.get_account()
    balances = accountInfo['balances']
    for balanceTtem in balances:
        if balanceTtem['asset'] == asset:
            return float(balanceTtem['free'])
    return 0


def getBaseAsset(symbol):
    exchangeInfos = client.get_exchange_info()
    symbolArr = exchangeInfos['symbols']

    for symbolItem in symbolArr:
        if symbolItem['symbol'] == symbol.upper():
            return symbolItem['baseAsset']
    return ''


def get_round_precision(ticker):
    info = client.get_symbol_info(ticker)
    f = [i["stepSize"] for i in info["filters"] if i["filterType"] == "LOT_SIZE"][0]
    print(f)
    prec = 0
    for i in range(10):
        if f[i] == "1":
            break
        if f[i] == ".":
            continue
        else:
            prec += 1
    return prec


def orderAction(action, ticker, price):
    statusObj = statusArr[ticker]
    if not statusArr[ticker]['orderPlaced']:
        if statusObj['tradeCount'] < maxOrderCount:
            if (action == 'buy') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'close'):
                print(ticker, "buy order")
                # count = 1000 / price
                places = get_round_precision(ticker)
                dollaramt = 40
                count = (round(dollaramt / float(price), places))
                print("count =", count)
                statusArr[ticker]['orderPlaced'] = True
                statusArr[ticker]['lastAction'] = 'buy'
                order(SIDE_BUY, count, ticker)
            if (action == 'close') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'buy'):
                print(ticker, "closing order")
                count = getLastSymbolCount(statusArr[ticker]['baseAsset'])
                if count != 0:
                    statusArr[ticker]['lastAction'] = 'close'
                    statusArr[ticker]['orderPlaced'] = True
                    order(SIDE_SELL, abs(count), ticker)
            if (action == 'sell') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'cover'):
                print(ticker, "sell order")
                count = 30 / price
                statusArr[ticker]['lastAction'] = 'sell'
                statusArr[ticker]['orderPlaced'] = True
                order(SIDE_SELL, count, ticker)
            if (action == 'cover') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'sell'):
                print(ticker, "covering order")
                count = getLastSymbolCount(statusObj['baseAsset'])
                if count != 0:
                    statusArr[ticker]['lastAction'] = 'cover'
                    statusArr[ticker]['orderPlaced'] = True
                    order(SIDE_BUY, abs(count), ticker)
        else:
            print('Max number of trades has been reached')


def startScan():
    percentChangeArr = []
    pickedTickers = []
    print('Scan started: ', symbols)
    if len(symbols) > 5:
        for symbol in symbols:
            candlesticks = client.get_historical_klines(symbol.upper(), Client.KLINE_INTERVAL_1HOUR, "1 day ago")
            lastClose = float(candlesticks[-1][4])
            firstClose = float(candlesticks[0][4])

            if firstClose != 0 and lastClose != 0:
                if biasSelection == '1':  # Percent Gain for Long
                    percentChange = 100 * (lastClose - firstClose) / firstClose
                elif biasSelection == '2':  # Percent Lose for Short
                    percentChange = 100 * (firstClose - lastClose) / firstClose
                percentChangeArr.append({'ticker': symbol.lower(), 'percentChange': percentChange})

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

        percentChangeArr.sort(key=sortByPercentChange, reverse=True)
        print('Sort by percent change:', percentChangeArr)

        if not advancedFilter:
            if len(percentChangeArr) > 5:
                for arrayIndex in range(0, 5):
                    pickedTickers.append(percentChangeArr[arrayIndex]['ticker'])
            else:
                for ticker in percentChangeArr:
                    pickedTickers.append(ticker['ticker'])

            for symbol in pickedTickers:
                ticker = symbol.lower()
                if strategySelection == '3':
                    candlesticks = client.get_historical_klines(ticker.upper(), interval, "1 day ago")
                else:
                    candlesticks = client.get_historical_klines(ticker.upper(), interval, "2 day ago")
                print('Received Historical data for', ticker)

                for candlestick in candlesticks:
                    openTimeStamp = datetime.fromtimestamp(candlestick[0] / 1000).strftime("%Y%m%d %H:%M:%S")
                    closeTimeStamp = datetime.fromtimestamp(candlestick[6] / 1000).strftime("%Y%m%d %H:%M:%S")

                    if ticker not in histData:
                        histData[ticker] = [
                            {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                             'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                             'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp}]
                    else:
                        histData[ticker].append(
                            {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                             'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                             'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp})

        else:
            tmpPickedTickers = []

            if len(percentChangeArr) > 5:
                for arrayIndex in range(0, 5):
                    tmpPickedTickers.append(percentChangeArr[arrayIndex]['ticker'])
            else:
                for ticker in percentChangeArr:
                    tmpPickedTickers.append(ticker['ticker'])

            atrFilterTickers = []
            for ticker in tmpPickedTickers:
                pickedTickers = []

                if strategySelection == '3':
                    candlesticks = client.get_historical_klines(ticker.upper(), interval, "1 day ago")
                else:
                    candlesticks = client.get_historical_klines(ticker.upper(), interval, "2 day ago")
                print('Received Historical data for', ticker)

                for candlestick in candlesticks:
                    openTimeStamp = datetime.fromtimestamp(candlestick[0] / 1000).strftime("%Y%m%d %H:%M:%S")
                    closeTimeStamp = datetime.fromtimestamp(candlestick[6] / 1000).strftime("%Y%m%d %H:%M:%S")

                    if ticker not in histData:
                        histData[ticker] = [
                            {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                             'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                             'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp}]
                    else:
                        histData[ticker].append(
                            {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                             'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                             'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp})
                dfData = pd.DataFrame(histData[ticker])
                close = dfData.tail(1)['Close'].values[0]

                if strategySelection == '1':  # ATR

                    try:
                        atrDF = Strategies.ATR(dfData, close, biasOptions[biasSelection])
                        atrZone = atrDF.tail(1)['Zone'].values[0]
                        atrDist = float(atrDF.tail(1)['ATR_dist'].values[0])
                        print("Ticker ",ticker, "last close = ", close, "Zone= ", atrZone, "ATR dist ", atrDist)
                        #print(atrDF)
                        if (biasSelection == '1' and atrZone == 'below ATR') or (biasSelection == '2' and atrZone == 'above ATR'):
                            atrFilterTickers.append({'ticker': ticker, 'atrDist': atrDist})
                            print("ATR filter tickers ", atrFilterTickers)
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'ATR except: ', e)
                        continue

                    if len(atrFilterTickers) > 0:
                        atrFilterTickers.sort(key=sortByATRDistance)
                        print (len(atrFilterTickers))

                        if len(atrFilterTickers) > 5:
                            for arrayIndex in range(0, 5):
                                pickedTickers.append(atrFilterTickers[arrayIndex]['ticker'])
                        else:
                            for tickerObj in atrFilterTickers:
                                pickedTickers.append(tickerObj['ticker'])
                    print("ATR picked tickers ", pickedTickers)
                elif strategySelection == '2':  # EMA
                    try:
                        emaDF = Strategies.EMA(dfData, biasOptions[biasSelection])
                        zone = emaDF.tail(1)['Zone'].values[0]

                        if (biasSelection == '1' and zone == 'Squeeze In') or (biasSelection == '2' and zone == 'Squeeze Out'):
                            pickedTickers.append(ticker)
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'EMA except: ', e)
                        continue
                elif strategySelection == '3':  # VWAP
                    vwapFilterTickers = []

                    try:
                        vwapDF = Strategies.VWAP(dfData, biasOptions[biasSelection])
                        vwapVal = vwapDF.tail(1)['VWAP'].values[0]
                        vwapDist = float(vwapDF.tail(1)['VWAP_distance'].values[0])
                        close = vwapDF.tail(1)['Close'].values[0]

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
                                pickedTickers.append(vwapFilterTickers[arrayIndex]['ticker'])
                        else:
                            for tickerObj in vwapFilterTickers:
                                pickedTickers.append(tickerObj['ticker'])
                elif strategySelection == '4':  # TTM Squeeze
                    ttmFilterTickers = []

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
                                pickedTickers.append(ttmFilterTickers[arrayIndex]['ticker'])
                        else:
                            for tickerObj in ttmFilterTickers:
                                pickedTickers.append(tickerObj['ticker'])
                elif strategySelection == '5':  # Top Break out
                    topFilterTickers = []

                    try:
                        topDF = Strategies.TopBreakOut(dfData, bias=biasOptions[biasSelection])
                        distance = float(topDF.tail(1)['Distance'].values[0])
                        direct = float(topDF.tail(1)['pos'].values[0])
                        if (biasSelection == '1' and direct == 0) or (
                                biasSelection == '2' and direct == 0):
                            topFilterTickers.append({'ticker': ticker, 'distance': distance})
                    except KeyError:
                        e = sys.exc_info()[0]
                        print(ticker, 'TopBreakOut except: ', e)

                    if len(topFilterTickers) > 0:
                        topFilterTickers.sort(key=sortByDistance)
                        if len(topFilterTickers) > 5:
                            for arrayIndex in range(0, 5):
                                pickedTickers.append(topFilterTickers[arrayIndex]['ticker'])
                        else:
                            for tickerObj in topFilterTickers:
                                pickedTickers.append(tickerObj['ticker'])

        if len(pickedTickers) > 0:
            print('picked: ', pickedTickers)
            startScreen(pickedTickers)
        else:
            print('No picked tickers')
    else:

        for symbol in symbols:
            ticker = symbol.lower()
            if strategySelection == '3':
                candlesticks = client.get_historical_klines(ticker.upper(), interval, "1 day ago")
            else:
                candlesticks = client.get_historical_klines(ticker.upper(), interval, "2 day ago")
            print('Received Historical data for', ticker)

            for candlestick in candlesticks:
                openTimeStamp = datetime.fromtimestamp(candlestick[0] / 1000).strftime("%Y%m%d %H:%M:%S")
                closeTimeStamp = datetime.fromtimestamp(candlestick[6] / 1000).strftime("%Y%m%d %H:%M:%S")

                if ticker not in histData:
                    histData[ticker] = [
                        {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                         'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                         'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp}]
                else:
                    histData[ticker].append(
                        {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[2]),
                         'Low': float(candlestick[3]), 'Close': float(candlestick[4]),
                         'Volume': float(candlestick[5]), 'Close_Time': closeTimeStamp})
        startScreen(symbols)

def startScreen(pickedTickers):
    symbolStrArr = []
    exchangeInfos = client.get_exchange_info()
    symbolArr = exchangeInfos['symbols']

    for symbol in pickedTickers:
        for symbolItem in symbolArr:
            if symbolItem['symbol'] == symbol.upper():
                baseAsset = symbolItem['baseAsset']
                lsymbol = symbol.lower()
                symbolStrArr.append(lsymbol + '@kline_' + timeFrameOptions[timeFrameSelection])

                free = getLastSymbolCount(baseAsset)
                lastAction = 'start'
                if biasOptions[biasSelection] == 'Long':
                    lastAction = 'close'
                    if free > 0:
                        lastAction = 'buy'
                elif biasOptions[biasSelection] == 'Short':
                    lastAction = 'cover'
                    if free < 0:
                        lastAction = 'sell'
                conn = bm.start_kline_socket(lsymbol, realTimeBar)
                statusArr[lsymbol] = {'lastAction': lastAction, 'orderPlaced': False, 'tradeCount': 0,
                                      'baseAsset': baseAsset, 'conn': conn,
                                      'startTime': datetime.now().strftime('%m%d_%H%M%S')}
                break

    # bm.start_multiplex_socket(symbolStrArr, realTimeBar)
    bm.start()


def endTrade(ticker):
    count = getLastSymbolCount(statusArr[ticker]['baseAsset'])
    if count > 0:
        order(SIDE_SELL, abs(count), ticker, endTrade=True)
    elif count < 0:
        order(SIDE_BUY, abs(count), ticker, endTrade=True)
    else:
        bm.stop_socket(statusArr[ticker]['conn'])
        print(ticker, 'trade ended')


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

timeFrameOptions = collections.OrderedDict()
timeFrameOptions["1"] = "1m"
timeFrameOptions["2"] = "5m"
timeFrameOptions["3"] = "15m"
timeFrameOptions["4"] = "1h"
# time frame selection except VWAP
if strategySelection != '3':
    while True:
        options = timeFrameOptions.keys()
        for entry in options:
            print(entry + ")\t" + timeFrameOptions[entry])
        timeFrameSelection = input("Select timeframe: ")
        if timeFrameSelection == '1':
            interval = Client.KLINE_INTERVAL_1MINUTE
            print('')
            break
        if timeFrameSelection == '2':
            interval = Client.KLINE_INTERVAL_5MINUTE
            print('')
            break
        if timeFrameSelection == '3':
            interval = Client.KLINE_INTERVAL_15MINUTE
            print('')
            break
        if timeFrameSelection == '4':
            interval = Client.KLINE_INTERVAL_1HOUR
            print('')
            break
else:
    timeFrameSelection = '1'
    interval = Client.KLINE_INTERVAL_1MINUTE

# Enter start time
while True:
    startOption = input('Start now?(Y/N)')

    if startOption.lower() == 'y':
        print('')
        break
    elif startOption.lower() == 'n':
        startTimeStr = input("Enter a start time in MM/DD/YYYY HH:MM format: ")
        try:
            startTimeDate = datetime.strptime(startTimeStr, '%m/%d/%Y %H:%M')
            if startTimeDate > datetime.now():
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
        endTimeDate = datetime.max
        print('')
        break
    elif endOption.lower() == 'n':
        endTimeStr = input("Enter an end time in MM/DD/YYYY HH:MM format: ")
        try:
            endTimeDate = datetime.strptime(endTimeStr, '%m/%d/%Y %H:%M')
            if endTimeDate > datetime.now():
                print('')
                break
            else:
                print('Invalid time')
        except ValueError:
            print("Incorrect format. It should be MM/DD/YYYY HH:MM")

symbols = []
inputOptions = collections.OrderedDict()
inputOptions['1'] = 'Input list from CSV'
inputOptions['2'] = 'Input list from user'
while True:
    options = inputOptions.keys()
    for entry in options:
        print(entry + ")\t" + inputOptions[entry])
    inputMethodSelection = input("Select Input Method: ")
    if inputMethodSelection == '1':
        filenames = input("Enter csv filenames space-separated: ").split()
        if len(filenames) > 0:
            for filename in filenames:
                csvFile = 'tickers/' + filename + '.csv'
                with open(csvFile) as f:
                    reader = csv.DictReader(f, delimiter=',')
                    for row in reader:
                        symbols.append(row['Token'])
            print('')
            break
        else:
            print('No tickers!!!')
    elif inputMethodSelection == '2':
        symbols = input("Enter multiple symbols space-separated: ").split()
        if len(symbols) > 0:
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

API_KEY = 'Jqlm79EwoDKltuw0WpITRlA6ExInFBY9xUPpSiwTXrri2ylXRNV82Ecf48Zxekmm'
API_SECRET = 'LnRW2W8Sw8rbRXWIQT2VI5a3vBGbsku1Nl6yeetGHMIjr0o2gBC6uaILZKCwQQKq'
client = Client(API_KEY, API_SECRET, tld='us')

statusArr = {}
histData = {}
bm = BinanceSocketManager(client)

if startOption.lower() == 'y':
    startScan()
elif startOption.lower() == 'n':
    delay = (startTimeDate - datetime.now()).total_seconds()
    print('delay: ', delay)
    threading.Timer(delay, startScan).start()
