import datetime
import collections
import time
import pandas as pd

from ibapi import utils
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *  # @UnusedWildImport
from ibapi.contract import *  # @UnusedWildImport
from ibapi.order import *  # @UnusedWildImport
from ibapi.order_state import *  # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.commission_report import CommissionReport
from ibapi.ticktype import *  # @UnusedWildImport
from OrderSamples import OrderSamples


class IBPy(EWrapper, EClient):
    counter = 0
    filledOrder = False
    nextOrderId = 0
    shareCount = -1
    tickerIndex = -1
    currentTickerSymbol = ''

    def __init__(self):
        EClient.__init__(self, self)
        self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType', 'Currency', 'Position', 'Avg cost'])

    def initParams(self, _tickerIndex: int, _tickerSymbol: str):
        self.counter = 0
        self.filledOrder = False
        self.shareCount = -1
        self.tickerIndex = _tickerIndex
        self.currentTickerSymbol = _tickerSymbol

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        super().error(reqId, errorCode, errorString)
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                       currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        print("AccountSummary. ReqId:", reqId, "Account:", account, "Tag: ", tag, "Value:", value, "Currency:",
              currency)

    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        print("AccountSummaryEnd. ReqId:", reqId)

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)
        print("ExecDetails - ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:",
              contract.currency, execution)

    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        print("ExecDetailsEnd. ReqId:", reqId)

    def commissionReport(self, commissionReport: CommissionReport):
        super().commissionReport(commissionReport)
        print("CommissionReport.", commissionReport)

    def currentTime(self, time: int):
        super().currentTime(time)
        print("CurrentTime:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"))

    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        print("TickSize. TickerId:", reqId, "TickType:", tickType, "Size:", size)

    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        super().tickGeneric(reqId, tickType, value)
        print("TickGeneric. TickerId:", reqId, "TickType:", tickType, "Value:", value)

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)
        print("TickString. TickerId:", reqId, "Type:", tickType, "Value:", value)

    def tickSnapshotEnd(self, reqId: int):
        super().tickSnapshotEnd(reqId)
        print("TickSnapshotEnd. TickerId:", reqId)

    def rerouteMktDataReq(self, reqId: int, conId: int, exchange: str):
        super().rerouteMktDataReq(reqId, conId, exchange)
        print("Re-route market data request. ReqId:", reqId, "ConId:", conId, "Exchange:", exchange)

    def completedOrder(self, contract: Contract, order: Order, orderState: OrderState):
        super().completedOrder(contract, order, orderState)
        print("CompletedOrder. PermId:", order.permId, "ParentPermId:", utils.longToStr(order.parentPermId), "Account:", order.account,
              "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange,
              "Action:", order.action, "OrderType:", order.orderType, "TotalQty:", order.totalQuantity,
              "CashQty:", order.cashQty, "FilledQty:", order.filledQuantity,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status,
              "Completed time:", orderState.completedTime, "Completed Status:" + orderState.completedStatus)

    def completedOrdersEnd(self):
        super().completedOrdersEnd()
        print("CompletedOrdersEnd")

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                            whyHeld, mktCapPrice)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:",
              whyHeld, "MktCapPrice:", mktCapPrice)

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

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        super().tickByTickMidPoint(reqId, time, midPoint)
        global Mid_price
        Mid_price = midPoint
        print("Midpoint. ReqId:", reqId, "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "MidPoint:", midPoint)

    def realtimeBar(self, reqId: TickerId, Time: int, open_: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqId, Time, open_, high, low, close, volume, wap, count)

        print("RealTimeBar - TickerId:", reqId, "Time: ",
              datetime.datetime.fromtimestamp(Time).strftime("%Y%m%d %H:%M:%S"),
              RealTimeBar(Time, -1, open_, high, low, close, volume, wap, count))

        if self.filledOrder:
            self.cancelRealTimeBars(self.tickerIndex)
            time.sleep(1)
            nextRealTimeBars(self.tickerIndex + 1)
        else:
            if strategySelection == "1" or strategySelection == "2":
                if self.shareCount == -1:
                    self.shareCount = avgPrice // open_

            if self.shareCount > 0:
                if self.counter == 0:
                    self.counter = self.counter + 1
                    contract = Contract()
                    contract.secType = 'STK'
                    contract.exchange = "ISLAND"
                    contract.currency = "USD"
                    contract.symbol = self.currentTickerSymbol

                    if strategySelection == "1" or strategySelection == "4":  # Long Strategy or Covering Positions
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, contract, OrderSamples.MarketOrder("BUY", self.shareCount))
                        print("PLACED ORDER for shares: %d" % self.shareCount)
                        time.sleep(3)
                    elif strategySelection == "2" or strategySelection == "3":  # Short Strategy or Closing Positions
                        self.nextOrderId = self.nextOrderId + 1
                        self.placeOrder(self.nextOrderId, contract, OrderSamples.MarketOrder("SELL", self.shareCount))
                        print("PLACED ORDER for shares: %d" % self.shareCount)
                        time.sleep(3)
            else:
                print("")
                print("Price is not enough")
                print("")
                self.cancelRealTimeBars(self.tickerIndex)
                time.sleep(1)
                nextRealTimeBars(self.tickerIndex + 1)

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        dictionary = {"Account": account, "Symbol": contract.symbol, "SecType": contract.secType, "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
        # print("position : ", dictionary)
        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)

    def positionEnd(self):
        super().positionEnd()
        # print("positionEnd")
        if strategySelection == "3":
            closePositions()
        elif strategySelection == "4":
            coverPositions()


# Request Real Time Bar for next ticker
def nextRealTimeBars(tickerIndex: int):
    if strategySelection == "1" or strategySelection == "2":
        if tickerIndex < len(tickers):
            tickerSymbol = tickers[tickerIndex].upper()
            print("")
            print("You are trading", tickerSymbol)
            print("")

            app.initParams(tickerIndex, tickerSymbol)

            contract = Contract()
            contract.secType = 'STK'
            contract.exchange = "ISLAND"
            contract.currency = "USD"
            contract.symbol = tickerSymbol
            app.reqRealTimeBars(tickerIndex, contract, 5, "TRADES", 1, [])
        else:
            print("")
            print("Place Order Finished")
            print("")
    elif strategySelection == "3":
        if tickerIndex < len(closeArr):
            tickerSymbol = closeArr[tickerIndex]['Symbol'].upper()
            print("")
            print("You are closing position for ", tickerSymbol)
            print("")

            app.initParams(tickerIndex, tickerSymbol)
            app.shareCount = closeArr[tickerIndex]['Position']

            contract = Contract()
            contract.secType = 'STK'
            contract.exchange = "ISLAND"
            contract.currency = "USD"
            contract.symbol = tickerSymbol

            app.reqRealTimeBars(tickerIndex, contract, 5, "TRADES", 1, [])
        else:
            print("")
            print("Closing positions using Market Orders Finished")
            print("")
    elif strategySelection == "4":
        if tickerIndex < len(coverArr):
            tickerSymbol = coverArr[tickerIndex]['Symbol'].upper()
            print("")
            print("You are covering position for ", tickerSymbol)
            print("")

            app.initParams(tickerIndex, tickerSymbol)
            app.shareCount = abs(coverArr[tickerIndex]['Position'])

            contract = Contract()
            contract.secType = 'STK'
            contract.exchange = "ISLAND"
            contract.currency = "USD"
            contract.symbol = tickerSymbol

            app.reqRealTimeBars(tickerIndex, contract, 5, "TRADES", 1, [])
        else:
            print("")
            print("Covering positions using Market Orders Finished")
            print("")


# Close positions using Market Orders
def closePositions():
    for index, row in app.pos_df.iterrows():
        if row['Symbol'] in tickers:
            if row['Position'] > 0:
                closeArr.append(row)
            else:
                print("You are closing position for ", row['Symbol'])
                print("Nothing to close")
                print("")
    if len(closeArr) > 0:
        nextRealTimeBars(0)
    else:
        print("")
        print("Closing positions using Market Orders Finished")
        print("")


# Cover positions using Market Orders
def coverPositions():
    for index, row in app.pos_df.iterrows():
        if row['Symbol'] in tickers:
            if row['Position'] < 0:
                coverArr.append(row)
            else:
                print("You are covering position for", row['Symbol'])
                print("Nothing to cover")
                print("")
    if len(coverArr) > 0:
        nextRealTimeBars(0)
    else:
        print("")
        print("Covering positions using Market Orders Finished")
        print("")


print("Welcome to Algorithms Trading")
print("")

# Taking multiple ticker symbols at a time
while True:
    tickers = input("Enter multiple ticker symbols space-separated: ").split()
    if len(tickers) > 0:
        break

# Select Strategy
while True:
    strategyOptions = collections.OrderedDict()
    strategyOptions["1"] = "Long Strategy - Buy stocks using Market Orders"
    strategyOptions["2"] = "Short Strategy - Sell stocks using Market Orders"
    strategyOptions["3"] = "Close positions using Market Orders"
    strategyOptions["4"] = "Cover positions using Market Orders"
    options = strategyOptions.keys()
    for entry in options:
        print(entry + ")\t" + strategyOptions[entry])
    strategySelection = input("Enter what would you like the strategy to do today: ")
    if strategySelection == "1" or strategySelection == "2":
        print("")
        print("You have selected ", strategyOptions[strategySelection])
        print("")
        # Calculate average investment price for each stock
        investmentPrice = 5000
        # investmentPrice = int(input("Enter Investment Price: "))
        avgPrice = investmentPrice / len(tickers)
        print("Average investment price for each stock: ", "{:0.0f}".format(avgPrice))
        print("")
        break
    elif strategySelection == "3":
        print("")
        print("You have selected ", strategyOptions[strategySelection])
        print("")
        closeArr = []
        break
    elif strategySelection == "4":
        print("")
        print("You have selected ", strategyOptions[strategySelection])
        print("")
        coverArr = []
        break

app = IBPy()
app.connect("127.0.0.1", 7497, 1000)

if strategySelection == "1" or strategySelection == "2":
    print("Place Order Started")
    nextRealTimeBars(0)
elif strategySelection == "3" or strategySelection == "4":
    app.reqPositions()

app.run()
