#!/usr/env python3
import datetime
from decimal import *
import logging
import os
import poloniex
from pymongo import MongoClient
import sys
import time

global coll_current

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_collection():
    global coll_current
    
    datetime_current = datetime.datetime.now().strftime('%m%d%Y_%H%M%S')
    db.create_collection(datetime_current)
    coll_current = datetime_current


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
    create_collection()
    logger.info('Created new collection: ' + str(coll_current))

# View only
#api_key = 'QDYU02XD-2GPXRUEO-DBN67ZGB-Z4H198FP'
#api_secret = '17a6db6142f1576ec37c4692294d671acb969846939e7ae2e875f27fe6347f88dbcdcd19cff60f5d516ca96ab2c55802e67eceb974f7cce61cbd73180a8729ba'
# Trade enabled
api_key = 'FOGUZX5E-HI79NPQ8-M02Q87GS-24GH5XZA'
api_secret = 'ea5151e99c8d9595864f843839f3bacf145cd1c15dfa3f7ae25597c263e5d433537e06a6783267f88ea6350a4d876b48ee6e3f4eb536f01a2d1cd57af13b7baa'

product = 'USDT_STR'

trade_amount = 1    # Amount of trade product to buy at regular intervals

loop_time = 10

try:
    polo = poloniex.Poloniex(api_key, api_secret)
except:
    logger.exception('Poloniex API key and/or secret incorrect. Exiting.')
    sys.exit(1)

user_fees = polo.returnFeeInfo()
maker_fee = Decimal(user_fees['makerFee'])
taker_fee = Decimal(user_fees['takerFee'])
logger.info('Current Maker Fee: ' + str(maker_fee))
logger.info('Current Taker Fee: ' + str(taker_fee))


def base_price():
    # Calculate base price from logged trades
    #pipeline = [{'$group': {'_id': None, 'mean': {'$avg': '$x'}}}]  # NEED TO FIX
    pipeline = [{
    '$project': {
        '_id': None,
        'weighted_tot': {
            '$multiply': [ '$amount', '$price' ]
            }
        }}]
    agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']

    result_tot = Decimal(0)
    for x in range(0, len(agg)):
        result_tot += Decimal(agg[x]['weighted_tot'])
    weighted_avg = result_tot / Decimal(len(agg))

    return weighted_avg


# NEED TO FIX THE BUY/SELL FUNCTIONS
def exec_trade(position, amount):
    if position == 'buy':
        polo.buy(product, Decimal(polo.returnTicker()[product]['lowestAsk']), Decimal(trade_amount))
    elif position == 'sell':
        pass
    else:
        logger.exception('Unrecognized argument passed to exec_trade().')


def log_trade(amount, price):
    # Store trade details in current MongoDB collection
    result = db.coll_current.insert_one({'amount': amount, 'price': price})
    # Add some try/except or if result == '????' to ensure successful write


if __name__ == '__main__':
    while (True):
        print('Stuff')
        
        print()
        print(str(balance_base) + ' ' + product_base)
        print(str(balance_trade) + ' ' + product_trade)

        time.sleep(loop_time)
