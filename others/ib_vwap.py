# -*- coding: utf-8 -*-
"""
IB API - Calculate VWAP and 2 standard deviation lines using historical data

"""
# Import libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import threading
import time
import numpy as np
import math

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
        print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(reqId,bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def histData(req_num,contract,duration,candle_size):
    """extracts historical data"""
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='ADJUSTED_LAST',
                          useRTH=0,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[])	 # EClient function to request contract details

def websocket_con():
    app.run()
    
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established

tickers = ["SEAC", "SPY"]
for ticker in tickers:
    histData(tickers.index(ticker),usTechStk(ticker),'1 D', '1 min')
    time.sleep(3)

###################storing trade app object in dataframe#######################
def dataDataframe(symbols,TradeApp_obj):
    "returns extracted historical data in dataframe format"
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date",inplace=True)
    return df_data
###############################################################################

def VWAP(DF,n=5):
    "function to VWAP"
    df = DF.copy()
    #df["MA"] = df['close'].rolling(n).mean()
    df['Avg'] = (df['High'] + df['Low'] + df['Close'])/3
    df['Cum_Vol'] = df['Volume'].cumsum()
    df["Vol_Price"] = df['Volume']*df['Avg']
    df["Vol_Price2"] = df['Volume'] * df['Avg']*df['Avg']
    df["Cum_VP"] = df["Vol_Price"].cumsum()
    df["Cum_VP2"] = df["Vol_Price2"].cumsum()
    df["VWAP"] = df['Cum_VP']/df['Cum_Vol']
    '''df["Dev"] = math.sqrt(max((df["Cum_VP2"]/df['Cum_Vol'])-(df["VWAP"]*df["VWAP"]),0))
    df["VWAP_up1"] = df["VWAP"] + 1 * df["Dev"]
    df["VWAP_dn1"] = df["VWAP"] - 1 * df["Dev"]
    df["VWAP_up2"] = df["VWAP"] + 2 * df["Dev"]
    df["VWAP_dn2"] = df["VWAP"] - 2 * df["Dev"]'''
    df.dropna(inplace=True)
    return df

#extract and store historical data in dataframe
historicalData = dataDataframe(tickers,app)

#calculate and store MACD values
TI_dict = {}

for ticker in tickers:
    TI_dict[ticker] = VWAP(historicalData[ticker],3)

TI_dict['SPY'].to_csv('VWAP.csv')