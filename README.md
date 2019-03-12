# oanda_tradebot in mac
step into cron by `crontab -e`
type:

59 4 * * * /bin/bash get_price_EURUSD.sh

it means run the sh script every day at 4:59am, the sh script runs python to get the daily update of EURUSD:

python3 oanda/get_open_price.py 'EUR_USD' > oanda/EUR_USD_opening.txt

The main.py would read in this opening price for reference.
