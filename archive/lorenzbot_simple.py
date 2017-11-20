#!/usr/env python3
import csv
import datetime
from decimal import *
import logging
import os
import poloniex
from pymongo import MongoClient
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_collection():
    datetime_current = datetime.datetime.now().strftime('%m%d%Y_%H%M%S')
    db.create_collection(datetime_current)
    return datetime_current


drop_collections = False

db = MongoClient().lorenzbot

if drop_collections == True:
    logger.info('Dropping all collections from database.')
    for name in db.collection_names():
        db.drop_collection(name)

coll_names = db.collection_names()

try:
    # Retrieve latest collection
    coll_current = coll_names[(len(coll_names) - 1)]
    logger.info('Found existing collection: ' + str(coll_current))
except:
    # If none found, create new
    logger.info('No collections found in database. Creating new...')
    coll_current = create_collection()
    logger.info('Created new collection: ' + str(coll_current))

print('Collections: ' + str(db.collection_names()))
sys.exit()

# View only
#api_key = 'QDYU02XD-2GPXRUEO-DBN67ZGB-Z4H198FP'
#api_secret = '17a6db6142f1576ec37c4692294d671acb969846939e7ae2e875f27fe6347f88dbcdcd19cff60f5d516ca96ab2c55802e67eceb974f7cce61cbd73180a8729ba'
# Trade enabled
api_key = 'FOGUZX5E-HI79NPQ8-M02Q87GS-24GH5XZA'
api_secret = 'ea5151e99c8d9595864f843839f3bacf145cd1c15dfa3f7ae25597c263e5d433537e06a6783267f88ea6350a4d876b48ee6e3f4eb536f01a2d1cd57af13b7baa'

product = 'USDT_STR'
trade_amount = 1    # Amount of trade product to buy at regular intervals

loop_time = 10

# csv log file naming
log_file = 'lorenzbot_simple_log.csv'
#log_file = 'trade_logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + 'lorenzbot_trade_log.csv'

if not os.path.exists('trade_logs'):
    logger.info('Log directory not found. Creating...')
    os.makedirs('trade_logs')

try:
    polo = poloniex.Poloniex(api_key, api_secret)
except:
    logger.exception('Poloniex API key or secret incorrect. Exiting.')
    sys.exit(1)

user_fees = polo.returnFeeInfo()
maker_fee = Decimal(user_fees['makerFee'])
taker_fee = Decimal(user_fees['takerFee'])
logger.info('Current Maker Fee: ' + str(maker_fee))
logger.info('Current Taker Fee: ' + str(taker_fee))


def base_price():
    pass


def exec_trade(position, trade_amount):
    if position == 'buy':
        polo.buy(product, Decimal(polo.returnTicker()[product]['lowestAsk']), Decimal(trade_amount))
    elif position == 'sell':
        pass
    else:
        logger.exception('Unrecognized argument passed to exec_trade().')
    

def calc_trade():
    pass


def log_trade():
    with open(log_file, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        #csv_writer.writerow([datetime.datetime.now(), ])


if __name__ == '__main__':
    while (True):
        print('Stuff')
        
        print()
        print(str(balance_base) + ' ' + product_base)
        print(str(balance_trade) + ' ' + product_trade)

        time.sleep(loop_time)
