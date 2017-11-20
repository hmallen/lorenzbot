#!/usr/env python3
import argparse
from configparser import ConfigParser
import csv
import datetime
from decimal import *
import logging
import os
import poloniex
from pymongo import MongoClient
import sys
import textwrap
import time

global coll_current

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    
    ---- Lorenz: Poloniex Trading Bot ----
    
    Set custom values for lorenzbot trading program.
        '''),
    epilog='\r')

parser.add_argument('-c', '--clean', action='store_true', default=False, help='Add argument to drop all collections and start fresh.')
parser.add_argument('-a', '--amount', default=0.1, type=float, help='Set trade amount.')
parser.add_argument('-m', '--max', default=100, type=float, help='Max amount of quote currency allowed for trading.')
parser.add_argument('-p', '--profit', default=0.05, type=float, help='Set profit threshold for sell triggering.')
parser.add_argument('--live', action='store_true', default=False, help='Add flag to enable live trading API keys')
parser.add_argument('--nocsv', action='store_false', default=True, help='Add flag to disable csv logging.')
#parser.add_argument(?? no - or -- ??, default='USDT_STR', help='Manual selection of currency pair for trading.') --> Product selection

logger.debug('Parsing arguments.')
args = parser.parse_args()
clear_collections = args.clean, logger.debug('clear_collections: ' + str(clear_collections))
trade_amount = Decimal(args.amount), logger.debug('trade_amount: ' + str(trade_amount))
trade_max = Decimal(args.max), logger.debug('trade_max: ' + str(trade_max))   # CURRENTLY UNUSED
profit_threshold = Decimal(args.profit), logger.debug('profit_threshold: ' + str(profit_threshold))
live_trading = args.live, logger.debug('live_trading: ' + str(live_trading))   # CURRENTLY UNUSED
csv_logging = args.csv, logger.debug('csv_logging: ' + str(csv_logging))

# Get config file and set program values from it
working_dir = os.listdir()

ini = None
for file in working_dir:
    if file.endswith('.ini'):
        ini = str(file)

if not ini:
    logger.error('No ini configuration file found. Exiting.')
    sys.exit(1)
else:
    config_file = ini
    logger.info('Found config file ' + config_file + '.')

config = configparser.ConfigParser()
config.read(config_file)

if live_trading == True:
    logger.warning('Live trading ENABLED.')
    # Trade enabled
    api_key = config['live']['key']
    api_secret = config['live']['secret']
else:
    logger.info('Live trading disabled.')
    # View only
    api_key = config['view']['key']
    api_secret = config['view']['secret']

# Variable modifiers
product = 'USDT_STR'
loop_time = 60
buy_threshold = Decimal(0.000105)
sell_padding = Decimal(0.9975)  # Proportion of total amount bought to sell when triggered
mongo_failures = 0

# NEED ACCOUNT BALANCE CHECKING ON STARTUP


def modify_collections(action):
    if action == 'create':
        global coll_current

        #coll_current = 'lorenzbot_collection'
        coll_current = datetime.datetime.now().strftime('%m%d%Y_%H%M%S')
        
        db.create_collection(coll_current)
        
        logger.info('Created new collection: ' + coll_current)

    elif action == 'drop':
        for name in db.collection_names():
            db.drop_collection(name)
            logger.debug('Dropped collection: ' + name)


if csv_logging == True:
    log_file = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '_polo_arbitrage_log.csv'
    if not os.path.exists('logs'):
        logger.info('Log directory not found. Creating...')
        os.makedirs('logs')

b = MongoClient().lorenzbot

coll_names = db.collection_names()

if clear_collections == True:
    logger.info('Dropping all collections from database.')
    modify_collections('drop')
    logger.info('Process complete. Restart program without boolean switch.')
    # COULD JUST PROCEED WITH MAIN PROGRAM...
    sys.exit()

else:
    try:
        # Try to retrieve latest collection
        coll_current = coll_names[(len(coll_names) - 1)]
        logger.info('Found existing collection: ' + str(coll_current))
    except:
        # If none found, create new
        logger.info('No collections found in database. Creating new...')
        modify_collections('create')

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

    logger.debug('amount_spent:  ' + str(amount_spent))
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

    amount_bought = amount_bought * sell_padding # Not necessarily needed, but gives some padding
    
    return amount_bought


# NEED TO FIX THE BUY/SELL FUNCTIONS
def exec_trade(position, price_limit=None):
    if position == 'buy':
        trade_response = polo.buy('USDT_STR', price_limit, trade_amount, 'immediateOrCancel')
        order_details = process_trade_response(trade_response, position)
        logger.debug('order_details: ' + str(order_details))

        try:
            mongo_response = db[coll_current].insert_one({'amount': float(order_details['amount']), 'price': float(order_details['rate'])})
            logger.debug('mongo_response: ' + str(mongo_response))
        except:
            logger.exception('Failed to write to MongoDB log!')
            mongo_failures += 1
        # Add some try/except or if result == '????' to ensure successful write

    elif position == 'sell':
        pass
    
    if csv_logging == True:
        log_trade_csv(order_details)

    # FEE INFO #
    # Buys:  taker_fee * STR
    # Sells: taker_fee * USDT


def process_trade_response(order_response, order_position):
    amount_unfilled = Decimal(order_response['amountUnfilled'])
    
    order_trades = polo.returnOrderTrades(order_response['orderNumber'])
    logger.debug('returnOrderTrades: ' + str(r))

    order_list = []
    trade_total = Decimal(0)
    for x in range(0, len(order_trades)):
        order_rate = Decimal(order_trades[x]['rate'])
        order_amount = Decimal(order_trades[x]['amount'])
        order_fee = Decimal(1) - Decimal(order_trades[x]['fee'])
        
        trade_total = (order_rate * order_amount) * order_fee
        
        order_list.append((order_rate, trade_total))

    rate_calc_total = Decimal(0)
    amount_total = Decimal(0)
    for x in range(0, len(order_list)):
        rate_calc_total += order_list[x][0] * order_list[x][1]
        amount_total += order_list[x][1]
    order_average_rate = rate_calc_total / amount_total

    logger.debug('Tot/Unfilled Difference: ' + str((trade_amount - amount_unfilled) - amount_total))
    
    return {'amount': amount_total, 'rate': order_average_rate}


def log_trade_csv(csv_row): # Must pass list as argument
    logger.info('Logging trade details to csv.')
    with open(log_file, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([csv_row])


if __name__ == '__main__':
    while (True):
        try:
            # Calculate base price
            base_price = calc_base()
            base_price_trigger = base_price - buy_threshold

            ob = polo.returnOrderBook('USDT_STR')
            lowest_ask = Decimal(ob['asks'][0][0])
            lowest_ask_volume = Decimal(ob['asks'][0][1])
            highest_bid = Decimal(ob['bids'][0][0])
            #highest_bid_volume = Decimal(ob['bids'][0][1])
                        
            lowest_ask_actual = lowest_ask / (Decimal(1) - taker_fee)
            sell_price_calc = base_price * (Decimal(1) + profit_threshold)

            logger.debug('base_price:         ' + "{:.8f}".format(base_price))
            logger.debug('base_price_trigger: ' + "{:.8f}".format(base_price_trigger))
            logger.debug('lowest_ask_actual:  ' + "{:.8f}".format(lowest_ask_actual))
            logger.debug('Difference:         ' + "{:.8f}".format(base_price - lowest_ask_actual))
            logger.debug('sell_price_calc:    ' + "{:.8f}".format(sell_price_calc))

            if highest_bid >= sell_price_calc and lowest_ask_volume >= trade_amount:
                logger.debug('TRADE CONDITIONS MET ---> SELLING')
                exec_trade('sell')
                modify_collections('drop')
                modify_collections('create')
                
            elif lowest_ask_actual < base_price_trigger:
                logger.debug('TRADE CONDITIONS MET ---> BUYING')
                exec_trade('buy', base_price_trigger)

            #trade_amount_adjust()
            #loop_time_adjust()
                

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')
            logger.info('Mongo Write Errors: ' + str(mongo_failures))
            sys.exit(0)

        time.sleep(loop_time)
