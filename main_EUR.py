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
order_id = '939'

#trade hour_parameter
#reversal_frame = [i for i in range(1,19)]
reversal_frame = [i for i in range(1,24)]
#limit/loss
reversal_loss = 0.0007
reversal_limit = 0.0007
trend_follow_loss = 0.001
trend_follow_limit = 0.0015

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

# compute RSI, output ranges from 0 to 1
def RSI(pricelist):
    diff = [(j-i) for i,j in zip(pricelist, pricelist[1:])]
    U = sum([i for i in diff if i > 0])
    D = sum([abs(i) for i in diff if i < 0])
    return U / (U + D)

def MACD(pricelist, fast, slow, interval):
    fast_avg = sum(pricelist[j] for j in [-interval*i - 1 for i in range(fast,-1,-1)]) / fast
    slow_avg = sum(pricelist[j] for j in [-interval*i - 1 for i in range(slow,-1,-1)]) / slow
    return fast_avg - slow_avg
 
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
def check_order_state(orderID):
    r = trades.TradeDetails(accountID=acccount_id, tradeID=orderID)
    return api.request(r)['trade']['state']

def demo(displayHeartbeat,order_id):
    response = connect_to_stream()
    price_list = []
    time_list = []
    MACD_list = []
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
                if len(price_list) == 0:
                    price_list.append(price)
                    time_list.append(time)
                    price_filled = False
                    print('initialize')
                #process each second, omit response shorter than 1s
                timedel = (time - time_list[-1]) / timedelta(seconds=1)
                if timedel > 1:
                    #unify the interval to each second(as streaming is sporadic)
                    price_list = price_list + [price] * int(timedel - 1)
                    time_list.append(time)
                    print('no of price ', len(price_list))
                    ticker = True
                else:
                    ticker = False
                #fill no more than 840 (14 minutes)
                if len(price_list) > stream_interval:
                    price_list = price_list[-stream_interval:]
                    time_list = time_list[-stream_interval:]
                    price_filled = True
                #check previous order closed or not
                #no trade before price_list is fully filled(14 mins)
                if ticker and price_filled:
                    rsi_15s = RSI([price_list[j] for j in [-15*i-1 for i in range(13,-1,-1)]])
                    MACD_signal = MACD(price_list,MACD_fast,MACD_slow,interval=15)
                    print('rsi_15s: ', rsi_15s)
                    print('MACD: ', MACD_signal)
                    opening_price = float(open(instrument + '_opening'+'.txt','r').read())
                    reversal_valve = datetime.now().hour in reversal_frame
                    order_state = check_order_state(order_id) == 'CLOSED'#'OPEN'/'CLOSED'
                    print('oderID: ',order_id)
                    if order_state:
                        if reversal_valve:
                            #reversal_short
                            if rsi_15s > rsi_15s_short:
                                order_id = create_order(limit=price - reversal_limit, loss=reversal_loss, units=-1*units)
                                print('trade executed')
                            #reversal_long
                            elif rsi_15s < rsi_15s_long:
                                order_id = create_order(limit=price + reversal_limit, loss=reversal_loss, units=units)
                                print('trade executed')
                            else:
                                print('waiting for reversal')
                            #omit order_state to have hedging feature(multiple orders for one instrument)
                        else: #not reverssal
                            #trend follow long
                            #MA_signal = MACD(price_list,MA_fast,MA_slow,interval=15)
                            print('not time for trading')
                    else:
                        print('position opened')
                else:
                    print('filling price histroy')


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
    demo(displayHeartbeat,order_id)


if __name__ == "__main__":
    main()
    
