
from ibapi.wrapper import EWrapper
import argparse
import datetime
import collections
import inspect
import csv
import logging
import time
import os.path
import random
import math
import numpy as np

from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.utils import iswrapper

from ContractSamples import ContractSamples
from OrderSamples import OrderSamples

# types
from ibapi.common import * # @UnusedWildImport
from ibapi.order_condition import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.ticktype import * # @UnusedWildImport
from ibapi.tag_value import TagValue

from ibapi.account_summary_tags import *

from ContractSamples import ContractSamples
from OrderSamples import OrderSamples
from AvailableAlgoParams import AvailableAlgoParams
from ScannerSubscriptionSamples import ScannerSubscriptionSamples
from FaAllocationSamples import FaAllocationSamples
from ibapi.scanner import ScanData
from ibapi.object_implem import Object
from ibapi.scanner import ScannerSubscription
import xml.etree.ElementTree as ET

from Scanner_subscription_gain_copy1 import *



class IBPy(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.Counter = 0
        self.FilledOrder = False
        self.TickbyTick = True
        self.UnFilledQty = 100

        self.Startday = True
        self.AboveVWAP = False
        self.Status = "OPEN"
        self.Retry = False


        self.stop_data = False
        self.Init = True
        self.Short = True
        self.StartScanner = True
        self.Valid_data = True

        self.Percent1 = False
        self.Percent2 = False
        self.Percent3 = False
        self.Percent4 = False
        self.Percent5 = False
        self.Percent6 = False
        self.Percent7 = False
        self.Percent8 = False
        self.Percent9 = False
        self.Percent10 = False
        self.Percent12 = False
        self.Percent14 = False
        self.Percent16 = False
        self.Percent18 = False
        self.Percent20 = False
        self.Percent22 = False
        self.Percent24 = False
        self.Percent26 = False
        self.Percent28 = False
        self.Percent30 = False

        self.PercentN4 = False

        self.Percent1P = False
        self.Percent2P = False
        self.Percent1N = False
        self.Percent2N = False

        self.EMA_status = "Long"

        self.first_time = True

        self.Cancelcount = 0

        Hist_count = 9000


    def nextValidId(self, orderId:int):

        self.nextOrderId = orderId

        #self.start()


    def error(self, reqId:TickerId, errorCode:int, errorString:str):

        print ("Error: ", reqId, " ", errorCode, " ", errorString)

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                       currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        print("AccountSummary. ReqId:", reqId, "Account:", account,
              "Tag: ", tag, "Value:", value, "Currency:", currency)
    # ! [accountsummary]

    # ! [accountsummaryend]
    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        print("AccountSummaryEnd. ReqId:", reqId)
    # ! [accountsummaryend]

    # ! [execdetails]
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)
        print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:",
              contract.currency, execution)

    # ! [execdetails]


    # ! [execdetailsend]
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        print("ExecDetailsEnd. ReqId:", reqId)

    # ! [execdetailsend]


    # ! [commissionreport]
    def commissionReport(self, commissionReport: CommissionReport):
        super().commissionReport(commissionReport)
        print("CommissionReport.", commissionReport)

    # ! [commissionreport]


    # ! [currenttime]
    def currentTime(self, time: int):
        super().currentTime(time)
        print("CurrentTime:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"))

    # ! [currenttime]


    # ! [completedorder]
    def completedOrder(self, contract: Contract, order: Order,
                       orderState: OrderState):
        super().completedOrder(contract, order, orderState)
        print("CompletedOrder. PermId:", order.permId, "ParentPermId:", utils.longToStr(order.parentPermId), "Account:",
              order.account,
              "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange,
              "Action:", order.action, "OrderType:", order.orderType, "TotalQty:", order.totalQuantity,
              "CashQty:", order.cashQty, "FilledQty:", order.filledQuantity,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status,
              "Completed time:", orderState.completedTime, "Completed Status:" + orderState.completedStatus)

    # ! [completedorder]

    # ! [completedordersend]
    def completedOrdersEnd(self):
        super().completedOrdersEnd()
        print("CompletedOrdersEnd")

    # ! [completedordersend]

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

        global Shares
        global Final_Price
        global contract
        global Order_status
        global Pick
        global Close
        global Ordercount
        global Stock_ID
        global action
        global Purchase_price

        self.UnFilledQty = remaining


        if (status == "Filled") & (self.Status == 'NEW POSITION') & (Ordercount<10):
            self.FilledOrder = True
            #Shares = int(filled)
            Final_Price = avgFillPrice
            Order_status = Order_status + 1
            if Order_status == 2:
                #self.Status = "FILLED"
                self.stop_data = False
                Ordercount = Ordercount + 1
                print("OrderCount", Ordercount)
                time.sleep(6)
                Purchase_price = avgFillPrice
                self.reqRealTimeBars(Stock_ID, Pick, 5, "TRADES", False, [])
                Order_status = 0
                self.Startday = False
                #self.reqTickByTickData(666, Pick, "AllLast", 0, False)
        if (status == "Filled") & (self.Status == 'CLOSED') & (Ordercount<10):
            self.FilledOrder = True
            #Shares = int(filled)
            Final_Price = avgFillPrice
            Order_status = Order_status + 1
            if (Order_status == 2)&(self.EMA_status == "Short"):
                self.Status = "FILLED"
                self.stop_data = False
                time.sleep(6)
                Purchase_price = avgFillPrice
                #action = "SELL"
                #self.nextOrderId = self.nextOrderId + 1
                #self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, Shares, math.floor(Final_Price-.1)))
                self.Status = 'NEW POSITION'
                Order_status = 0
                Ordercount = Ordercount + 1
                self.reqRealTimeBars(Stock_ID, Pick, 5, "TRADES", False, [])
            if (Order_status == 2) & (self.EMA_status == "Long"):
                self.Status = "FILLED"
                self.stop_data = False
                time.sleep(6)
                Purchase_price = avgFillPrice
                #action = "BUY"
                #self.nextOrderId = self.nextOrderId + 1
                #self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, Shares, math.floor(Final_Price - .1)))
                self.Status = 'NEW POSITION'
                Order_status = 0
                Ordercount = Ordercount + 1
                self.reqRealTimeBars(Stock_ID, Pick, 5, "TRADES", False, [])

        if (status == "Cancelled")& (Ordercount<10):
            print("Pending Cancel")
            if self.UnFilledQty > 0:
                time.sleep(5)
                self.Status = "CANCELLED"
                self.reqRealTimeBars(Stock_ID, Pick, 5, "TRADES", False, [])
                print("Retrying to place order")


    def openOrder(self, orderId, contract, order, orderState):
        #super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId,
              "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
              "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
              "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)

        if orderState.status == "Filled":
            self.FilledOrder = True

        if orderState.status == "PendingCancel":
            print ("Pending Cancel")
            self.FilledOrder = False

        order.contract = contract
        #self.permId2ord[order.permId] = order

    def fundamentalData(self, reqId: TickerId, data: str):
        super().fundamentalData(reqId, data)
        # print("FundamentalData. ReqId:", reqId, "Data:", data)
        global marketcap

        tree = ET.fromstring(data)
        for elem in tree.iter():

            if elem.attrib == {'FieldName': 'MKTCAP', 'Type': 'N'}:
                print("Received MKTCAP")
                marketcap = float(elem.text)

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        super().tickByTickMidPoint(reqId, time, midPoint)
        global Mid_price
        Mid_price = midPoint
        print("Midpoint. ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "MidPoint:", midPoint)

    def realtimeBar(self, reqId: TickerId, Date_int:int, open_: float, high: float, low: float, Close: float,
                        volume: int, wap: float, Count: int):
        super().realtimeBar(reqId, Date_int, open_, high, low, Close, volume, wap, Count)
        #print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, Close, volume, wap, Count))
        global close
        global Limit_price
        global Shares
        global selection2
        global action
        global Tickcounter
        global hr_cnt
        global cnt
        global VSum
        global VPSum
        global VWAP
        global VWAP_1P
        global VWAP_1N
        global VWAP_2P
        global VWAP_2N
        global N
        global Dev
        global Devsum
        global VWAP_array
        global VWAPCount
        global Purchase_price
        global Start
        global Avg_price
        global writefile
        global csvobj
        global Purchase_time
        global news_counter
        global time_date
        global Ticker
        global contract
        global stock
        global count
        global trade_signal
        global EndDate
        global VWAP_up
        global VWAP_down
        global marketcap
        global Time_bell
        global Pre_high
        global Pre_low
        global Time_now
        global Time_now_sec
        global ScanPick
        global Pick
        global skip_list
        global Hist_count
        # print (Hist_count)
        global close_array
        global EMA9_array
        global EMA9
        global EMA27_array
        global EMA27
        global EMA54_array
        global EMA54
        global Buffer
        global Temp_vol
        global Stock_ID

        # Calculate Volume EVERY 5 SEC
        Temp_vol = Temp_vol + volume
        VSum = VSum + volume
        #print("Vsum= ", VSum)

        if Date_int%60 == 0 :


            if self.Status == "CANCELLED":
                print("Retrying")
                time.sleep(2)
                self.nextOrderId = self.nextOrderId + 1
                self.Cancelcount = self.Cancelcount + 1

                if self.Cancelcount < 5:

                    if self.Startday == True:
                        if action == "BUY":
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (Shares), math.ceil(Close+1)))
                        if action == "SELL":
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (Shares), math.floor(Close)))
                        self.cancelRealTimeBars(Stock_ID)
                        self.Status = "NEW POSITION"


                    else:

                        if action == "BUY":
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (2 * Shares), math.ceil(Close+1)))
                        if action == "SELL":
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (2 * Shares), math.floor(Close)))
                        self.cancelRealTimeBars(Stock_ID)
                        self.Status = "CLOSED"

                else:
                    print("Exiting after 5 tries")
                    self.cancelRealTimeBars(Stock_ID)



            if self.Status == "NEW POSITION":

                if self.EMA_status == "Long":
                    Tickcounter = Tickcounter + 1
                    # print(close_array)
                    close_array.append(Close)
                    print("Tick ", Tickcounter)

                    # Avg_price = Shares * Purchase_price

                    # global contract1
                    close = Close
                    print("Time= ", "Ticker = ", Ticker, "current price = ", Close, "Volume Bid = ", volume)

                    # exponential MA Calculation
                    SMA = Close
                    EMA9 = SMA
                    EMA27 = SMA
                    EMA54 = SMA
                    # print(Counter)
                    N1 = 10
                    N2 = 28
                    N3 = 55
                    if Tickcounter < N1:
                        # print("I am in N1")
                        EMA9_array.append(Close)
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)
                    if Tickcounter == N1:
                        Close_split = close_array[(Tickcounter - N1): (Tickcounter - 1)]
                        # print("Close array")
                        # print(close_array)
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N1 - 1)
                        # print(SMA)
                        EMA9_array.append(SMA)
                        EMA9 = SMA
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)
                    if Tickcounter > N1:
                        # print("EMA9")
                        # print(EMA9_array)
                        Last_EMA9 = EMA9_array[Tickcounter - 2]
                        k = 2 / (N1)
                        EMA9 = Close * (k) + Last_EMA9 * (1 - k)
                        EMA9_array.append(EMA9)

                    if (Tickcounter > N1) & (Tickcounter < N2):
                        # print("I am in N2")
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)

                    if Tickcounter == N2:
                        Close_split = close_array[(Tickcounter - N2): (Tickcounter - 1)]
                        # print("Close array")
                        # print(close_array)
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N2 - 1)
                        EMA27_array.append(SMA)
                        EMA27 = SMA
                        EMA54_array.append(Close)
                    if Tickcounter > N2:
                        # print("EMA27")
                        # print(EMA27_array)
                        Last_EMA27 = EMA27_array[Tickcounter - 2]
                        k = 2 / (N2)
                        EMA27 = Close * (k) + Last_EMA27 * (1 - k)
                        EMA27_array.append(EMA27)

                    if (Tickcounter > N2) & (Tickcounter < N3):
                        # print("I am in N3")
                        EMA54_array.append(Close)
                    if Tickcounter == N3:
                        # print("Close array")
                        # print(close_array)
                        Close_split = close_array[(Tickcounter - N3): (Tickcounter - 1)]
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N3 - 1)
                        EMA54_array.append(SMA)
                        EMA54 = SMA
                    if Tickcounter > N3:
                        # print("EMA54")
                        # print(EMA54_array)
                        Last_EMA54 = EMA54_array[Tickcounter - 2]
                        k = 2 / (N3)
                        EMA54 = Close * (k) + Last_EMA54 * (1 - k)
                        EMA54_array.append(EMA54)

                    VPSum = VPSum + (wap) * (wap)
                    # print("VPsum= ", VPSum)
                    VWAP = VPSum / VSum
                    # print ("VWAP= " , VWAP)
                    N = N + 1
                    Devsum = Devsum + (wap * wap * Temp_vol)

                    Dev_now = (Devsum / VSum) - (VWAP * VWAP)

                    if Dev_now > 0:
                        Dev = math.sqrt(Dev_now)
                    else:
                        Dev = 0
                    # print("Dev", Dev_now)
                    VWAP_1P = VWAP + (Dev)
                    VWAP_1N = VWAP - (Dev)
                    VWAP_2P = VWAP + (2 * Dev)
                    VWAP_2N = VWAP - (2 * Dev)
                    print("VWAP =", VWAP)
                    print("Adjusted VWAP = ", VWAP_1P, " ", VWAP_1N)
                    # Reset Temp Vol
                    Temp_vol = 0

                    if Close > VWAP:
                        self.AboveVWAP = True
                        VWAP_up = VWAP_up + 1
                        # Purchase_price = tick.price

                    if Close < VWAP:
                        self.AboveVWAP = False
                        VWAP_down = VWAP_down + 1
                        # Purchase_price = tick.price

                    print("Purchase Price", Purchase_price)
                    print("P&L ", Close - Purchase_price)
                    PnL = (Close - Purchase_price)
                    # print("Writing to file")
                    writefile.writerow([Ticker,Date_int , Purchase_price, Close,
                                        (volume), VSum, VWAP, self.AboveVWAP, self.Status, PnL, Tickcounter, VWAP_up,
                                        VWAP_down, VWAP_1P,
                                        VWAP_2P, VWAP_1N, VWAP_2N, Pre_high, Pre_low, EMA9, EMA27, EMA54, self.EMA_status])
                    csvobj.flush()

                    if (Tickcounter > N3)&(self.Status == "NEW POSITION"):
                        print("EMA9",EMA9)
                        print("EMA54", EMA54)
                        #print("Buffered EMA54)",(100-Buffer)*EMA54*.01)
                        #print("Adjusted VWAP", VWAP_1N)
                        if EMA9 < .985*EMA54:
                            self.EMA_status = "Short"
                            action = "SELL"
                            print("Triggered EMA9 less than EMA54")
                            self.nextOrderId = self.nextOrderId + 1
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (2*Shares), math.floor(Close-1)))
                            self.cancelRealTimeBars(Stock_ID)
                            self.Status = "CLOSED"

                    if Purchase_price == 1000:
                        print("Skip")
                    else:
                        if (Close - Purchase_price) * Shares > 205:
                            action = "SELL"
                            print("Exit for good! ")
                            self.nextOrderId = self.nextOrderId + 1
                            self.placeOrder(self.nextOrderId, Pick,
                                            OrderSamples.IOC(action, (Shares), math.floor(Close - 1)))
                            self.cancelRealTimeBars(Stock_ID)
                            self.Status = "Exit"


                if self.EMA_status == "Short":

                    Tickcounter = Tickcounter + 1
                    # print(close_array)
                    close_array.append(Close)
                    print("Tick ", Tickcounter)

                    # Avg_price = Shares * Purchase_price

                    # global contract1
                    close = Close
                    print("Time= ", "Ticker = ", Ticker, "current price = ", Close, "Volume Bid = ", volume)

                    # exponential MA Calculation
                    SMA = Close
                    EMA9 = SMA
                    EMA27 = SMA
                    EMA54 = SMA
                    # print(Counter)
                    N1 = 10
                    N2 = 28
                    N3 = 55
                    if Tickcounter < N1:
                        # print("I am in N1")
                        EMA9_array.append(Close)
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)
                    if Tickcounter == N1:
                        Close_split = close_array[(Tickcounter - N1): (Tickcounter - 1)]
                        # print("Close array")
                        # print(close_array)
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N1 - 1)
                        # print(SMA)
                        EMA9_array.append(SMA)
                        EMA9 = SMA
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)
                    if Tickcounter > N1:
                        # print("EMA9")
                        # print(EMA9_array)
                        Last_EMA9 = EMA9_array[Tickcounter - 2]
                        k = 2 / (N1)
                        EMA9 = Close * (k) + Last_EMA9 * (1 - k)
                        EMA9_array.append(EMA9)

                    if (Tickcounter > N1) & (Tickcounter < N2):
                        # print("I am in N2")
                        EMA27_array.append(Close)
                        EMA54_array.append(Close)

                    if Tickcounter == N2:
                        Close_split = close_array[(Tickcounter - N2): (Tickcounter - 1)]
                        # print("Close array")
                        # print(close_array)
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N2 - 1)
                        EMA27_array.append(SMA)
                        EMA27 = SMA
                        EMA54_array.append(Close)
                    if Tickcounter > N2:
                        # print("EMA27")
                        # print(EMA27_array)
                        Last_EMA27 = EMA27_array[Tickcounter - 2]
                        k = 2 / (N2)
                        EMA27 = Close * (k) + Last_EMA27 * (1 - k)
                        EMA27_array.append(EMA27)

                    if (Tickcounter > N2) & (Tickcounter < N3):
                        # print("I am in N3")
                        EMA54_array.append(Close)
                    if Tickcounter == N3:
                        # print("Close array")
                        # print(close_array)
                        Close_split = close_array[(Tickcounter - N3): (Tickcounter - 1)]
                        # print(Close_split)
                        SMA = (np.sum(Close_split)) / (N3 - 1)
                        EMA54_array.append(SMA)
                        EMA54 = SMA
                    if Tickcounter > N3:
                        # print("EMA54")
                        # print(EMA54_array)
                        Last_EMA54 = EMA54_array[Tickcounter - 2]
                        k = 2 / (N3)
                        EMA54 = Close * (k) + Last_EMA54 * (1 - k)
                        EMA54_array.append(EMA54)

                    # print(N)
                    VPSum = VPSum + (wap) * (wap)
                    # print("VPsum= ", VPSum)
                    VWAP = VPSum / VSum
                    # print ("VWAP= " , VWAP)
                    N = N + 1
                    Devsum = Devsum + (wap * wap * Temp_vol)

                    Dev_now = (Devsum / VSum) - (VWAP * VWAP)

                    if Dev_now > 0:
                        Dev = math.sqrt(Dev_now)
                    else:
                        Dev = 0
                    # print("Dev", Dev_now)
                    VWAP_1P = VWAP + (.25 * Dev)
                    VWAP_1N = VWAP - (.25 * Dev)
                    VWAP_2P = VWAP + (2 * Dev)
                    VWAP_2N = VWAP - (2 * Dev)
                    print ("VWAP =", VWAP)
                    print("Adjusted VWAP = ", VWAP_1P, " ", VWAP_1N)
                    # Reset Temp Vol
                    Temp_vol = 0

                    if close > VWAP:
                        self.AboveVWAP = True
                        VWAP_up = VWAP_up + 1
                        # Purchase_price = tick.price

                    if close < VWAP:
                        self.AboveVWAP = False
                        VWAP_down = VWAP_down + 1
                        # Purchase_price = tick.price

                    print("Purchase Price", Purchase_price)
                    print("P&L ", Purchase_price- Close)

                    PnL = (Purchase_price - Close)
                    # print("Writing to file")
                    writefile.writerow([Ticker, Date_int, Purchase_price, Close,
                                        (volume), VSum, VWAP, self.AboveVWAP, self.Status, PnL, Tickcounter, VWAP_up,
                                        VWAP_down, VWAP_1P,
                                        VWAP_2P, VWAP_1N, VWAP_2N, Pre_high, Pre_low, EMA9, EMA27, EMA54, self.EMA_status])
                    csvobj.flush()

                    print("EMA9", EMA9)
                    print("EMA54", EMA54)
                    # print("Buffered EMA54)",(100-Buffer)*EMA54*.01)
                    #print("Adjusted VWAP", VWAP_1P)

                    if (Tickcounter > N3) & (self.Status == "NEW POSITION"):
                        if EMA9 > 1.015*EMA54:
                            self.EMA_status = "Long"
                            action = "BUY"
                            print("Triggered EMA9 more than EMA54")
                            self.nextOrderId = self.nextOrderId + 1
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, (2*Shares), math.ceil(Close-1)))
                            self.cancelRealTimeBars(Stock_ID)
                            self.Status = "CLOSED"

                    if Purchase_price == 1000:
                        print("Skip")
                    else:

                        if (Purchase_price - Close) * Shares > 205:
                            action = "BUY"
                            print("Exit for good! ")
                            self.nextOrderId = self.nextOrderId + 1
                            self.placeOrder(self.nextOrderId, Pick,
                                            OrderSamples.IOC(action, (Shares), math.ceil(Close + 1)))
                            self.cancelRealTimeBars(Stock_ID)
                            self.Status = "Exit"


    def historicalData(self, reqId: int, bar: BarData):
        print("HistoricalData. ReqId:", reqId, "BarData.", bar)

        global close
        global Limit_price
        global Shares
        global selection2
        global action
        global Tickcounter
        global hr_cnt
        global cnt
        global VSum
        global VPSum
        global VWAP
        global VWAP_1P
        global VWAP_1N
        global VWAP_2P
        global VWAP_2N
        global N
        global Dev
        global Devsum
        global VWAP_array
        global VWAPCount
        global Purchase_price
        global Start
        global Avg_price
        global writefile
        global csvobj
        global Purchase_time
        global news_counter
        global time_date
        global Ticker
        global contract
        global stock
        global count
        global trade_signal
        global EndDate
        global VWAP_up
        global VWAP_down
        global marketcap
        global Time_bell
        global Pre_high
        global Pre_low
        global Time_now
        global Time_now_sec
        global ScanPick
        global Pick
        global skip_list
        global Hist_count
        #print (Hist_count)
        global close_array
        global EMA9_array
        global EMA9
        global EMA27_array
        global EMA27
        global EMA54_array
        global EMA54
        global Short_dict
        global Scan_ID
        global Stock_ID
        global start_price


        if reqId == Hist_count:

            Tickcounter = Tickcounter + 1
            #print(close_array)
            close_array.append(bar.close)
            print("Tick ", Tickcounter)
            if self.Init == True:
                Pre_high = bar.high
                Pre_low = bar.low
                self.Init = False

            if time.mktime(datetime.datetime.strptime(bar.date, '%Y%m%d %H:%M:%S').timetuple()) < Time_bell:
                if bar.high >= Pre_high:
                    Pre_high = bar.high

                if bar.low <= Pre_low:
                    Pre_low = bar.low

            if (bar.close < 5) or (bar.close > 500):
                print("Price is outside range")
                self.Retry = True

            for x in skip_list:

                if Ticker == x:
                    print("Ticker already analysed")
                    self.Retry = True

            '''
            
            if len(Ticker) == 4:
                print("Four letter Ticker")
            else:
                print("Long letter")
                self.Retry = True
            '''

            #Avg_price = Shares * Purchase_price

            # global contract1
            close = bar.close
            print("Time= ", bar.date, "Ticker = ", Ticker, "current price = ", bar.close, "Volume Bid = ", bar.volume)

            #exponential MA Calculation
            #exponential MA Calculation
            SMA = bar.close
            EMA9 = SMA
            EMA27 = SMA
            EMA54 = SMA
            # print(Counter)
            N1 = 10
            N2 = 28
            N3 = 55
            if Tickcounter < N1:
                #print("I am in N1")
                EMA9_array.append(bar.close)
                EMA27_array.append(bar.close)
                EMA54_array.append(bar.close)
            if Tickcounter == N1:
                Close_split = close_array[(Tickcounter - N1): (Tickcounter - 1)]
                #print("Close array")
                #print(close_array)
                #print(Close_split)
                SMA = (np.sum(Close_split)) / (N1-1)
                #print(SMA)
                EMA9_array.append(SMA)
                EMA9 = SMA
                EMA27_array.append(bar.close)
                EMA54_array.append(bar.close)
            if Tickcounter > N1:
                #print("EMA9")
                #print(EMA9_array)
                Last_EMA9 = EMA9_array[Tickcounter - 2]
                k = 2 / (N1)
                EMA9 = bar.close * (k) + Last_EMA9 * (1 - k)
                EMA9_array.append(EMA9)
                print("EMA 9", EMA9)

            if (Tickcounter>N1) & (Tickcounter<N2):
                #print("I am in N2")
                EMA27_array.append(bar.close)
                EMA54_array.append(bar.close)

            if Tickcounter == N2:
                Close_split = close_array[(Tickcounter - N2): (Tickcounter-1)]
                #print("Close array")
                #print(close_array)
                #print(Close_split)
                SMA = (np.sum(Close_split)) / (N2-1)
                EMA27_array.append(SMA)
                EMA27 = SMA
                EMA54_array.append(bar.close)
            if Tickcounter > N2:
                #print("EMA27")
                #print(EMA27_array)
                Last_EMA27 = EMA27_array[Tickcounter - 2]
                k = 2 / (N2)
                EMA27 = bar.close * (k) + Last_EMA27 * (1 - k)
                EMA27_array.append(EMA27)

            if (Tickcounter >N2) & (Tickcounter < N3):
                #print("I am in N3")
                EMA54_array.append(bar.close)
            if Tickcounter == N3:
                #print("Close array")
                #print(close_array)
                Close_split = close_array[(Tickcounter - N3): (Tickcounter - 1)]
                #print(Close_split)
                SMA = (np.sum(Close_split)) / (N3-1)
                EMA54_array.append(SMA)
                EMA54 = SMA
            if Tickcounter > N3:
                #print("EMA54")
                #print(EMA54_array)
                Last_EMA54 = EMA54_array[Tickcounter - 2]
                k = 2 / (N3)
                EMA54 = bar.close * (k) + Last_EMA54 * (1 - k)
                EMA54_array.append(EMA54)

            if (time.mktime(datetime.datetime.strptime(bar.date, '%Y%m%d %H:%M:%S').timetuple()) >= (Time_day_begin)):

                if self.first_time == True:
                    start_price = bar.close
                    print("Start Price = ", start_price)
                    self.first_time = False

                if bar.volume > 0:
                    VSum = VSum + bar.volume
                    #print("Vsum= ", VSum)
                    VPSum = VPSum + (bar.average) * (bar.volume)
                    # print("VPsum= ", VPSum)
                    VWAP = VPSum / VSum
                    # print ("VWAP= " , VWAP)
                    N = N + 1
                    Devsum = Devsum + (bar.average * bar.average * bar.volume)

                    Dev_now = (Devsum / VSum) - (VWAP * VWAP)

                    if Dev_now > 0:
                        Dev = math.sqrt(Dev_now)
                    else:
                        Dev = 0
                    #print("Dev", Dev_now)
                    VWAP_1P = VWAP + .25*Dev
                    VWAP_1N = VWAP - .25*Dev
                    VWAP_2P = VWAP + (2 * Dev)
                    VWAP_2N = VWAP - (2 * Dev)
                    print("Adjusted VWAP = ", VWAP_1P, " ", VWAP_1N)

            if close > VWAP:
                self.AboveVWAP = True
                VWAP_up = VWAP_up + 1
                # Purchase_price = tick.price

            if close < VWAP:
                self.AboveVWAP = False
                VWAP_down = VWAP_down + 1
                # Purchase_price = tick.price

            print ("EMA9 = ", EMA9)
            PnL = (close - Purchase_price)
            #print("Writing to file")
            writefile.writerow([Ticker, (bar.date), Purchase_price, bar.close,
                 (bar.volume), VSum, VWAP, self.AboveVWAP, self.Status, PnL, Tickcounter, VWAP_up, VWAP_down, VWAP_1P,
                 VWAP_2P, VWAP_1N, VWAP_2N, Pre_high, Pre_low, EMA9, EMA27, EMA54, self.EMA_status])
            csvobj.flush()

            # CHANGEME
            if (time.mktime(datetime.datetime.strptime(bar.date, '%Y%m%d %H:%M:%S').timetuple()) > (Time_now_sec - 120)) &(self.Valid_data == True):
                print("Reached Market open Time")
                self.Valid_data = False
                #SUBSCRIBE
                self.cancelHistoricalData(Hist_count)
                if self.Startday == True:
                    print("Volume = ", VSum)
                    print("VWAP up% = ", 100 * (VWAP_up / Tickcounter))
                    # print ("MARKET CAP = ", marketcap)
                    print("Pre High = ", Pre_high)
                    print("Pre Low = ", Pre_low)
                    Perc=abs(100*(bar.close-start_price)/start_price)
                    print ("Percent Change", Perc)
                    # CHANGEME THIS IS FOR BEARISH SCAN

                    Shortable = False

                    if Ticker in Short_dict.keys():
                        if Short_dict[Ticker] >= 100000:
                            Shortable = True
                            print("Shortable")
                        else:
                            print("Not Shortable")
                            Shortable = False

                    if (Ticker in Short_dict.keys()) & (EMA9>EMA27) & (EMA9 > VWAP_1P) & (EMA27>EMA54) & (VSum*bar.close*100>1000000)&(VSum>1000):
                        print("Buy Stock and Starting Real Time Data ")
                        # Purchase_price = tick.price
                        self.Status = "PICK"
                        # AUTO_ORDER
                        self.nextOrderId = self.nextOrderId + 1
                        # self.TickbyTick = False
                        # time.sleep(2)
                        if (bar.close > 1) & (bar.close < 10):
                            Shares = 400
                            Buffer = 2
                        if (bar.close > 10) & (bar.close < 25):
                            Shares = 200
                            Buffer = 1
                        if (bar.close > 25) & (bar.close < 50):
                            Shares = 100
                            Buffer = .5
                        if (bar.close > 50) & (bar.close < 100):
                            Shares = 50
                            Buffer = .3
                        if (bar.close > 100) & (bar.close < 200):
                            Shares = 25
                            Buffer = .2
                        if (bar.close > 200) & (bar.close < 300):
                            Shares = 10
                            Buffer = .1
                        if (bar.close > 200):
                            Shares = 5
                            Buffer = .1

                        # CHANGEME
                        if self.Status == "PICK":

                            self.Valid_data = False
                            self.Short = False
                            self.Startday = True
                            self.Status = 'NEW POSITION'
                            # CHANGEME

                            self.EMA_status = "Long"
                            action = "BUY"
                            #self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC(action, Shares, math.ceil(bar.close)))
                            self.reqRealTimeBars(Stock_ID, Pick, 5, "TRADES", False, [])
                            #self.reqTickByTickData(6666, Pick, "AllLast", 0, False)
                            # print("*****************************")
                            # print("PLACED ORDER")
                            # print("*****************************")
                            # time.sleep(5)
                            # self.Startday = False
                            # CHANGEME
                            # self.Retry = True
                            # self.Status = "OPEN"
                            # self.Startday = True
                            # self.Startday = False
                    else:
                        time.sleep(5)
                        if bar.close > VWAP:
                            print("Price above VWAP")

                        if VSum<5000:

                            print ("Not Enough Volume")

                        self.Retry = True


            if self.Retry == True:
                self.Retry = False
                print("Wait 5 secs")
                time.sleep(5)
                ScanPick = ScanPick + 1
                print("Scan Pick: ", ScanPick)
                if ScanPick == 25:
                    self.StartScanner = True
                    print("Go back to Top")
                    #skip_list = []
                    self.reqScannerSubscription(Scan_ID, scanSub, [], tagvalues)

                Pick = Contract()
                Pick.secType = 'STK'
                Pick.exchange = "SMART"
                Pick.currency = "USD"
                Pick.primaryExchange = "ISLAND"
                try:
                    Pick.symbol = Scan_List[ScanPick]
                except:
                    self.StartScanner = True
                    print("Go back to Top")
                    skip_list = []
                    self.reqScannerSubscription(Scan_ID, scanSub, [], tagvalues)

                tickpick = Scan_List[ScanPick]
                print("Stock Pick = ", Scan_List[ScanPick])
                Ticker = Scan_List[ScanPick]

                Time_now = time.localtime()
                Time_now_sec = time.mktime(Time_now)

                # SUBSCRIBE
                Hist_count = Hist_count+1
                self.reqHistoricalData(Hist_count, Pick, "", "2 D", "5 secs", "TRADES", 0, 1, True, [])

                self.StartTick = True
                self.Processdata = True
                self.Init = True
                self.Valid_data = True
                self.first_time = True

                VSum = 0
                VPSum = 0
                Tickcounter = 0
                VWAP_up = 0
                VWAP_down = 0
                marketcap = 0
                N = 0
                Dev = 0
                Devsum = 0
                VWAP_array = []
                VWAPCount = 0
                slope = 0
                VWAP = 0
                Pre_high = 0
                Pre_low = 0
                close_array = []
                EMA9_array = []
                EMA9 = 0
                EMA27_array = []
                EMA27 = 0
                EMA54_array = []
                EMA54 = 0


    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails,
                    distance: str, benchmark: str, projection: str, legsStr: str):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark,
                            projection, legsStr)
        #        print("ScannerData. ReqId:", reqId, "Rank:", rank, "Symbol:", contractDetails.contract.symbol,
        #              "SecType:", contractDetails.contract.secType,
        #              "Currency:", contractDetails.contract.currency,
        #              "Distance:", distance, "Benchmark:", benchmark,
        #              "Projection:", projection, "Legs String:", legsStr)
        global scancounter
        global tickpick
        global ScanPick
        global Scan_List
        global Time_now
        global Time_now_sec
        global Ticker
        global Pick
        global Hist_count
        #global Scantarget
        global Scan_ID


        if self.StartScanner == True :
            ScanPick = 0
            scancounter = -1
            self.StartScanner = False
            Scan_List = []

        #print("ScannerData. ReqId:", reqId,ScanData(contractDetails.contract, rank))

        scancounter = scancounter +1
        #scancounter = 10
        print ("Scan  Pick Counter ", scancounter)

        Scan_List.append(contractDetails.contract.symbol)

        if scancounter == 25:
            #Scan_List = ['QUMU', 'BLNK', 'BE', 'CTRN', 'HIMX', 'WKHS', 'FRTA', 'VXRT', 'EKSO', 'SURF', 'OPTN']
            print("Scan aborted")
            print(Scan_List)
            #SUBSCRIBE
            self.cancelScannerSubscription(Scan_ID)
            time.sleep(2)
            # Start the first Ticker
            Pick = Contract()
            Pick.secType = 'STK'
            Pick.exchange = "SMART"
            Pick.currency = "USD"
            Pick.primaryExchange = "ISLAND"


            try:
                Pick.symbol = Scan_List[ScanPick]
            except:
                print("Restart Scan")
                print(Scan_List)
                # SUBSCRIBE
                self.cancelScannerSubscription(Scan_ID)
                time.sleep(2)

            tickpick = Scan_List[ScanPick]
            print("Stock Pick = ", Scan_List[ScanPick])
            Ticker = Scan_List[ScanPick]

            Time_now = time.localtime()
            Time_now_sec = time.mktime(Time_now)

            self.StartTick = True
            self.Processdata = True

            # SUBSCRIBE
            Hist_count = Hist_count +1
            self.reqHistoricalData(Hist_count, Pick , "", "2 D", "5 secs", "TRADES", 0, 1, True, [])
            self.Valid_data = True
            #self.reqHistoricalTicks(9000, Pick, time_date," ", 1000, "TRADES", 0, True, [])



    def tickByTickAllLast(self, reqId: int, tickType: int, Time: int, price: float,
                          size: int, tickAtrribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, Time, price, size, tickAtrribLast,
                                  exchange, specialConditions)
        '''
        if tickType == 1:
            print("Last.", end='')
        else:
            print("AllLast.", end='')
        print(" ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(Time).strftime("%Y%m%d %H:%M:%S"),
              "Price:", price, "Size:", size, "Exch:" , exchange,
              "Spec Cond:", specialConditions, "PastLimit:", tickAtrribLast.pastLimit, "Unreported:", tickAtrribLast.unreported)
        '''
        global Shares
        global Final_Price
        global selection2
        global action
        global Tickcounter
        global hr_cnt
        global cnt
        global VSum
        global VPSum
        global WVAP
        global VWAP_1P
        global VWAP_1N
        global VWAP_2P
        global VWAP_2N
        global N
        global Dev
        global Devsum
        global VWAP_array
        global VWAPCount
        global Purchase_price
        global Start
        global Avg_price
        global writefile
        global csvobj
        global Purchase_time
        global news_counter
        global time_date
        global Ticker
        global contract
        global stock
        global count
        global trade_signal
        global EndDate
        global VWAP_up
        global VWAP_down
        global marketcap
        global VWAP_1P_cnt
        global VWAP_2P_cnt
        global VWAP_cnt
        global Pre_high
        global Pre_low
        global Time_bell_1
        global Pick
        global wait_cnt
        global skip_list


        # global contract1
        close = price
        print("Time= ", datetime.datetime.fromtimestamp(Time).strftime("%Y%m%d %H:%M:%S"), "current price = ", price, "Volume = ", size)

        VSum = VSum + size
        # print("Vsum= ", VSum)
        VPSum = VPSum + (price) * (size)
        # print("VPsum= ", VPSum)
        VWAP = VPSum / VSum

        # print ("VWAP= " , VWAP)
        Tickcounter = Tickcounter + 1
        # print(Tickcounter)
        N = N + 1
        VWAPCount = VWAPCount + 1
        VWAP_array.append(VWAP)
        if N >= 5:
            if VWAPCount == 5:
                slope = 1000 * (VWAP_array[N - 1] - VWAP_array[N - 6]) / 5
                VWAPCount = 0
        Devsum = Devsum + (VWAP - price) * (VWAP - price)
        Dev = math.sqrt((Devsum) / N)
        VWAP_1P = VWAP + Dev
        VWAP_1N = VWAP - Dev
        VWAP_2P = VWAP + 2 * Dev
        VWAP_2N = VWAP - 2 * Dev

        #print(N)

        if close > VWAP:
            self.AboveVWAP = True
            VWAP_up = VWAP_up + 1
            # Purchase_price = tick.price

        if close < VWAP:
            self.AboveVWAP = False
            VWAP_down = VWAP_down + 1
            # Purchase_price = tick.price

        PnL = (close - Purchase_price)
        # print(PnL)
        writefile.writerow(
            [Ticker, datetime.datetime.fromtimestamp(Time).strftime("%Y%m%d %H:%M:%S"), Purchase_price, price,
             size, VSum, VWAP, self.AboveVWAP, self.Status, PnL, Tickcounter, VWAP_up, VWAP_down, VWAP_1P, VWAP_2P,
             VWAP_1N, VWAP_2N, Pre_high, Pre_low])
        csvobj.flush()



        if self.Status == "PICK":

            if self.stop_data == False:


                if (price > VWAP) & (price>Pre_high):
                    print("*****************************")
                    print("Price above VWAP & Pre High")
                    print("*****************************")
                    VWAP_1P_cnt = VWAP_1P_cnt + 1
                    if VWAP_1P_cnt>40:
                        VWAP_1P_cnt = 0

                        self.nextOrderId = self.nextOrderId + 1
                        self.cancelTickByTickData(6666)
                        self.TickbyTick = False
                        # time.sleep(2)
                        # CHANGEME
                        self.Status = "NEW POSITION"
                        self.Short = False
                        #CHANGEME
                        #self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("BUY", Shares, (price + .2)))
                        self.stop_data = True
                        print("*****************************")
                        print("OPEN NEW POSITION")
                        print("*****************************")
                        time.sleep(5)

                if (price<Pre_high) & (price>Pre_low):

                        wait_cnt = wait_cnt +1

                        if wait_cnt > 400:
                            skip_list.append(Ticker)
                            wait_cnt = 0
                            self.StartScanner = True
                            print("Go back to Top")
                            self.stop_data = True
                            self.cancelTickByTickData(6666)
                            self.reqScannerSubscription(Scan_ID, scanSub, [], tagvalues)

                if (price < VWAP)&(price<Pre_low):

                    print("*****************************")
                    print("Price below VWAP & Pre_low")
                    print("*****************************")
                    VWAP_1P_cnt = VWAP_1P_cnt + 1
                    if VWAP_1P_cnt > 40:
                        VWAP_1P_cnt = 0

                        self.nextOrderId = self.nextOrderId + 1
                        self.cancelTickByTickData(6666)
                        self.TickbyTick = False
                        # time.sleep(2)
                        # CHANGEME
                        self.Status = "NEW POSITION"
                        self.Short = True
                        #self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("SELL", Shares, (price - .2)))
                        self.stop_data = True
                        print("*****************************")
                        print("OPEN NEW POSITION")
                        print("*****************************")
                        time.sleep(5)

        if self.Status == "FILLED":

            if self.Short == False:

                if self.stop_data == False:

                    if (price * Shares) < .96 * (Final_Price * Shares):
                        print("*****************************")
                        print("Price above Avg Price")
                        print("*****************************")
                        VWAP_1P_cnt = VWAP_1P_cnt + 1
                        if VWAP_1P_cnt > 100:
                            VWAP_1P_cnt = 0

                            self.nextOrderId = self.nextOrderId + 1
                            self.cancelTickByTickData(666)
                            self.TickbyTick = False
                            # time.sleep(2)
                            self.Status = "CLOSED"
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("SELL", Shares, (price - .2)))
                            self.stop_data = True
                            print("*****************************")
                            print("CLOSE POSITION")
                            print("*****************************")
                            time.sleep(5)

                    if self.Percent4 == False:

                        if (price * Shares) > 1.04 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 4 reached Checkpoint")
                            print("*****************************")
                            self.Percent4 = True

                    if self.Percent4 == True:

                        if (price * Shares) < 1.04 * (Final_Price * Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("SEL", Shares, (price - .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT4 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)

                    if self.Percent6 == False:

                        if (price * Shares) > 1.06 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 6 reached Checkpoint")
                            print("*****************************")
                            self.Percent6 = True

                    if self.Percent6 == True:

                        if (price * Shares) < 1.06 * (Final_Price * Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("SELL", Shares, (price - .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT6 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)

                    if self.Percent8 == False:

                        if (price * Shares) > 1.08 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 8 reached Checkpoint")
                            print("*****************************")
                            self.Percent6 = True

                    if self.Percent8 == True:

                        if (price * Shares) < 1.08 * (Final_Price * Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("SELL", Shares, (price - .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT8 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)

            if self.Short == True:

                if self.stop_data == False:

                    if (price*Shares) > 1.04 * (Final_Price*Shares):
                        print("*****************************")
                        print("Price above Avg Price")
                        print("*****************************")
                        VWAP_1P_cnt = VWAP_1P_cnt + 1
                        if VWAP_1P_cnt > 100:
                            VWAP_1P_cnt = 0

                            self.nextOrderId = self.nextOrderId + 1
                            self.cancelTickByTickData(666)
                            self.TickbyTick = False
                            # time.sleep(2)
                            self.Status = "CLOSED"
                            self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("BUY", Shares, (price + .2)))
                            self.stop_data = True
                            print("*****************************")
                            print("CLOSE POSITION")
                            print("*****************************")
                            time.sleep(5)

                    if self.Percent4  == False:

                        if (price * Shares) < .96 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 4 reached Checkpoint")
                            print("*****************************")
                            self.Percent4 = True

                    if self.Percent4 == True:

                        if (price*Shares) > .96 * (Final_Price*Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("BUY", Shares, (price + .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT4 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)

                    if self.Percent6 == False:

                        if (price * Shares) < .94 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 6 reached Checkpoint")
                            print("*****************************")
                            self.Percent6 = True

                    if self.Percent6 == True:

                        if (price * Shares) > .94 * (Final_Price * Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("BUY", Shares, (price + .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT6 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)

                    if self.Percent8 == False:

                        if (price * Shares) < .92 * (Final_Price * Shares):
                            print("*****************************")
                            print("Percent 8 reached Checkpoint")
                            print("*****************************")
                            self.Percent6 = True

                    if self.Percent8 == True:

                        if (price * Shares) > .92 * (Final_Price * Shares):

                            print("*****************************")
                            print("Price below Avg Price")
                            print("*****************************")
                            VWAP_1P_cnt = VWAP_1P_cnt + 1
                            if VWAP_1P_cnt > 3:
                                VWAP_1P_cnt = 0

                                self.nextOrderId = self.nextOrderId + 1
                                self.cancelTickByTickData(666)
                                self.TickbyTick = False
                                # time.sleep(2)
                                self.Status = "CLOSED"
                                self.placeOrder(self.nextOrderId, Pick, OrderSamples.IOC("BUY", Shares, (price + .2)))
                                self.stop_data = True
                                print("*****************************")
                                print("PLACED PERCENT8 ORDER")
                                print("*****************************")

                                print("*****************************")
                                print("CLOSE POSITION")
                                print("*****************************")
                                time.sleep(5)



