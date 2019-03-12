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
instrument = 'EUR_USD'
api = oandapyV20.API(access_token=access_token)
units = 10000

opening_price = float(open(instrument + '_opening'+'.txt','r').read())

#trade hour_parameter
reversal_frame = [i for i in range(7,13)]

#limit/loss
reversal_loss = 0.0007
reversal_limit = 0.0007
trend_follow_loss = 0.001
trend_follow_limit = 0.0015

#rsi_parameter
rsi_s_short = 0.7
rsi_s_long = 0.3
rsi_15s_short = 0.7
rsi_15s_long = 0.3
rsi_60s_short = 0.7
rsi_60s_long = 0.3
#MACD/MA_parameter
MACD_fast = 12
MACD_slow = 26
MACD_smooth = 9
MA_fast = 10
MA_slow = 20

# compute RSI, output ranges from 0 to 1
def RSI(pricelist):
    diff = [(j-i) for i,j in zip(pricelist, pricelist[1:])]
    U = sum([i for i in diff if i > 0])
    D = sum([abs(i) for i in diff if i < 0])
    return U / (U + D)
    

def connect_to_stream():
	domainDict = {'live':'stream-fxtrade.oanda.com', 'demo': 'stream-fxpractice.oanda.com'}
	environment = 'demo'
	domain = domainDict[environment]
	try:
		s = requests.Session()
		url = ('https://' + domain + '/v3/accounts/{}/pricing/stream').format(acccount_id)
		headers = {'Authorization':'Bearer ' + access_token,
        'X-Accept-Datetime-Format':'RFC3339'}
		params = {'instruments': instrument}
		req = requests.Request('GET', url, headers=headers, params=params)
		pre = req.prepare()
		resp = s.send(pre, stream = True)
		return resp
	except Exception as e:
		s.close()
		print("Caught exception when connecting to stream\n" + str(e)) 

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

#'OPEN' or 'CLOSED'
def check_order_state(order_ID):
    r = trades.TradeDetails(accountID=acccount_id, tradeID=order_ID)
    return api.request(r)['trade']['state']

def demo(displayHeartbeat):
    response = connect_to_stream()
    price_list = []
    time_list = []
    MACD_list = []
    order_ID = '721'
    if response.status_code != 200:
        print(response.text)
        return
    for line in response.iter_lines(1):
        if line:
            try:
                line = line.decode('utf-8')
                msg = json.loads(line)
            except Exception as e:
                print("Caught exception when converting message into json\n" + str(e))
                return

            if "instrument" in msg or "tick" in msg or displayHeartbeat:
                #get the mid-price and time
                dict1 = json.loads(line)
                bids = dict1['bids'][0]['price']
                asks = dict1['asks'][0]['price']

                time = datetime.strptime(dict1['time'][:-7],'%Y-%m-%dT%H:%M:%S.%f') #trucate the time representation
                price = (float(bids) + float(asks)) / 2
                print(price, ' ', time)
                
                #initialize    


def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-b", "--displayHeartBeat", dest = "verbose", action = "store_true", 
                        help = "Display HeartBeat in streaming data")
    displayHeartbeat = False
    (options, args) = parser.parse_args()
    if len(args) > 1:
        parser.error("incorrect number of arguments")
    if options.verbose:
        displayHeartbeat = True
    demo(displayHeartbeat)


if __name__ == "__main__":
    main()
    
