import requests
from datetime import timedelta, datetime
import json

from optparse import OptionParser
from oandapyV20 import API
import oandapyV20.endpoints.trades as trades

import oandapyV20.endpoints.positions as positions
from oandapyV20.contrib.requests import MarketOrderRequest
from oandapyV20.contrib.requests import TakeProfitDetails, TrailingStopLossDetails
import oandapyV20.endpoints.orders as orders
import oandapyV20


access_token = '08546c09c623885d199b5b0900dc0cd2-755959840b9c1ddcdf59784060805faf'
acccount_id = '101-003-2891660-002'
instrument = 'USD_JPY'
api = oandapyV20.API(access_token=access_token)

units = 10000
order_id = '939'

#trade hour_parameter
#reversal_frame = [i for i in range(1,19)]
reversal_frame = [i for i in range(1,24)]
#limit/loss
reversal_loss = 0.07
reversal_limit = 0.1
trend_follow_loss = 0.1
trend_follow_limit = 0.15

#rsi_parameter
rsi_15s_short = 0.8
rsi_15s_long = 0.2
#MACD/MA_parameter
MACD_fast = 12
MACD_slow = 26
#MACD_smooth = 9
MA_fast = 10
MA_slow = 20

#max recording
stream_interval = 400

#return lsat transaction IDs
def create_order(limit,loss, units):
    mktOrder = MarketOrderRequest(
        instrument = instrument,
        units = units,
        takeProfitOnFill = TakeProfitDetails(price=limit).data,
        trailingStopLossOnFill=TrailingStopLossDetails(distance=loss,timeInForce='GTC').data,
            )
    r = orders.OrderCreate(acccount_id,data=mktOrder.data)
    try:
        rv = api.request(r)
    except oandapyV20.exceptions.V20Error as err:
        print(r.status_code, err)
    else:
        #print(rv)
        return int(rv["relatedTransactionIDs"][1])

create_order(111,0.07,10000)
