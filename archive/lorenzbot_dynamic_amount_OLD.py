#!/usr/env python3
import argparse
import configparser
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variable modifiers
product = 'USDT_STR'
loop_time_min = Decimal(6) # Minimum allowed loop time with dynamic adjustment (seconds)

buy_threshold = Decimal(0.000105)
sell_padding = Decimal(0.9975)  # Proportion of total amount bought to sell when triggered

# System variables (Do not change)
calc_base_initialized = False   # Needed to prevent infinite loop b/w calc_base() and exec_trade() on entry buy
buy_skips = 0
mongo_failures = 0
csv_failures = 0

# Handle argument parsing
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    
    ---- Lorenz: Poloniex Trading Bot ----
    
    Set custom values for lorenzbot trading program.
        '''),
    epilog='\r')

# Define arguments that can be passed to program
parser.add_argument('-c', '--clean', action='store_true', default=False, help='Add argument to drop all collections and start fresh. [Default = False]')

parser.add_argument('-a', '--amount', default=0.1, type=float, help='Set static base amount of quote product to trade. [Default = 0.1]')
parser.add_argument('--dynamicamount', action='store_true', default=False, help='Add flag to dynamically set trade amount based on current conditions.')
parser.add_argument('-i', '--initial', default=0.05, type=float, help='Set proportion of total funds to use for initial buy. [Default = 0.05]')

parser.add_argument('-m', '--max', default=1.0, type=float, help='Total amount of USDT to use for trading. [Default = 1.0]')
parser.add_argument('-p', '--profit', default=0.05, type=float, help='Set profit threshold for sell triggering. [Default = 0.05]')

parser.add_argument('-l', '--loop', default=60, type=float, help='Main program loop time (seconds). [Default = 60]')
parser.add_argument('--dynamicloop', action='store_true', default=False, help='Add flag to dynamically set loop time based on current conditions.')

parser.add_argument('--live', action='store_true', default=False, help='Add flag to enable live trading API keys.')
parser.add_argument('--nocsv', action='store_false', default=True, help='Add flag to disable csv logging.')
parser.add_argument('--debug', action='store_true', default=False, help='Add flag to include debug level output to console.')

# Parse arguments passed to program
logger.debug('Parsing arguments.')
args = parser.parse_args()

# Set variables from arguments passed to program
debug = args.debug
if debug == True:
    logger.setLevel(logging.DEBUG)
    logger.debug('Activated debug logging.')

clean_collections = args.clean; logger.debug('clean_collections: ' + str(clean_collections))

trade_amount = Decimal(args.amount); logger.debug('trade_amount: ' + "{:.2f}".format(trade_amount))
amount_dynamic = args.dynamicamount; logger.debug('amount_dynamic: ' + str(amount_dynamic))
trade_proportion_initial = Decimal(args.initial); logger.debug('trade_proportion_initial: ' + "{:.2f}".format(trade_proportion_initial))

trade_usdt_max = Decimal(args.max); logger.debug('trade_usdt_max: ' + "{:.2f}".format(trade_usdt_max))
profit_threshold = Decimal(args.profit); logger.debug('profit_threshold: ' + "{:.2f}".format(profit_threshold))

loop_time = Decimal(args.loop); logger.debug('loop_time: ' + str(loop_time))
loop_dynamic = args.dynamicloop; logger.debug('loop_dynamic: ' + str(loop_dynamic))

live_trading = args.live; logger.debug('live_trading: ' + str(live_trading))
csv_logging = args.nocsv; logger.debug('csv_logging: ' + str(csv_logging))

# Handle all of the arguments delivered appropriately
if trade_usdt_max > Decimal(10):
    logger.warning('Total USDT trade amount set to a high value. Confirm before continuing.')
if trade_amount > Decimal(10):
    logger.warning('Total STR trade amount set to a high value. Confirm before continuing.')
    user_confirm = input('Continue? (y/n): ')

    if user_confirm == 'y':
        logger.info('Confirmed. Starting program.')
    elif user_confirm == 'n':
        logger.warning('Startup cancelled by user. Exiting.')
        sys.exit()
    else:
        logger.error('Unrecognized user input. Exiting.')
        sys.exit(1)

if loop_dynamic == True:
    logger.info('Dynamic loop time calculation activated. Base loop time set to ' + str(loop_time) + ' seconds.')
else:
    logger.info('Using fixed loop time of ' + str(loop_time) + ' seconds.')

if csv_logging == True:
    log_file = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '_lorenzbot_log.csv'
    logger.info('CSV log file path: ' + log_file)
    if not os.path.exists('logs'):
        logger.info('Log directory not found. Creating...')
        os.makedirs('logs')


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


def get_balances():
    user_balances = polo.returnAvailableAccountBalances()['exchange']
    bal_str = Decimal(user_balances['STR'])
    bal_usdt = Decimal(user_balances['USDT'])
    
    bal_dict = {'str': bal_str, 'usdt': bal_usdt}

    return bal_dict


def calc_base():
    logger.debug('Entering base_price calculation.')
    
    while (True):
        trade_log_length = db[coll_current].count()
        logger.debug('MongoDB collection length: ' + str(trade_log_length))
        
        if trade_log_length == 0:
            if amount_dynamic == True:
                trade_amount_initial = trade_usdt_max * trade_proportion_initial
            else:
                trade_amount_initial = trade_amount
            logger.debug('trade_amount_initial: ' + "{:.2f}".format(trade_amount_initial))
            
            logger.info('No trade log found. Making entry buy.')
            try:
                limit_price = calc_limit_price(trade_amount_initial, 'buy')
                logger.debug('limit_price: ' + "{:.8f}".format(limit_price))
                exec_trade('buy', limit_price, trade_amount_initial)
            except:
                logger.exception('Entry buy failed. Exiting.')
                sys.exit(1)
            
        else:
            break

    calc_base_initialized = True

    #total_spent = calc_trade_totals('spent')['trade_total']
    #logger.debug('total_spent: ' + "{:.8f}".format(total_spent))

    #total_bought = calc_trade_totals('bought')['trade_total']
    #logger.debug('total_bought: ' + "{:.2f}".format(total_bought))

    rate_avg = calc_trade_totals('spent') / calc_trade_totals('bought')
    logger.debug('rate_avg: ' + "{:.8f}".format(rate_avg))

    return rate_avg


def calc_trade_totals(position):
    if position == 'bought':
        pipeline = [{
            '$group': {
                '_id': None,
                'total_bought': {'$sum': '$amount'}
                }
            }]
        agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']
        logger.debug('agg: ' + str(agg))

        trade_total = Decimal(agg[0]['total_bought'])
        #trade_total = trade_total * sell_padding # Not necessarily needed, but gives some padding

    elif position == 'spent':
        pipeline = [{
            '$project': {
                '_id': None,
                'total_spent': {'$multiply': ['$amount', '$price']}
                }
            }]
        agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']
        
        trade_total = Decimal(0)
        for x in range(0, len(agg)):
            trade_total += Decimal(agg[x]['total_spent'])

    logger.debug('trade_total[' + position + ']: ' + "{:.8f}".format(trade_total))
    
    return trade_total


####
# Improve this function by returning weighted average of exec price based on trade amount!!!!
####
def calc_limit_price(amount, position, withFees=None):
    # NEED HANDLING FOR IMPOSSIBLE SITUATIONS
    if position == 'buy':
        book_pos = 'asks'
    elif position == 'sell':
        book_pos = 'bids'

    book_depth = 20  # Default
    while (True):
        book = polo.returnOrderBook('USDT_STR', depth=book_depth)
        
        book_tot = Decimal(0)
        for x in range(0, len(book[book_pos])):
            book_tot += Decimal(book[book_pos][x][1])
            if book_tot >= amount:
                price_actual = Decimal(book[book_pos][x][0])
                logger.debug('price_actual: ' + "{:.8f}".format(price_actual))
                logger.debug('book_tot: ' + "{:.2f}".format(book_tot))
                break
            else:
                price_actual = 0

        if price_actual > 0:
            logger.debug('calc_limit_price() successful within limits (depth=' + str(book_depth) + ').')
            break
        
        else:
            book_depth += 20

            # NEED TO FIGURE OUT HOW TO HANDLE THIS!!!!
            if book_depth > 100:
                #logger.exception('Failed to set price_actual in calc_limit_price().')
                logger.exception('Failed to set price_actual in calc_limit_price(). Exiting.')
                sys.exit(1)
            
            logger.warning('Volume not satisfied at default order book depth=' + str(book_depth - 20) + '. Retrying with depth = ' + str(book_depth) + '.')
            time.sleep(1)

    logger.debug('[' + position + ']price_actual: ' + "{:.8f}".format(price_actual))

    if withFees:
        logger.debug('Adding fees to calc_limit_price() return value.')
        if position == 'buy':
            price_actual = price_actual * (Decimal(1) + taker_fee)
        elif position == 'sell':
            price_actual = price_actual * (Decimal(1) - taker_fee)
        logger.debug('[' + position + ']price_actual[+FEES]: ' + "{:.8f}".format(price_actual))

    return price_actual


# NEED TO FIX THE BUY/SELL FUNCTIONS
def exec_trade(position, limit, amount):    
    if calc_base_initialized == True:
        base_price_initial = calc_base()
    else:
        base_price_initial = 0
        
    if position == 'buy':
        trade_response = polo.buy('USDT_STR', limit, amount, 'immediateOrCancel')
        logger.debug('[BUY] trade_response: ' + str(trade_response))
        
        order_details = process_trade_response(trade_response, position)
        logger.debug('[BUY] order_details: ' + str(order_details))

        try:
            mongo_response = db[coll_current].insert_one({'amount': float(order_details['amount']), 'price': float(order_details['rate']), 'side': position, 'date': order_details['date']})
            logger.debug('[BUY] mongo_response: ' + str(mongo_response))
        except:
            logger.exception('[BUY] Failed to write to MongoDB log!')
            mongo_failures += 1
        
    elif position == 'sell':
        sell_amount = calc_trade_totals('bought')
        logger.debug('sell_amount: ' + "{:.2f}".format(sell_amount))

        account_balances = get_balances()
        balance_str = account_balances['str']

        if balance_str < sell_amount:
            logger.warning('Account balance now less than total bought. Adjusting sell amount to current balance.')
            sell_amount = balance_str
            logger.warning('New sell amount: ' + "{:.2f}".format(sell_amount))
        
        trade_response = polo.sell('USDT_STR', limit, sell_amount, 'immediateOrCancel')  # CHANGE TO REGULAR LIMIT ORDER?
        logger.debug('[SELL] trade_response: ' + str(trade_response))

        amount_unfilled = Decimal(response['amountUnfilled'])
        logger.debug('amount_unfilled: ' + "{:.2f}".format(amount_unfilled))
        
        order_details = process_trade_response(trade_response, position)
        logger.debug('[SELL] order_details: ' + str(order_details))

        try:
            mongo_response = db[coll_current].insert_one({'amount': float(order_details['amount']), 'price': float(order_details['rate']), 'side': position, 'date': order_details['date']})
            logger.debug('[SELL] mongo_response: ' + str(mongo_response))
        except:
            logger.exception('[SELL] Failed to write to MongoDB log!')
            mongo_failures += 1

        modify_collections('create')    # Create new collection
        
        # If order not completely filled, handle unfilled amount
        if amount_unfilled > Decimal(0):
            # Create new collection and add amount_unfilled as buy in MongoDB for base_price calculation
            try:
                mongo_response = db[coll_current].insert_one({'amount': float(amount_unfilled), 'price': float(base_price_initial), 'side': 'buy', 'date': order_details['date']})
                logger.debug('[UNFILLED/NEW] mongo_response: ' + str(mongo_response))
            except:
                logger.exception('[UNFILLED/NEW] Failed to write to MongoDB log!')
                mongo_failures += 1
        
        else:
            logger.debug('Sell completely filled. New collection starting empty.')

    if csv_logging == True:
            csv_list = [order_details['date'],
                        position,
                        "{:.8f}".format(order_details['amount']),
                        "{:.8f}".format(order_details['rate']),
                        "{:.8f}".format(base_price_initial),
                        "{:.8f}".format(calc_base())]
            logger.debug('csv_list: ' + str(csv_list))
            log_trade_csv(csv_list)


def process_trade_response(response, position):
    order_trades = polo.returnOrderTrades(response['orderNumber'])
    trade_date = order_trades[(len(order_trades) - 1)]['date']
    logger.debug('returnOrderTrades: ' + str(order_trades))
    logger.debug('trade_date: ' + trade_date)

    # FEE INFO #
    # Buys:  STR x (1 - taker_fee)
    # Sells: USDT x (1 - taker_fee)

    # Build list with rates and actual trade amounts (trade amounts - fee)
    order_list = []
    logger.debug('len(order_trades): ' + str(len(order_trades)))
    for x in range(0, len(order_trades)):
        if position == 'buy':
            order_rate = Decimal(order_trades[x]['rate'])
            order_amount = Decimal(order_trades[x]['amount']) * (Decimal(1) - Decimal(order_trades[x]['fee']))

        elif position == 'sell':
            order_rate = ((Decimal(order_trades[x]['amount']) * Decimal(order_trades[x]['rate'])) * (Decimal(1) - Decimal(order_trades[x]['fee']))) / Decimal(order_trades[x]['amount'])
            order_amount = Decimal(order_trades[x]['amount'])
        
        order_list.append([order_amount, order_rate])

    logger.debug('len(order_list): ' + str(len(order_list)))
    logger.debug('order_list: ' + str(order_list))

    # Sum amounts bought and calculate weighted average of rate
    amount_total = Decimal(0)
    rate_calc_total = Decimal(0)
    for x in range(0, len(order_list)):
        rate_calc_total += order_list[x][0] * order_list[x][1]
        amount_total += order_list[x][0]
    order_average_rate = rate_calc_total / amount_total

    logger.debug('rate_calc_total:    ' + "{:.8f}".format(rate_calc_total))
    logger.debug('amount_total:       ' + "{:.8f}".format(amount_total))
    logger.debug('order_average_rate: ' + "{:.8f}".format(order_average_rate))
    
    logger.debug('Calc. Error Margin: ' + "{:.2f}".format((trade_amount - Decimal(response['amountUnfilled'])) - amount_total))
    
    return {'date': trade_date, 'amount': amount_total, 'rate': order_average_rate}


def log_trade_csv(csv_row): # Must pass list as argument
    logger.info('Logging trade details to csv file.')
    try:
        with open(log_file, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(csv_row)

    except:
        logger.error('Failed to write to csv file.')
        csv_failures += 1


def loop_time_dynamic(base, amount, book):
    if loop_dynamic == True:
        logger.debug('Calculating loop time.')

        ask_limit = calc_limit_price(amount, 'buy')
        logger.debug('ask_actual: ' + "{:.8f}".format(ask_limit))
        
        diff = (base - ask_limit) / base
        logger.debug('diff: ' + "{:.4f}".format(diff * Decimal(100)) + ' %')

        if diff <= Decimal(0.0001): # To exclude tiny values
            logger.debug('diff <= 0')
            lt = loop_time

        elif Decimal(0.0001) < diff <= Decimal(1):
            logger.debug('0 < diff < 1')
            lt = loop_time - ((loop_time - loop_time_min) * diff)

        elif diff > Decimal(1):
            logger.debug('1 < diff')
            lt = loop_time_min

    else:
        lt = loop_time
        
    logger.debug('lt: ' + "{:.2f}".format(lt))
    
    return lt


def calc_trade_amount():
    if amount_dynamic == True:
        logger.debug('Calculating trade amount.')
        
        #amt = ????
        logger.debug('CALC_TRADE_AMOUNT REACHED')
        sys.exit()

    else:
        amt = trade_amount

    logger.debug('amt: ' + "{:.2f}".format(amt))

    return amt


if __name__ == '__main__':
    # Connect to MongoDB
    db = MongoClient().lorenzbot

    if clean_collections == True:
        logger.warning('Option to delete all existing collections selected.')
        user_confirm = input('Continue? (y/n): ')

        if user_confirm == 'y':
            logger.info('Confirmed. Deleting all collections')
        elif user_confirm == 'n':
            logger.warning('Collection deletion cancelled by user. Exiting.')
            sys.exit()
        else:
            logger.error('Unrecognized user input. Exiting.')
            sys.exit(1)
        
        logger.info('Dropping all collections from database.')
        modify_collections('drop')
        logger.info('Process complete. Restart program without boolean switch.')
        # COULD JUST PROCEED WITH MAIN PROGRAM...
        sys.exit()
    
    else:
        try:
            # Try to retrieve latest collection
            coll_names = db.collection_names()
            coll_current = coll_names[(len(coll_names) - 1)]
            logger.info('Found existing collection: ' + str(coll_current))
        except:
            # If none found, create new
            logger.info('No collections found in database. Creating new...')
            modify_collections('create')

    # Get config file and set program values from it
    working_dir = os.listdir()

    for file in working_dir:
        if file.endswith('.ini'):
            config_file = str(file)
            logger.info('Found config file: \"' + config_file + '\"')
            break
    else:
        logger.error('No ini configuration file found. Exiting.')
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    # Set Poloniex API keys
    if live_trading == True:
        logger.warning('Live trading ENABLED.')
        # Trade-enabled API key
        api_key = config['live']['key']
        api_secret = config['live']['secret']
    else:
        logger.info('Live trading disabled.')
        # View-only API key
        api_key = config['view']['key']
        api_secret = config['view']['secret']

    # Connect to Poloniex API
    try:
        polo = poloniex.Poloniex(api_key, api_secret)
    except:
        logger.exception('Poloniex API key and/or secret incorrect. Exiting.')
        sys.exit(1)

    # Get and set user maker/taker fees
    user_fees = polo.returnFeeInfo()
    maker_fee = Decimal(user_fees['makerFee'])
    taker_fee = Decimal(user_fees['takerFee'])
    logger.info('Current Maker Fee: ' + "{:.4f}".format(maker_fee))
    logger.info('Current Taker Fee: ' + "{:.4f}".format(taker_fee))

    # Get initial account balances
    account_balances = get_balances()
    balance_str = account_balances['str']
    balance_usdt = account_balances['usdt']
    logger.info('Balance STR:  ' + "{:.2f}".format(balance_str))
    logger.info('Balance USDT: ' + "{:.2f}".format(balance_usdt))

    if balance_usdt < trade_usdt_max:
        logger.warning('Insufficient USDT balance -- need at least ' + "{:.2f}".format(trade_usdt_max) + ' USDT.')
        user_input = input('Continue using full balance of ' + "{:.2f}".format(balance_usdt) + ' instead? (y/n): ')

        if user_confirm == 'y':
            trade_usdt_max = balance_usdt
            logger.info('Max trade amount adjusted.')
        elif user_confirm == 'n':
            logger.warning('Startup cancelled by user due to insufficient balance. Exiting.')
            sys.exit()
        else:
            logger.error('Unrecognized user input. Exiting.')
            sys.exit(1)

    global trade_usdt_remaining
    if db[coll_current].count() > 0:
        logger.debug('Collection not empty. Calculating trade amount remaining.')
        trade_usdt_remaining = trade_usdt_max - calc_trade_totals('bought')
    else:
        logger.debug('Collection empty. Setting trade remaining to trade max.')
        trade_usdt_remaining = trade_usdt_max
    logger.debug('trade_usdt_remaining: ' + "{:.2f}".format(trade_usdt_remaining))

    if trade_usdt_remaining < 0:
        logger.error('Trade amount remaining less than 0. Try cleaning collections or setting a higher max trade value. Exiting.')
        sys.exit(1)

# Functions Used/Arguments Required/Values Returned:
#
# calc_base() --> Decimal(base_price)
# calc_limit_price(book, amt, position, book_depth=20) --> Decimal(price_actual)
# calc_trade_totals(position = 'bought' or 'spent') --> Decimal(trade_total)
# exec_trade(position, price_limit=None, trade_amount=None) --> None
# get_balances() --> {'str': Decimal(bal_str), 'usdt': Decimal(bal_usdt)}
# loop_time_dynamic(base, amt, book) --> Decimal(lt)

    while (True):
        try:
            logger.debug('----[LOOP START]----')
            
            # Calculate base price
            base_price = calc_base()
            logger.debug('base_price: ' + "{:.8f}".format(base_price))
            base_price_trigger = base_price# - buy_threshold    # IS BUY_THRESHOLD NEEDED IF CALCULATING FEES TOO?
            logger.debug('base_price_trigger: ' + "{:.8f}".format(base_price_trigger))

            # Get current account balances
            account_balances = get_balances()
            logger.debug('account_balances: ' + str(account_balances))
            balance_str = account_balances['str']
            balance_usdt = account_balances['usdt']

            # Verify remaining STR balance with expected trade amount
            total_bought_str = calc_trade_totals('bought')
            logger.debug('total_bought_str: ' + "{:.8f}".format(total_bought_str))

            # Verify remaining USDT balance with expected trade amount
            trade_usdt_remaining = trade_usdt_max - total_bought_str
            logger.debug('trade_usdt_remaining: ' + "{:.8f}".format(trade_usdt_remaining))

            if balance_usdt < trade_usdt_remaining:
                logger.warning('USDT balance less than remaining trade allowance. Adjusting allowance to 95% of current balance.')
                trade_usdt_remaining = balance_usdt * Decimal(0.95)
                logger.info('[ADJUSTED]trade_usdt_remaining: ' + "{:.2f}".format(trade_usdt_remaining))

            if balance_str < total_bought_str:
                logger.warning('STR balance less than total amount bought. Will default to selling available STR balance instead.')

            # Check current order book conditions
            # CHANGE TO USE CALC LIMIT FUNCTION
            ob = polo.returnOrderBook('USDT_STR')
            lowest_ask = Decimal(ob['asks'][0][0])
            lowest_ask_volume = Decimal(ob['asks'][0][1])
            highest_bid = Decimal(ob['bids'][0][0])
            highest_bid_volume = Decimal(ob['bids'][0][1])
            logger.debug('lowest_ask_volume:  ' + "{:.2f}".format(lowest_ask_volume))

            # CHANGE TO USE CALC LIMIT FUNCTION
            lowest_ask_actual = lowest_ask * (Decimal(1) + taker_fee)   # Actual rate if bought at this price, including fees
            logger.debug('lowest_ask_actual:  ' + "{:.8f}".format(lowest_ask_actual))
            logger.debug('Difference:         ' + "{:.8f}".format(base_price_trigger - lowest_ask_actual))

            sell_price_target = base_price * (Decimal(1) + profit_threshold + taker_fee)
            logger.debug('sell_price_target:    ' + "{:.8f}".format(sell_price_target))

            # CHANGE TO USE CALC LIMIT FUNCTION
            # Check for sell conditions
            if (highest_bid >= sell_price_target) and (lowest_ask_volume >= calc_trade_totals('bought')):
                logger.debug('TRADE CONDITIONS MET ---> SELLING')
                exec_trade('sell', sell_price_target, calc_trade_totals('bought'))

            # Check for buy conditions
            elif (lowest_ask_actual < base_price_trigger):
                logger.debug('Price good for buy. Checking account balance.')
                if ((balance_usdt * trade_amount) > base_price_trigger):
                    logger.debug('TRADE CONDITIONS MET ---> BUYING')
                    exec_trade('buy', base_price_trigger, calc_trade_amount())
                else:
                    logger.warning('Insufficient balance to execute buy trade. Skipping buy.')
                    buy_skips += 1
                    logger.warning('Buy trades skipped: ' + str(buy_skips))

            #trade_amount_adjust()
            logger.debug('----[LOOP END]----')

            time.sleep(loop_time_dynamic(base_price_trigger, trade_amount, ob))

        except Exception as e:
            logger.exception(e)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')
            logger.info('Mongo write errors: ' + str(mongo_failures))
            if csv_logging == True:
                logger.info('CSV write errors: ' + str(csv_failures))
            
            sys.exit(0)
