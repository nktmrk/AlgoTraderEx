import math
import numpy as np


class Strategies:

    # calculate Exponential moving average
    @staticmethod
    def EMA(dataFrame, bias='Long'):
        df = dataFrame.copy()

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
            if bias == 'Long':
                # Action
                if df.loc[i, 'Zone'] == 'Squeeze Out' and df.loc[i - 1, 'Zone'] == 'Squeeze In':
                    df.loc[i, 'ACTION'] = 'buy'
                if df.loc[i, 'Zone'] == 'Squeeze in' and df.loc[i - 1, 'Zone'] == 'Squeeze out':
                    df.loc[i, 'ACTION'] = 'close'
            if bias == 'Short':
                # Action
                if df.loc[i, 'Zone'] == 'Squeeze Out' and df.loc[i - 1, 'Zone'] == 'Squeeze In':
                    df.loc[i, 'ACTION'] = 'cover'
                if df.loc[i, 'Zone'] == 'Squeeze in' and df.loc[i - 1, 'Zone'] == 'Squeeze out':
                    df.loc[i, 'ACTION'] = 'sell'

        return df

    # calculate True Range, Average True Range, Trailing stop
    @staticmethod
    def ATR(dataFrame, close, bias='Long'):
        if float(close) < 10:
            atrPeriod = 14
            atrFactor = 12
        elif 10 < float(close) < 20:
            atrPeriod = 14
            atrFactor = 10
        elif 20 < float(close) < 30:
            atrPeriod = 7
            atrFactor = 8
        elif 30 < float(close) < 50:
            atrPeriod = 7
            atrFactor = 7
        elif float(close) > 50:
            atrPeriod = 7
            atrFactor = 7

        df = dataFrame.copy()

        df['H-L'] = abs(df['High'] - df['Low'])  # Abs of difference between High and Low
        df['H-PC'] = abs(
            df['High'] - df['Close'].shift(1))  # Abs of difference between High and previous period's close
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))  # Abs of difference between Low and previous period's close
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
        df['ATR'] = df['TR'].ewm(alpha=(1 / atrPeriod), adjust=False).mean()
        df['EMA_200'] = df["Close"].ewm(span=200, min_periods=200).mean()

        for i in range(1, len(df)):
            loss = df.loc[i, 'ATR'] * atrFactor
            if i == 1:
                df.loc[i, 'State'] = bias
                if bias == 'Long':
                    df.loc[i, 'Trail'] = df.loc[i, 'Close'] - loss
                if bias == 'Short':
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

            df.loc[i, 'ATR_dist'] = 100 * (df.loc[i, 'Trail'] - df.loc[i, 'Close']) / df.loc[i, 'Close']

            df.loc[i, 'Zone'] = 'no'
            if df.loc[i, 'Close'] > df.loc[i, 'Trail']:
                df.loc[i, 'Zone'] = 'above ATR'
            elif df.loc[i, 'Close'] < df.loc[i, 'Trail']:
                df.loc[i, 'Zone'] = 'below ATR'

            df.loc[i, 'ACTION'] = 'NO'
            # pos
            if bias == 'Long':
                # Action
                if df.loc[i, 'Zone'] == 'above ATR' and df.loc[i - 1, 'Zone'] == 'below ATR':
                    df.loc[i, 'ACTION'] = 'buy'
                if df.loc[i, 'Zone'] == 'below ATR' and df.loc[i - 1, 'Zone'] == 'above ATR':
                    df.loc[i, 'ACTION'] = 'close'
            if bias == 'Short':
                # Action
                if df.loc[i, 'Zone'] == 'below ATR' and df.loc[i - 1, 'Zone'] == 'above ATR':
                    df.loc[i, 'ACTION'] = 'sell'
                if df.loc[i, 'Zone'] == 'above ATR' and df.loc[i - 1, 'Zone'] == 'below ATR':
                    df.loc[i, 'ACTION'] = 'cover'

        return df

    # Volume Weighted Average Price
    @staticmethod
    def VWAP(dataFrame, bias='Long'):
        df = dataFrame.copy()

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

            df.loc[i, 'ACTION'] = 'NO'
            # pos
            if bias == 'Long':
                # Action
                if df.loc[i, 'Zone'] == 'pos_fast' and df.loc[i - 1, 'Zone'] == 'pos_fast' and df.loc[
                    i - 2, 'Zone'] == 'pos_slow':
                    df.loc[i, 'ACTION'] = 'buy'
                if df.loc[i, "MA_9"] < .99 * df.loc[i, "MA_27"]:
                    df.loc[i, 'ACTION'] = 'close'
                df.loc[i, 'VWAP_distance'] = 100 * (df.loc[i, 'Close'] - df.loc[i, 'VWAP_up1']) / df.loc[i, 'Close']

            if bias == 'Short':
                # Action
                if df.loc[i, 'Zone'] == 'neg_fast' and df.loc[i - 1, 'Zone'] == 'neg_fast' and df.loc[
                    i - 2, 'Zone'] == 'neg_slow':
                    df.loc[i, 'ACTION'] = 'sell'
                if df.loc[i, "MA_9"] > 1.01 * df.loc[i, "MA_27"]:
                    df.loc[i, 'ACTION'] = 'cover'
                df.loc[i, 'VWAP_distance'] = 100 * (df.loc[i, 'Close'] - df.loc[i, 'VWAP_dn1']) / df.loc[i, 'Close']

        return df

    # TTM Squeeze Calculation
    @staticmethod
    def TTMSqueeze(dataFrame, n=20, bias='Long'):
        df = dataFrame.copy()

        df["MA_9"] = df["Close"].ewm(span=9, min_periods=9).mean()
        df["MA_27"] = df["Close"].ewm(span=27, min_periods=27).mean()

        df['20sma'] = df['Close'].rolling(window=n).mean()
        df['sDev'] = df['Close'].rolling(window=n).std()
        df['LowerBandBB'] = df['20sma'] - (2 * df['sDev'])
        df['UpperBandBB'] = df['20sma'] + (2 * df['sDev'])

        df['H-L'] = abs(df['High'] - df['Low'])  # Abs of difference between High and Low
        df['H-PC'] = abs(
            df['High'] - df['Close'].shift(1))  # Abs of difference between High and previous period's close
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
                i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow'] and df.loc[i, 'LowerBandBB'] > df.loc[
                                            i - 1, 'LowerBandBB']
            df.loc[i, 'preSqueezeOut'] = df.loc[i, 'LowerBandKCLow'] < df.loc[i, 'LowerBandBB'] < df.loc[
                i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCLow']

            df.loc[i, 'originalSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCMid'] and df.loc[
                i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid'] and df.loc[i, 'LowerBandBB'] > df.loc[
                                                 i - 1, 'LowerBandBB']
            df.loc[i, 'originalSqueezeOut'] = df.loc[i, 'LowerBandKCMid'] < df.loc[i, 'LowerBandBB'] < df.loc[
                i - 1, 'LowerBandBB'] and df.loc[i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCMid']

            df.loc[i, 'extrSqueezeIn'] = df.loc[i, 'LowerBandBB'] > df.loc[i, 'LowerBandKCHigh'] and df.loc[
                i, 'UpperBandBB'] < df.loc[i, 'UpperBandKCHigh'] and df.loc[i, 'LowerBandBB'] > df.loc[
                                             i - 1, 'LowerBandBB']
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
            if bias == 'Long':
                # Action
                if df.loc[i, 'squeeze'] == 'yellow' and df.loc[i, 'momentum'] == 'cyan' and df.loc[i, 'MA_9'] > df.loc[
                    i, 'MA_27']:
                    df.loc[i, 'ACTION'] = 'buy'
                if df.loc[i, 'MA_9'] < df.loc[i, 'MA_27']:
                    df.loc[i, 'ACTION'] = 'close'

            if bias == 'Short':
                # Action
                if df.loc[i, 'squeeze'] == 'yellow' and df.loc[i, 'momentum'] == 'red' and df.loc[i, 'MA_9'] < df.loc[
                    i, 'MA_27']:
                    df.loc[i, 'ACTION'] = 'sell'
                if df.loc[i, 'MA_9'] > df.loc[i, 'MA_27']:
                    df.loc[i, 'ACTION'] = 'cover'

        return df

    # Top Ultimate Breakout Indicator
    @staticmethod
    def TopBreakOut(dataFrame, bias='Long'):
        df = dataFrame.copy()

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

            if bias == 'Long':
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
                df.loc[i, 'Entry_ratio'] = df.loc[i, 'High'] / df.loc[i - 1, 'QB']
                df.loc[i, 'Exit_ratio'] = df.loc[i, 'Low'] / df.loc[i - 1, 'LL']
                df.loc[i, 'Distance'] = 100 * (df.loc[i, 'Entry_ratio'] - df.loc[i, 'Exit_ratio'])

            elif bias == 'Short':
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
                df.loc[i, 'Entry_ratio'] = df.loc[i, 'Low'] / df.loc[i - 1, 'QS']
                df.loc[i, 'Exit_ratio'] = df.loc[i, 'High'] / df.loc[i - 1, 'HH']
                df.loc[i, 'Distance'] = 100 * (df.loc[i, 'Entry_ratio'] - df.loc[i, 'Exit_ratio'])

        return df