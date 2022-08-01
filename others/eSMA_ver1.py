from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.order import *
import datetime
import pandas as pd
import numpy as np
import pandas as pd
import csv
import time

class TestApp(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId:int):

        self.nextOrderId = orderId

        self.start()


    def error(self, reqId:TickerId, errorCode:int, errorString:str):

        print ("Error: ", reqId, " ", errorCode, " ", errorString)

    def fundamentalData_handler(msg):
        print(msg)

    def fundamentalData(self, reqId: TickerId, data: str):

        super().fundamentalData(reqId, data)

        print("FundamentalData. ReqId:", reqId, "Data:", data)

    def tickPrice(self, reqId, tickType, price, attrib):

        print("Price", price, "Ticktype : ", TickTypeEnum.to_str(tickType))

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        super().tickByTickMidPoint(reqId, time, midPoint)
        print("Midpoint. ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "MidPoint:", midPoint)

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:",
              whyHeld, "MktCapPrice:", mktCapPrice)

    def openOrder(self, orderId, contract, order, orderState):
        #super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId,
              "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
              "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
              "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)

        order.contract = contract
        self.permId2ord[order.permId] = order

    def execDetails(self, reqId, contract, execution):
        #super().execDetails(reqId, contract, execution)
        print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:", contract.currency, execution)
    # ! [execdetails]

    def historicalData(self, reqId:int, bar: BarData):
        global Data_np
        global Counter
        global fileobj
        global write_file
        SMA = bar.close
        EMA20 = SMA
        EMA50 = SMA
        Counter = Counter+1
        #print(Counter)
        if Counter>20:
            Close_array = Data_np["Close"]
            Close_split = Close_array[(Counter-20): Counter]
            print(Close_split)
            SMA = (np.sum(Close_split))/20
            EMA20_array = Data_np["EMA20"]
            Last_EMA20 = EMA20_array[Counter-1]
            k = 2/(1+20)
            EMA20 = bar.close*(k)+Last_EMA20*(1-k)
            print(SMA)

        if Counter>50:
            Close_array = Data_np["Close"]
            EMA50_array = Data_np["EMA50"]
            Last_EMA50 = EMA50_array[Counter-1]
            k = 2/(1+50)
            EMA50 = bar.close*(k)+Last_EMA50*(1-k)

        time.sleep(.1)

        rowdata = [bar.date, bar.open, bar.high, bar.low, bar.close, SMA, EMA20, EMA50]
        rowdata1 = (bar.date, bar.open, bar.high, bar.low, bar.close, SMA, EMA20, EMA50)

        Data_np = np.append(Data_np, np.array([rowdata1], dtype=data_type))
        write_file.writerow(rowdata)
        fileobj.flush()

        #print(Data_np)
        #Data.append(row)
        #print("HistoricalData. ReqId:", reqId, "BarData.", bar)
        #print(BarData)


    def start(self):

        contract1 = Contract()
        contract1.symbol = 'JNUG'
        contract1.secType = 'STK'
        contract1.exchange = "SMART"
        contract1.currency = "USD"

        order = Order()
        order.action = 'BUY'
        order.totalQuantity = 100
        order.OrderType = 'LMT'
        order.lmtPrice = 72.60

        #app.placeOrder(self.nextOrderId, contract1, order)


app = TestApp()
app.connect("127.0.0.1", 4001, 3)
#app.fundamentalData()
app.nextOrderId = 0

contract2 = Contract()
contract2.symbol = 'JNUG'
contract2.secType = 'STK'
contract2.exchange = "SMART"
contract2.currency = "USD"

contract3 = Contract()
contract3.symbol = 'AMZN'
contract3.secType = 'STK'
contract3.exchange = "SMART"
contract3.currency = "USD"


app.start()

fileobj = open('Archive/Historic_data2.csv', 'w')
write_file = csv.writer(fileobj, dialect="excel")
write_file.writerow(["Date","Open","High", "Low","Close",'SMA','EMA20', 'EMA50'])


data_type = [("Date",'S20'), ("Open",'f8'), ("High",'f8'),( "Low",'f8'), ("Close",'f8'), ('SMA', 'f8'), ('EMA20', 'f8'), ('EMA50', 'f8')]
Data_np = np.zeros((1),dtype=data_type)
Counter= 0

queryTime = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")
app.reqHistoricalData(4104, contract3, queryTime, "5 D", "5 mins", "MIDPOINT", 1, 1, False, [])


app.run()
print(Data_np)

