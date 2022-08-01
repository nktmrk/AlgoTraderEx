from ibapi.client import EClient
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *
from ibapi import utils
from OrderSamples import OrderSamples

import pandas as pd
import numpy as np
import threading
import time
import datetime


class IBApi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.posDF = pd.DataFrame(columns=['account', 'symbol', 'position', 'avg_cost', 'contract'])
        self.histData = {}
        self.shareCount = 0
        self.counter = 0
        self.nextOrderId = 0
        self.filledOrder = False
        self.lowArr = []
        self.highArr = []

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):
        super().completedOrder(contract, order, orderState)
        print("CompletedOrder. PermId:", order.permId, "ParentPermId:", utils.longToStr(order.parentPermId), "Account:",
              order.account, "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange,
              "Action:", order.action, "OrderType:", order.orderType, "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
              "FilledQty:", order.filledQuantity, "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status,
              "Completed time:", orderState.completedTime, "Completed Status:" + orderState.completedStatus)

    def completedOrdersEnd(self):
        super().completedOrdersEnd()
        print("CompletedOrdersEnd")

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                            whyHeld, mktCapPrice)
        '''print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled, "Remaining:", remaining, 
            "AvgFillPrice:", avgFillPrice,  "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
            lastFillPrice, "ClientId:", clientId, "WhyHeld:", whyHeld, "MktCapPrice:", mktCapPrice)'''

        if (self.filledOrder == False) and (status == "Filled"):
            self.filledOrder = True
            print("Order is filled completely")
        elif (self.filledOrder == False) and (filled == self.shareCount):
            self.filledOrder = True
            print("Order is filled completely")
        elif status == "Submitted":
            print("Current status is Submitted")
            if not self.filledOrder:
                print("Order not completely filled")
                self.shareCount = remaining
        elif status == "Cancelled":
            print("Current status is Cancelled")
            if not self.filledOrder:
                print("Order not completely filled")
                self.shareCount = remaining
                # Retry placing order
                self.counter = 0

    def historicalData(self, reqId, bar):
        if reqId not in self.histData:
            self.histData[reqId] = [{"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close, "volume": bar.volume}]
        else:
            self.histData[reqId].append({"date": bar.date, "open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close, "volume": bar.volume})

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.reqRealTimeBars(reqId, usTechStk(ticker), 5, "TRADES", 1, [])

        '''dfData = pd.DataFrame(self.histData[reqId])
        trailDF = calcAtrTrailStop(dfData)
        trailDF.to_csv('ATR.csv')'''

    def realtimeBar(self, reqId: TickerId, time_: int, open_: float, high: float, low: float, close: float, volume: int, wap: float, count: int):
        super().realtimeBar(reqId, time_, open_, high, low, close, volume, wap, count)
        global firstTrade

        dateStamp = datetime.datetime.fromtimestamp(time_)
        # print("Time: ", dateStamp.strftime("%Y%m%d %H:%M:%S"), ' high: ', high, ' low: ', low)
        if time_ % 60 == 0:
            if len(self.highArr) > 0:
                high_ = np.max(self.highArr)
            else:
                high_ = high
            if len(self.lowArr) > 0:
                low_ = np.min(self.lowArr)
            else:
                low_ = high

            if reqId not in self.histData:
                self.histData[reqId] = [{"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_, "close": close, "volume": volume}]
            else:
                self.histData[reqId].append({"date": dateStamp.strftime('%Y%m%d  %H:%M:%S'), "open": open_, "high": high_, "low": low_, "close": close, "volume": volume})

            self.lowArr.clear()
            self.highArr.clear()

            # calculate and store Trail Stop values
            dfData = pd.DataFrame(self.histData[reqId])
            trailDF = calcAtrTrailStop(dfData)
            trailDF.to_csv('ATR.csv')

            trailStopVal = trailDF.tail(1)['trail'].values[0]
            print('Trail Stop: ', trailStopVal)
            # print('atrVal: ', trailDF.tail(1)['atr'].values[0])
            if firstTrade == 'long' and close <= trailStopVal:
                print("Sell Signal")
                firstTrade = 'short'
                if self.shareCount > 0:
                    if self.counter == 0:
                        self.counter = self.counter + 1
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, usTechStk(ticker), OrderSamples.MarketOrder("SELL", self.shareCount))
                        print("Placed SELL order for shares: %d" % self.shareCount)
                        time.sleep(3)
            elif firstTrade == 'short' and close >= trailStopVal:
                print("Buy Signal")
                firstTrade = 'long'
                if self.shareCount > 0:
                    if self.counter == 0:
                        self.counter = self.counter + 1
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, usTechStk(ticker), OrderSamples.MarketOrder("BUY", self.shareCount))
                        print("Placed BUY order for shares: %d" % self.shareCount)
                        time.sleep(3)
        else:
            self.lowArr.append(low)
            self.highArr.append(high)

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)

        dictionary = {"symbol": contract.symbol, 'contract': contract, "position": position, "avg_cost": avgCost}
        self.posDF = self.posDF.append(dictionary, ignore_index=True)

    def positionEnd(self):
        super().positionEnd()

        global firstTrade

        for index, row in self.posDF.iterrows():
            if row['symbol'] == ticker:
                if row['position'] > 0:
                    firstTrade = 'long'
                else:
                    firstTrade = 'short'

                self.shareCount = abs(row['position'])
                self.reqHistoricalData(reqId=10000, contract=usTechStk(ticker), endDateTime='', durationStr='2 D', barSizeSetting='1 min',
                                       whatToShow='TRADES', useRTH=0, formatDate=1, keepUpToDate=1, chartOptions=[])
                break


# function to calculate True Range, Average True Range, Trailing stop
def calcAtrTrailStop(df):
    global firstTrade
    global atrPeriod
    global atrFactor

    df['h-l'] = abs(df['high'] - df['low'])  # Abs of difference between High and Low
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))  # Abs of difference between High and previous period's close
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))  # Abs of difference between Low and previous period's close
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1, skipna=False)  # Max of H-L, H-PC, L-PC
    df['atr'] = df['tr'].ewm(alpha=(1/atrPeriod), adjust=False).mean()  # Calculate WILDERS moving Average True Range calculated from previous step.

    for i in range(1, len(df)):
        loss = df.loc[i, 'atr'] * atrFactor
        if i == 1:
            df.loc[i, 'state'] = firstTrade
            if firstTrade == 'long':
                df.loc[i, 'trail'] = df.loc[i, 'close'] - loss
            if firstTrade == 'short':
                df.loc[i, 'trail'] = df.loc[i, 'close'] + loss
        else:
            pState = df.loc[i-1, 'state']
            pTrail = df.loc[i-1, 'trail']
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


def usTechStk(symbol, sec_type="STK", currency="USD", exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def websocket_con():
    app.run()


firstTrade = 'long'
print("Welcome to Algorithms Trading")
print("")

app = IBApi()
app.connect(host='127.0.0.1', port=7497, clientId=23)  # port 4002 for ib gateway paper trading / 7497 for TWS paper trading

while True:
    ticker = input("Enter ticker symbol: ")
    if len(ticker) > 0:
        break

while True:
    atrPeriod = input("Enter ATR period: ")
    if atrPeriod.isdigit():
        atrPeriod = int(atrPeriod)
        break

while True:
    atrFactor = input("Enter atr factor: ")
    if atrFactor.isdigit():
        atrFactor = int(atrFactor)
        break

app.reqPositions()

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()