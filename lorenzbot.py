#!/usr/env python3
import datetime
from decimal import *
import logging
import mongoTicker
import os
import poloniex
from pprint import pprint
import psutil
import pymongo
import sys
import time

product = 'BTC_STR'
product_base = 'BTC'
product_trade = 'STR'
#
#sample_array = [(price, amount), (..., ...), ...]
#

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Class definition here



# Custom functions
def base_price():
    print('Stuff & Things')


if __name__ == '__main__':
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

    # Ticker startup
    #wsTicker = mongoTicker.Ticker()

    try:
        #wsTicker.start()
        #time.sleep(3)
        pass
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    while (True):
        try:
            #startup_read = Decimal(wsTicker(product)['last'])
            break
        except:
            logger.warning('Waiting for valid ticker data...')
            #time.sleep(5)

    logger.info('Ticker connection established.')

    # MongoDB startup
    client = pymongo.MongoClient()
    db = client['lorenzbot']

    trade_data = []

    polo = poloniex.Poloniex('QDYU02XD-2GPXRUEO-DBN67ZGB-Z4H198FP', '17a6db6142f1576ec37c4692294d671acb969846939e7ae2e875f27fe6347f88dbcdcd19cff60f5d516ca96ab2c55802e67eceb974f7cce61cbd73180a8729ba')

    try:
        user_fees = polo.returnFeeInfo()
        maker_fee = Decimal(user_fees['makerFee'])
        taker_fee = Decimal(user_fees['takerFee'])
        print('Maker Fee: ' + str(maker_fee))
        print('Taker Fee: ' + str(taker_fee))
        
        user_available_balance = polo.returnAvailableAccountBalances()
        available_balance_exchange = user_available_balance['exchange']
        available_balance_margin = user_available_balance['margin']
        print('Avail. Bal. Exchange: ' + str(available_balance_exchange))
        print('Avail. Bal. Margin:   ' + str(available_balance_margin))
        
        user_tradable_balance = polo.returnTradableBalances()
        tradable_balance = user_tradable_balance[product]
        tradable_balance_base = Decimal(tradable_balance[product_base])
        tradable_balance_trade = Decimal(tradable_balance[product_trade])
        print('returnTradableBalances')
        pprint(tradable_balance)
        print('Base Prod. Balance:  ' + str(tradable_balance_base))
        print('Trade Prod. Balance: ' + str(tradable_balance_trade))
        
        #margin_summary = polo.returnMarginAccountSummary()
        #print('returnMarginAccountSummary')
        #pprint(margin_summary)

        #user_active_loans = polo.returnActiveLoans()
        #print('returnActiveLoans')
        #pprint(user_active_loans)

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        wsTicker.stop()
        time.sleep(3)
        logger.info('Exiting.')
        sys.exit()
