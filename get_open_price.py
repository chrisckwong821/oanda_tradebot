import sys
import requests
import json
def get_last_price(instrument):
    #currency_layer
    key = 'QB9Y'
    url = ('https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&'+
        'from_currency={}&to_currency={}&apikey={}').format(instrument[:3],instrument[4:],key)
    r = requests.get(url)
    response = json.loads(r.text)
    rate = float(response['Realtime Currency Exchange Rate']['5. Exchange Rate'])
    print(rate)
    return rate


get_last_price(sys.argv[1])