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

global coll_current

clear_collections = False    # Set True to clear collections and start fresh
# NEED ACCOUNT BALANCE CHECKING ON STARTUP

# Variable modifiers
product = 'USDT_STR'
trade_amount = Decimal(1)    # Amount of trade product to buy at regular intervals
trade_max = 100
loop_time = 60
profit_threshold = Decimal(0.05)
buy_threshold = Decimal(0.000105)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_collection():
    global coll_current
    
    #coll_current = datetime.datetime.now().strftime('%m%d%Y_%H%M%S')
    coll_current = 'lorenzbot_collection'
    db.create_collection(coll_current)
    logger.info('Created new collection: ' + coll_current)


def drop_collections():
    for name in db.collection_names():
        db.drop_collection(name)
        logger.debug('Dropped collection: ' + name)


db = MongoClient().lorenzbot

coll_names = db.collection_names()

if clear_collections == True:
    logger.info('Dropping all collections from database.')
    drop_collections()
    logger.info('Process complete. Please switch drop_collections to \'False\' and restart program.')
    sys.exit()
else:
    try:
        # Retrieve latest collection
        coll_current = coll_names[(len(coll_names) - 1)]
        logger.info('Found existing collection: ' + str(coll_current))
    except:
        # If none found, create new
        logger.info('No collections found in database. Creating new...')
        create_collection()

# View only
#api_key = 'QDYU02XD-2GPXRUEO-DBN67ZGB-Z4H198FP'
#api_secret = '17a6db6142f1576ec37c4692294d671acb969846939e7ae2e875f27fe6347f88dbcdcd19cff60f5d516ca96ab2c55802e67eceb974f7cce61cbd73180a8729ba'
# Trade enabled
api_key = 'FOGUZX5E-HI79NPQ8-M02Q87GS-24GH5XZA'
api_secret = 'ea5151e99c8d9595864f843839f3bacf145cd1c15dfa3f7ae25597c263e5d433537e06a6783267f88ea6350a4d876b48ee6e3f4eb536f01a2d1cd57af13b7baa'

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

# DELAY TO READ LOG MESSAGES
time.sleep(3)


def calc_base():
    logger.debug('Entering base_price calculation.')
    
    while (True):
        # Total amount spent
        pipeline = [{
        '$project': {
            '_id': None,
            'amount_spent': {
                '$multiply': [ '$amount', '$price' ]
                }
            }}]
        agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']

        trade_log_length = len(agg)
        logger.debug('Trade log length: ' + str(len(agg)))
        
        if trade_log_length == 0:
            logger.warning('No trade log found. Making entry buy.')
            exec_trade('buy')
        else:
            break

    amount_spent = Decimal(0)
    for x in range(0, len(agg)):
        amount_spent += Decimal(agg[x]['amount_spent'])

    # Total amount bought
    pipeline = [{
        '$group': {
            '_id': None,
            'amount_bought': {'$sum': '$amount'}
            }
        }]
    agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']
    logger.debug('agg: ' + str(agg))

    amount_bought = Decimal(agg[0]['amount_bought'])
    logger.debug('agg[0][\'amount_bought\']: ' + "{:.8f}".format(agg[0]['amount_bought']))

    weighted_avg = amount_spent / amount_bought

    #logger.debug('amount_spent:  ' + str(amount_spent))
    logger.debug('amount_bought: ' + "{:.8f}".format(amount_bought))
    logger.debug('weighted_avg:  ' + "{:.8f}".format(weighted_avg))

    return weighted_avg


def sell_amount():
    # Total amount bought
    pipeline = [{
        '$group': {
            '_id': None,
            'amount_bought': {'$sum': '$amount'}
            }
        }]
    agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']
    logger.debug('agg: ' + str(agg))

    amount_bought = Decimal(agg[0]['amount_bought'])
    logger.debug('agg[0][\'amount_bought\']: ' + "{:.8f}".format(agg[0]['amount_bought']))

    amount_bought = amount_bought * Decimal(0.9975) # Not necessarily needed, but gives some padding
    
    return amount_bought


# NEED TO FIX THE BUY/SELL FUNCTIONS
def exec_trade(position):
    if position == 'buy':
        logger.info('Executing ' + position + ' trade.')

        ticker = polo.returnTicker()['USDT_STR']
        #response = {'total': str(Decimal(ticker['lowestAsk']) * trade_amount), 'rate': ticker['lowestAsk']}
        response = polo.buy(product, polo.returnTicker()[product]['lowestAsk'], trade_amount)
        logger.debug('response: ' + str(response))
        
        trade_net = Decimal(trade_amount) - (Decimal(trade_amount) * taker_fee)

        # Store trade details in current MongoDB collection
        result = db[coll_current].insert_one({'amount': float(trade_net), 'price': float(ticker['lowestAsk'])})
        logger.debug(result)
        
    elif position == 'sell':
        logger.info('Executing ' + position + ' trade.')

        ticker = polo.returnTicker()['USDT_STR']
        #response = {'total': str(Decimal(ticker['highestBid']) * trade_amount), 'rate': ticker['highestBid']}
        response = polo.sell(product, polo.returnTicker()[product]['highestBid'], sell_amount())
        logger.debug(response)
        
        trade_net = Decimal(response['total']) * (Decimal(1) - taker_fee)

        # Store trade details in current MongoDB collection
        result = db[coll_current].insert_one({'amount': float(trade_net), 'price': float(ticker['highestBid'])})
        logger.debug(result)
            
    else:
        logger.exception('Unrecognized argument passed to exec_trade().')
    
    logger.debug(response)

    # FEE INFO #
    # Buys:  taker_fee * STR
    # Sells: taker_fee * USDT
    # Add some try/except or if result == '????' to ensure successful write


if __name__ == '__main__':
    while (True):
        try:
            # Calculate base price
            base_price = calc_base()

            ticker = polo.returnTicker()['USDT_STR']
            lowest_ask = Decimal(ticker['lowestAsk'])
            highest_bid = Decimal(ticker['highestBid'])

            lowest_ask_actual = lowest_ask / (Decimal(1) - taker_fee)

            logger.debug('base_price:        ' + "{:.8f}".format(base_price))#"{:.8f}".format(base_price))
            logger.debug('lowest_ask_actual: ' + "{:.8f}".format(lowest_ask_actual))#"{:.8f}".format(lowest_ask_actual))
            logger.debug('Difference:        ' + "{:.8f}".format(base_price - lowest_ask_actual))#"{:.8f}".format(base_price - lowest_ask_actual))

            sell_price_calc = base_price * (Decimal(1) + profit_threshold)
            logger.debug('sell_price_calc:   ' + "{:.8f}".format(sell_price_calc))

            if highest_bid > sell_price_calc:
                exec_trade('sell')
                drop_collections()
                create_collection()
                
            elif lowest_ask_actual < (base_price - buy_threshold):
                logger.debug('TRADE CONDITIONS MET --> BUYING')
                exec_trade('buy')

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')
            sys.exit(0)

        time.sleep(loop_time)
