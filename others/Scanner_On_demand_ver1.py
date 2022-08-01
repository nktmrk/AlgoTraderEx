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

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.utils import iswrapper
from ibapi.common import *                                  # @UnusedWildImport
from ibapi.order_condition import *                         # @UnusedWildImport
from ibapi.contract import *                                # @UnusedWildImport
from ibapi.order import *                                   # @UnusedWildImport
from ibapi.order_state import *                             # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.ticktype import *                                # @UnusedWildImport
from ibapi.tag_value import TagValue
from ibapi.scanner import ScanData
from ibapi.object_implem import Object
from ibapi.scanner import ScannerSubscription
from ibapi.account_summary_tags import *

from OrderSamples import OrderSamples


class IBPy(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails,
                    distance: str, benchmark: str, projection: str, legsStr: str):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark, projection, legsStr)
        '''print("ScannerData. ReqId:", reqId, "Rank:", rank, "Symbol:", contractDetails.contract.symbol,
                  "SecType:", contractDetails.contract.secType,
                 "Currency:", contractDetails.contract.currency,
                 "Distance:", distance, "Benchmark:", benchmark,
                 "Projection:", projection, "Legs String:", legsStr)'''
        scanList.append(contractDetails.contract.symbol)

    def scannerDataEnd(self, reqId: int):
        super().scannerDataEnd(reqId)

        print("Stock Pick List = ", scanList)
        self.cancelScannerSubscription(5009)


app = IBPy()
app.connect("127.0.0.1", 4002, 108)

scanList = []

scanSub = ScannerSubscription()
scanSub.instrument = "STK"
scanSub.locationCode = "STK.US.MAJOR"
scanSub.scanCode = "MOST_ACTIVE"

tagValues = [TagValue("usdMarketCapAbove", "500000"), TagValue("priceAbove", "2"), TagValue("priceBelow", "1000"),
             TagValue("volumeAbove", "1000")]

app.reqScannerSubscription(5009, scanSub, [], tagValues)
app.run()