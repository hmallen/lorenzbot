#!/usr/env python3
import csv
import datetime
from decimal import *
import logging
import mongoTicker
import os
import poloniex
from pprint import pprint
import psutil
#import pymongo
import sys
import time

global balance_base, balance_trade

product = 'BTC_STR'
product_base = 'BTC'
product_trade = 'STR'

loop_time = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Class definition here



# Custom functions
def exec_trade(position, amount, price):
    # Exec trade function
    # INSERT HERE

    if position == 'buy':
        pass
    elif position == 'sell':
        pass
    else:
        logging.error('Unknown argument to exec_trade().')

    print('TRADE: ' + position)


def log_trade():
    with open(log_file, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([datetime.datetime.now(),
                             "{:.8f}".format(btcusdt_market)])


def balance_info():
    global balance_base, balance_trade
    
    available_balances = polo.returnAvailableAccountBalances()

    try:
        balance_base = Decimal(available_balances[product_base])
    except:
        balance_base = Decimal(0)
    try:
        balance_trade = Decimal(available_balances[product_trade])
    except:
        balance_trade = Decimal(0)


def base_price():
    print('Stuff & Things')


mongo_running = False
for proc in psutil.process_iter(attrs=['pid', 'name']):
    if proc.info['name'] == 'mongod':
        mongo_pid = proc.info['pid']
        mongo_running = True
        logger.info('MongoDB running.')
        break
if mongo_running == False:
    logger.error('Mongodb not running. Type \"mongod\" in terminal to start.')
    sys.exit(1)

polo = poloniex.Poloniex('QDYU02XD-2GPXRUEO-DBN67ZGB-Z4H198FP', '17a6db6142f1576ec37c4692294d671acb969846939e7ae2e875f27fe6347f88dbcdcd19cff60f5d516ca96ab2c55802e67eceb974f7cce61cbd73180a8729ba')

user_fees = polo.returnFeeInfo()
maker_fee = Decimal(user_fees['makerFee'])
taker_fee = Decimal(user_fees['takerFee'])
print()
print('Maker Fee: ' + str(maker_fee))
print('Taker Fee: ' + str(taker_fee))

# Ticker startup
wsTicker = mongoTicker.Ticker()

try:
    wsTicker.start()
    time.sleep(3)
    pass
except Exception as e:
    logger.exception(e)
    sys.exit(1)

connection_attempts = 0
while (True):
    if connection_attempts >= 10:
        logger.error('Failed to acquire valid ticker data. Exiting.')
        sys.exit(1)
    try:
        connection_attempts += 1
        startup_read = Decimal(wsTicker(product)['last'])
        break
    except:
        logger.warning('Waiting for valid ticker data...')
        time.sleep(5)

logger.info('Ticker connection established.')

# MongoDB startup
#client = pymongo.MongoClient()
#db = client['lorenzbot']

log_file = 'trade_logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + 'lorenzbot_trade_log.csv'
if not os.path.exists('trade_logs'):
    logger.info('Log directory not found. Creating...')
    os.makedirs('trade_logs')

if __name__ == '__main__':
    while (True):
        try:
            balance_info()
            print()
            print(str(balance_base) + ' ' + product_base)
            print(str(balance_trade) + ' ' + product_trade)

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            wsTicker.stop()
            time.sleep(3)
            logger.info('Exiting.')
            sys.exit()

        time.sleep(loop_time)
