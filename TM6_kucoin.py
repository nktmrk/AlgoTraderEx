import collections
import sys
import pandas as pd
import datetime
import csv
import time
import asyncio

from datetime import datetime
from Strategies import Strategies
from kucoin.ws_client import KucoinWsClient
from kucoin.client import WsToken
from kucoin.client import Trade
from kucoin.client import User
from kucoin.client import Market
from kucoin.client import Margin


async def main():
    global loop

    def timeFrameStr():
        if timeFrameSelection == '1':
            return '1'
        elif timeFrameSelection == '2':
            return '5'
        elif timeFrameSelection == '3':
            return '15'
        elif timeFrameSelection == '4':
            return '60'

    def analysisDataFrame(ticker, close):
        dfData = pd.DataFrame(histData[ticker])

        if strategySelection == '1':
            try:
                atrDF = Strategies.ATR(dfData, close, bias=biasOptions[biasSelection])

                if len(atrDF.index) > 0:
                    logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_ATR_' + statusArr[ticker][
                        'startTime'] + '.csv'
                    atrDF.to_csv(logFileName)

                    atrVal = atrDF.tail(1)['Trail'].values[0]
                    ema = atrDF.tail(1)['EMA_200'].values[0]
                    Zone = atrDF.tail(1)['Zone'].values[0]
                    signal = atrDF.tail(1)['ACTION'].values[0]
                    distance = atrDF.tail(1)['ATR_dist'].values[0]
                    print('Symbol =', ticker, 'ATR value =', atrVal, 'EMA =', ema, 'Zone =', Zone, 'Signal =', signal,
                          'Distance = ', distance)

                    if biasOptions[biasSelection] == 'Long' and (signal == 'buy' or signal == 'close'):
                        orderAction(signal, ticker, close)
                    if biasOptions[biasSelection] == 'Short' and (signal == 'sell' or signal == 'cover'):
                        orderAction(signal, ticker, close)
            except KeyError:
                e = sys.exc_info()[0]
                print(ticker, 'ATR exception: ', e)
        elif strategySelection == '2':
            try:
                emaDF = Strategies.EMA(dfData, bias=biasOptions[biasSelection])

                if len(emaDF.index) > 0:
                    logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_EMA_' + statusArr[ticker][
                        'startTime'] + '.csv'
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

                    print('Symbol =', ticker, 'ema9 =', ema9, 'ema27 =', ema27, 'ema54 =', ema54, 'MA_9_dist =',
                          MA_9_dist, 'MA_27_dist =', MA_27_dist, 'MA_54_dist =', MA_54_dist, 'MA_fast =', MA_fast, 'MA_slow =', MA_slow,
                          'MA_med =', MA_med)

                    if biasOptions[biasSelection] == 'Long' and (signal == 'buy' or signal == 'close'):
                        orderAction(signal, ticker, close)
                    if biasOptions[biasSelection] == 'Short' and (signal == 'sell' or signal == 'cover'):
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

                    print('Symbol =', ticker, "ema9 =", ema9, "ema27 =", ema27, "signal =", signal, "VWAP distance =",
                          VWAP_distance, "Zone =", Zone, "MA_ratio", MA_ratio, "Cum_vol =", Cum_vol, "VWAP =", VWAP, "VWAP up1 =",
                          VWAP_up1, "VWAP_dn1 =", VWAP_dn1)

                    if biasOptions[biasSelection] == 'Long' and (signal == 'buy' or signal == 'close'):
                        orderAction(signal, ticker, close)
                    if biasOptions[biasSelection] == 'Short' and (signal == 'sell' or signal == 'cover'):
                        orderAction(signal, ticker, close)
            except KeyError:
                e = sys.exc_info()[0]
                print(ticker, 'VWAP exception: ', e)
        elif strategySelection == '4':
            try:
                ttmDF = Strategies.TTMSqueeze(dfData, bias=biasOptions[biasSelection])

                if len(ttmDF.index) > 0:
                    logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_TTM_' + statusArr[ticker][
                        'startTime'] + '.csv'
                    ttmDF.to_csv(logFileName)

                    squeeze = ttmDF.tail(1)['squeeze'].values[0]
                    momentum = ttmDF.tail(1)['momentum'].values[0]
                    signal = ttmDF.tail(1)['ACTION'].values[0]
                    ema9 = ttmDF.tail(1)['MA_9'].values[0]
                    ema27 = ttmDF.tail(1)['MA_27'].values[0]
                    momo = ttmDF.tail(1)['momo'].values[0]
                    dir = ttmDF.tail(1)['dir'].values[0]
                    val = ttmDF.tail(1)['val'].values[0]

                    print('Symbol =', ticker, "squeeze =", squeeze, 'momo =', momo, 'dir =', dir, 'val =', val,
                          "momentum =", momentum, "signal =", signal, "ema9 =", ema9, "ema27 =", ema27)

                    if biasOptions[biasSelection] == 'Long' and (signal == 'buy' or signal == 'close'):
                        orderAction(signal, ticker, close)
                    if biasOptions[biasSelection] == 'Short' and (signal == 'sell' or signal == 'cover'):
                        orderAction(signal, ticker, close)
            except KeyError:
                e = sys.exc_info()[0]
                print(ticker, 'TTMSqueeze except: ', e)
        elif strategySelection == '5':
            try:
                analyseDF = Strategies.TopBreakOut(dfData, bias=biasOptions[biasSelection])

                if len(analyseDF.index) > 0:
                    logFileName = 'log/' + ticker + '_' + timeFrameStr() + '_TopBreakOut_' + statusArr[ticker][
                        'startTime'] + '.csv'
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

                    if biasOptions[biasSelection] == 'Long' and (signal == 'buy' or signal == 'close'):
                        orderAction(signal, ticker, close)
                    if biasOptions[biasSelection] == 'Short' and (signal == 'sell' or signal == 'cover'):
                        orderAction(signal, ticker, close)
            except KeyError:
                e = sys.exc_info()[0]
                print(ticker, 'TopBreakOut except: ', e)

    async def order(side, quantity, ticker, endTrade=False):
        try:
            tradeClient.create_market_margin_order(symbol=ticker.upper(), side=side, size=quantity)
            # tradeClient.create_limit_margin_order(symbol=ticker.upper(), side=side, size=quantity)
            statusArr[ticker]['orderPlaced'] = False
            statusArr[ticker]['tradeCount'] = statusArr[ticker]['tradeCount'] + 1

            if endTrade:
                await ws_client.unsubscribe('/market/candles:' + ticker + '_' + timeFrameOptions[timeFrameSelection])
                print(ticker, 'trade ended')
        except Exception as e:
            print("create_order exception occured - {}".format(e))

    def getLastSymbolCount(asset):
        accounts = userClient.get_account_list()
        for accountItem in accounts:
            if accountItem['type'] == 'margin' and accountItem['currency'] == asset:
                return float(accountItem['balance'])
        userClient.create_account(account_type='margin', currency=asset)
        return 0

    def getBaseAsset(symbol):
        arr = symbol.split('-')
        if len(arr) > 0:
            return arr[0]
        return ''

    def orderAction(action, ticker, price):
        statusObj = statusArr[ticker]
        if not statusArr[ticker]['orderPlaced']:
            if (action == 'buy') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'close'):
                print(ticker, "buy order")
                count = 0.0001
                statusArr[ticker]['orderPlaced'] = True
                statusArr[ticker]['lastAction'] = 'buy'
                order('buy', count, ticker)
            if (action == 'close') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'buy'):
                print(ticker, "closing order")
                count = getLastSymbolCount(getBaseAsset(ticker))
                if count > 0:
                    statusArr[ticker]['lastAction'] = 'close'
                    statusArr[ticker]['orderPlaced'] = True
                    order('sell', count, ticker)
            if (action == 'sell') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'cover'):
                print(ticker, "sell order")
                count = 0.0001
                statusArr[ticker]['lastAction'] = 'sell'
                statusArr[ticker]['orderPlaced'] = True
                order('sell', count, ticker)
            if (action == 'cover') and (statusObj['lastAction'] == 'start' or statusObj['lastAction'] == 'sell'):
                print(ticker, "covering order")
                count = getLastSymbolCount(getBaseAsset(ticker))
                if count != 0:
                    statusArr[ticker]['lastAction'] = 'cover'
                    statusArr[ticker]['orderPlaced'] = True
                    order('buy', abs(count), ticker)

    def reverseList(lst):
        lst.reverse()
        return lst

    def storeHistData(ticker):
        endTime = int(time.time())
        if strategySelection == '3':
            startTime = endTime - 3600 * 24
        else:
            startTime = endTime - 3600 * 24 * 2
        candlesticks = marketClient.get_kline(symbol=ticker.upper(),
                                              kline_type=timeFrameOptions[timeFrameSelection],
                                              startAt=startTime, endAt=endTime)
        candlesticks = reverseList(candlesticks)
        print('Received Historical data for', ticker)
        for candlestick in candlesticks:
            openTimeStamp = datetime.fromtimestamp(int(candlestick[0])).strftime("%Y%m%d %H:%M:%S")
            if ticker not in histData:
                histData[ticker] = [
                    {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[3]),
                     'Low': float(candlestick[4]), 'Close': float(candlestick[2]),
                     'Volume': float(candlestick[6])}]
            else:
                histData[ticker].append(
                    {"Open_Time": openTimeStamp, 'Open': float(candlestick[1]), 'High': float(candlestick[3]),
                     'Low': float(candlestick[4]), 'Close': float(candlestick[2]),
                     'Volume': float(candlestick[6])})

    async def startScan():
        changeRateArr = []
        pickedTickers = []

        print('Scan started: ', symbols)
        if len(symbols) > 5:
            print('Retrieving 24hr Stats for all tickers...')
            print('')
            for symbol in symbols:
                usymbol = symbol.upper()
                res = marketClient.get_24h_stats(usymbol)
                print('24h stats for', usymbol, res)
                changeRateArr.append({'ticker': usymbol, 'changeRate': float(res['changeRate'])})

            def sortByChangeRate(ticker):
                return ticker.get('changeRate')

            def sortByATRDistance(ticker):
                return abs(ticker.get('atrDist'))

            def sortByVWAPDistance(ticker):
                return abs(ticker.get('vwapDist'))

            def sortByMomo(ticker):
                return abs(ticker.get('momo'))

            def sortByDistance(ticker):
                return abs(ticker.get('distance'))

            if biasSelection == '1':
                changeRateArr.sort(key=sortByChangeRate, reverse=True)
            elif biasSelection == '2':
                changeRateArr.sort(key=sortByChangeRate)

            print('')
            print('Sort by percent change:', changeRateArr)
            print('')

            if not advancedFilter:
                for arrayIndex in range(0, 5):
                    ticker = changeRateArr[arrayIndex]['ticker']
                    pickedTickers.append(ticker)
                    storeHistData(ticker)
            else:
                tmpPickedTickers = []
                if len(changeRateArr) > 10:
                    for arrayIndex in range(0, 10):
                        ticker = changeRateArr[arrayIndex]['ticker']
                        tmpPickedTickers.append(ticker)
                        storeHistData(ticker)
                else:
                    for ticker in changeRateArr:
                        tmpPickedTickers.append(ticker['ticker'])
                        storeHistData(ticker['ticker'])

                print('Starting advanced filter for', tmpPickedTickers)
                print('')
                for ticker in tmpPickedTickers:
                    dfData = pd.DataFrame(histData[ticker])
                    close = dfData.tail(1)['Close'].values[0]

                    if strategySelection == '1':  # ATR
                        atrFilterTickers = []

                        try:
                            atrDF = Strategies.ATR(dfData, close, biasOptions[biasSelection])
                            atrZone = atrDF.tail(1)['Zone'].values[0]
                            atrDist = float(atrDF.tail(1)['ATR_dist'].values[0])
                            print("Ticker =", ticker, "last close = ", close, "Zone= ", atrZone, "ATR dist ", atrDist)
                            if (biasSelection == '1' and atrZone == 'below ATR') or (
                                    biasSelection == '2' and atrZone == 'above ATR'):
                                atrFilterTickers.append({'ticker': ticker, 'atrDist': atrDist})
                                print("ATR filter tickers ", atrFilterTickers)
                        except KeyError:
                            e = sys.exc_info()[0]
                            print(ticker, 'ATR except: ', e)
                            continue

                        if len(atrFilterTickers) > 0:
                            atrFilterTickers.sort(key=sortByATRDistance)
                            print(len(atrFilterTickers))

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

                            if (biasSelection == '1' and zone == 'Squeeze In') or (
                                    biasSelection == '2' and zone == 'Squeeze Out'):
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
                await startScreen(pickedTickers)
            else:
                print('No picked tickers')
        else:
            for symbol in symbols:
                storeHistData(symbol.upper())
            await startScreen(symbols)

    async def startScreen(pickedTickers):
        for symbol in pickedTickers:
            usymbol = symbol.upper()
            statusArr[usymbol] = {'lastAction': 'start', 'orderPlaced': False, 'tradeCount': 0, 'lastTime': '',
                                  'startTime': datetime.now().strftime('%m%d_%H%M%S')}
            await ws_client.subscribe('/market/candles:' + usymbol + '_' + timeFrameOptions[timeFrameSelection])

        while True:
            # print("sleeping to keep loop open")
            await asyncio.sleep(60, loop=loop)

    async def endTrade(ticker):
        count = getLastSymbolCount(getBaseAsset(ticker))
        if count > 0:
            order('sell', count, ticker, endTrade=True)
        elif count < 0:
            order('buy', abs(count), ticker, endTrade=True)
        else:
            await ws_client.unsubscribe('/market/candles:' + ticker + '_' + timeFrameOptions[timeFrameSelection])
            print(ticker, 'trade ended')

    # callback function that receives messages from the socket
    async def deal_msg(msg):
        arr1 = msg['topic'].split(':')
        arr2 = arr1[1].split('_')
        ticker = arr2[0]
        candles = msg['data']['candles']
        timeVal = candles[0]
        if timeVal != statusArr[ticker]['lastTime']:
            statusArr[ticker]['lastTime'] = timeVal

            if statusArr[ticker]['tradeCount'] < maxOrderCount:
                if datetime.now() < endTimeDate:
                    openTimeStr = datetime.fromtimestamp(int(timeVal)).strftime("%Y%m%d %H:%M:%S")

                    if ticker not in histData:
                        histData[ticker] = [
                            {"Open_Time": openTimeStr, "Open": float(candles[1]), "High": float(candles[3]),
                             "Low": float(candles[4]), "Close": float(candles[2]), "Volume": float(candles[5])}]
                    else:
                        histData[ticker].append(
                            {"Open_Time": openTimeStr, "Open": float(candles[1]), "High": float(candles[3]),
                             "Low": float(candles[4]), "Close": float(candles[2]), "Volume": float(candles[5])})
                    print("Symbol =", ticker, "Open Time =", openTimeStr, "Close =", candles[2], "Open =", candles[1],
                          "High =", candles[3], "Low =", candles[4])
                    analysisDataFrame(ticker, candles[2])
                else:
                    print('Time is up for', ticker)
                    await endTrade(ticker)
            else:
                print('Max number of trades for', ticker, 'has been reached')
                await endTrade(ticker)

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
    timeFrameOptions["1"] = "1min"
    timeFrameOptions["2"] = "3min"
    timeFrameOptions["3"] = "15min"
    timeFrameOptions["4"] = "1hour"
    # time frame selection except VWAP
    if strategySelection != '3':
        while True:
            options = timeFrameOptions.keys()
            for entry in options:
                print(entry + ")\t" + timeFrameOptions[entry])
            timeFrameSelection = input("Select timeframe: ")
            if timeFrameSelection == '1':
                print('')
                break
            if timeFrameSelection == '2':
                print('')
                break
            if timeFrameSelection == '3':
                print('')
                break
            if timeFrameSelection == '4':
                print('')
                break
    else:
        timeFrameSelection = '1'

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
                            symbols.append(row['Symbol'])
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

    if len(symbols) > 5:
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

    # LIVE KEY
    API_KEY = '609b7c06ce6dbe0006f0e631'
    API_SECRET = 'b5a5092c-644f-44a9-9cf6-426569201a51'
    API_PASSPHRASE = 'Learntotradeinkucoin'
    '''
    # SANDBOX KEY
    API_KEY = '60a32b7f365ac600068a2d7b'
    API_SECRET = '306af733-db6e-4a3a-93fe-5570663d0755'
    API_PASSPHRASE = 'dogetothemoon'
    '''
    client = WsToken()
    userClient = User(API_KEY, API_SECRET, API_PASSPHRASE)
    tradeClient = Trade(key=API_KEY, secret=API_SECRET, passphrase=API_PASSPHRASE)
    marketClient = Market(url='https://api.kucoin.com')
    marginClient = Margin(API_KEY, API_SECRET, API_PASSPHRASE)
    ws_client = await KucoinWsClient.create(None, client, deal_msg, private=False)

    if startOption.lower() == 'y':
        await startScan()
    elif startOption.lower() == 'n':
        delay = (startTimeDate - datetime.now()).total_seconds()
        print('delay: ', delay)
        time.sleep(delay)
        await startScan()


if __name__ == "__main__":
    statusArr = {}
    histData = {}
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
