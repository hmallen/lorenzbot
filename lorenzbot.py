#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import csv
import datetime
from decimal import *
import logging
import os
import poloniex
import psutil
from pymongo import MongoClient
import shutil
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import textwrap
import time

global coll_current
global base_price, calc_base_initialized
global trade_amount, trade_usdt_max, trade_usdt_remaining
global trade_amount_start, trade_usdt_max_start
global telegram_time_last
global mongo_failures, buy_failures, sell_failures, csv_failures, telegram_failures

poloniex_config_path = 'config/poloniex.ini'
telegram_config_path = 'config/telegram.ini'

log_out = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.log'
log_out_last = './last_debug.log'
log_file = 'logs/lorenzbot_log.csv'
log_file_last = './last_lorenzbot_log.csv'
exception_log_file = './exception_log.log'
exception_last_file = './exception_last.txt'

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)

# Add handler to output log messages to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Add handler to write log messages to file
file_handler = logging.FileHandler(log_out)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

trade_market = 'USDT_STR'
#cashout_market = 'USDT_BTC'

if not os.path.exists('logs'):
    logger.info('Log directory not found. Creating.')
    try:
        os.makedirs('logs')
    except Exception as e:
        logger.exception('Failed to create log directory. Exiting.')
        logger.exception(e)
        sys.exit(1)
if not os.path.exists('logs/old'):
    logger.info('Log archive directory not found. Creating.')
    try:
        os.makedirs('logs/old')
    except Exception as e:
        logger.exception('Failed to create log archive directory. Exiting.')
        logger.exception(e)
        sys.exit(1)

# Variable modifiers
product = trade_market
loop_time_min = Decimal(6)  # Minimum allowed loop time with dynamic adjustment (seconds)

buy_threshold = Decimal(0.000105)
sell_padding = Decimal(0.9975)  # Proportion of total amount bought to sell when triggered

# System variables (Do not change)
calc_base_initialized = False   # Needed to prevent infinite loop b/w calc_base() and exec_trade() on entry buy
buy_skips = 0
buy_failures = 0
sell_skips = 0
sell_failures = 0
mongo_failures = 0
csv_failures = 0
telegram_time_last = time.time()
telegram_failures = 0

# Handle argument parsing
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    
    ---- Lorenz: Poloniex Trading Bot ----
    
    Set custom values for lorenzbot trading program.
        '''),
    epilog='\r')

# Define arguments that can be passed to program
parser.add_argument('-c', '--clean', action='store_true', default=False, help='Add argument to drop all collections and csv trade log to start fresh. [Default = False]')

parser.add_argument('-a', '--amount', default=1.0, type=float, help='Set static base amount of quote product to trade. [Default = 1.0]')
parser.add_argument('--dynamicamount', action='store_true', default=False, help='Add flag to dynamically set trade amount based on current conditions.')
parser.add_argument('-i', '--initial', default=0.01, type=float, help='Set proportion of total funds to use for initial buy. [Default = 0.01]')

parser.add_argument('-m', '--max', default=1.0, type=float, help='Total amount of USDT to use for trading. [Default = 1.0]')
parser.add_argument('-p', '--profit', default=0.05, type=float, help='Set profit threshold for sell triggering. [Default = 0.05]')

parser.add_argument('-l', '--loop', default=60, type=float, help='Main program loop time (seconds). [Default = 60]')
parser.add_argument('--dynamicloop', action='store_true', default=False, help='Add flag to dynamically set loop time based on current conditions.')

parser.add_argument('--live', action='store_true', default=False, help='Add flag to enable live trading API keys.')
#parser.add_argument('--cashout', action='store_true', default=False, help='Add flag to enable \"cash out\" of profits to alternate currency (ex. BTC)')

parser.add_argument('--telegram', action='store_true', default=False, help='Add flag to enable Telegram alerts.')
#parser.add_argument('--telegramexceptions', action='store_true', default=False, help='Add flag to save exceptions to file then send it connected users')

parser.add_argument('--nocsv', action='store_false', default=True, help='Add flag to disable csv logging.')
parser.add_argument('--mongoalt', action='store_true', default=False, help='Add flag to use alternative database for use of multiple instances concurrently.')
parser.add_argument('--debug', action='store_true', default=False, help='Add flag to include debug level output to console.')

# Parse arguments passed to program
logger.debug('Parsing arguments.')
args = parser.parse_args()

# Set variables from arguments passed to program
debug = args.debug
if debug == True:
    console_handler.setLevel(logging.DEBUG)
    logger.debug('Activated debug logging.')

clean_logs = args.clean; logger.debug('clean_logs: ' + str(clean_logs))

trade_amount = Decimal(args.amount); logger.debug('trade_amount: ' + "{:.2f}".format(trade_amount))
amount_dynamic = args.dynamicamount; logger.debug('amount_dynamic: ' + str(amount_dynamic))
trade_proportion_initial = Decimal(args.initial); logger.debug('trade_proportion_initial: ' + "{:.2f}".format(trade_proportion_initial))

trade_usdt_max = Decimal(args.max); logger.debug('trade_usdt_max: ' + "{:.2f}".format(trade_usdt_max))
profit_threshold = Decimal(args.profit); logger.debug('profit_threshold: ' + "{:.2f}".format(profit_threshold))

loop_time = Decimal(args.loop); logger.debug('loop_time: ' + str(loop_time))
loop_dynamic = args.dynamicloop; logger.debug('loop_dynamic: ' + str(loop_dynamic))

live_trading = args.live; logger.debug('live_trading: ' + str(live_trading))
#cashout_active = args.cashout; logger.debug('cashout_active: ' + str(cashout_active))

telegram_active = args.telegram; logger.debug('telegram_active: ' + str(telegram_active))

csv_logging = args.nocsv; logger.debug('csv_logging: ' + str(csv_logging))
mongo_alt = args.mongoalt; logger.debug('mongo_alt: ' + str(mongo_alt))


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
    try:
        bal_str = Decimal(user_balances['STR'])
    except:
        bal_str = Decimal(0)
    try:
        bal_usdt = Decimal(user_balances['USDT'])
    except:
        bal_usdt = Decimal(0)
    
    bal_dict = {'str': bal_str, 'usdt': bal_usdt}

    return bal_dict


def calc_base():
    global calc_base_initialized
    
    logger.debug('Entering base_price calculation.')
    logger.debug('db[coll_current].count(): ' + str(db[coll_current].count()))
    
    if db[coll_current].count() == 0:
        logger.info('No trade log found. Making entry buy.')
        while (True):
            if amount_dynamic == True:
                logger.debug('trade_amount[CALC]: ' + "{:.2f}".format(trade_amount))
                
                trade_price_initial = calc_limit_price(trade_amount, 'buy')
                logger.debug('trade_price_initial[CALC]: ' + "{:.2f}".format(trade_price_initial))
            
            else:
                logger.debug('trade_amount[STATIC]: ' + "{:.2f}".format(trade_amount))
                
                trade_price_initial = calc_limit_price(trade_amount, 'buy')
                logger.debug('trade_price_initial[STATIC]: ' + "{:.2f}".format(trade_price_initial))
            
            logger.info('Entry trade amount: ' + "{:.4f}".format(trade_amount))
            try:
                logger.debug('trade_price_initial: ' + "{:.8f}".format(trade_price_initial))
                exec_trade('buy', trade_price_initial, trade_amount)
                break
            except Exception as e:
                logger.exception('Entry buy failed. Exiting.')
                logger.exception(e)
                
                sys.exit(1) # REMOVE TO PREVENT EXIT ON REBUY AND HANDLE DIFFERENTLY?

    calc_base_initialized = True
    logger.debug('calc_base_initialized: ' + str(calc_base_initialized))

    total_spent = calc_trade_totals('spent')
    total_bought = calc_trade_totals('bought')

    if float(total_bought) > 0:
        rate_avg = calc_trade_totals('spent') / calc_trade_totals('bought')
        logger.debug('rate_avg: ' + "{:.8f}".format(rate_avg))
    else:
        rate_avg = Decimal(0)
        logger.error('Trying to calculate rate with 0 STR bought. Preventing divide by zero error by returning 0.')

    #rate_avg = calc_trade_totals('spent') / calc_trade_totals('bought')
    #logger.debug('rate_avg: ' + "{:.8f}".format(rate_avg))

    return rate_avg


def calc_trade_totals(position):
    if db[coll_current].count() > 0:
        if position == 'bought':
            pipeline = [{
                '$group': {
                    '_id': None,
                    'total_bought': {'$sum': '$amount'}
                    }
                }]
            agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']
            #logger.debug('agg: ' + str(agg))

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
            #logger.debug('agg: ' + str(agg))
            
            trade_total = Decimal(0)
            for x in range(0, len(agg)):
                trade_total += Decimal(agg[x]['total_spent'])

    else:
        trade_total = Decimal(0)
        logger.debug('No documents found in collection. Setting total to 0.')

    logger.debug('trade_total[' + position + ']: ' + "{:.8f}".format(trade_total))
    
    return trade_total


####
# Improve this function by returning weighted average of exec price based on trade amount!!!!
####
def calc_limit_price(amount, position, reverseLookup=None, withFees=None):
    # NEED HANDLING FOR IMPOSSIBLE SITUATIONS
    if position == 'buy':
        book_pos = 'asks'
    elif position == 'sell':
        book_pos = 'bids'

    book_depth = 40  # Double the default value
    while (True):
        book = polo.returnOrderBook(trade_market, depth=book_depth)

        # Lookup amount based on price
        if reverseLookup == True:
            logger.debug('Reverse lookup (amount) in calc_limit_price().')
            book_tot = Decimal(0)
            amt_tot = Decimal(0)
            for x in range(0, len(book[book_pos])):
                book_tot += Decimal(book[book_pos][x][0]) * Decimal(book[book_pos][x][1])
                amt_tot += Decimal(book[book_pos][x][1])
                if float(book_tot) == float(amount):
                    actual = amt_tot
                    
                    break
                
                elif float(book_tot) > float(amount):
                    book_tot -= Decimal(book[book_pos][x][0]) * Decimal(book[book_pos][x][1])
                    amt_tot -= Decimal(book[book_pos][x][1])

                    actual = amt_tot + (amount / Decimal(book[book_pos][x][0]))
                    
                    break
            else:
                actual = 0
        
        # Lookup price based on amount
        else:
            logger.debug('Regular lookup (price) in calc_limit_price().')
            book_tot = Decimal(0)
            for x in range(0, len(book[book_pos])):
                book_tot += Decimal(book[book_pos][x][1])
                if book_tot >= amount:
                    actual = Decimal(book[book_pos][x][0])
                    logger.debug('actual: ' + "{:.8f}".format(actual))
                    logger.debug('book_tot: ' + "{:.2f}".format(book_tot))
                    break
            else:
                actual = 0

        logger.debug('actual: ' + "{:.8f}".format(actual))
        logger.debug('book_tot: ' + "{:.2f}".format(book_tot))
        
        if float(actual) <= 0:
            # NEED TO FIGURE OUT HOW TO HANDLE THIS!!!!
            if book_depth >= 200:
                #logger.exception('Failed to set price_actual in calc_limit_price().')
                #break
                logger.error('Failed to set price_actual in calc_limit_price(). Exiting.')
                sys.exit(1)

            else:
                logger.warning('Volume not satisfied at default order book depth=' + str(book_depth) + '. Retrying with depth = ' + str(book_depth + 40) + '.')
                book_depth += 40
                
                time.sleep(1)

        else:
            logger.debug('calc_limit_price() successful within limits (depth=' + str(book_depth) + ').')

            if withFees:
                logger.debug('Adding fees to calc_limit_price() return value.')
                if position == 'buy':
                    actual = actual * (Decimal(1) + taker_fee)
                elif position == 'sell':
                    actual = actual * (Decimal(1) - taker_fee)
                logger.debug('[' + position + ']price_actual[+FEES]: ' + "{:.8f}".format(actual))
            
            break

    return actual


# NEED TO FIX THE BUY/SELL FUNCTIONS
def exec_trade(position, limit, amount):
    global calc_base_initialized
    global telegram_time_last
    global mongo_failures, buy_failures, sell_failures
    
    if calc_base_initialized == True:
        base_price_initial = calc_base()
    else:
        base_price_initial = 0
        
    if position == 'buy':
        try:
            trade_response = polo.buy(trade_market, limit, amount, 'immediateOrCancel')
            logger.debug('[BUY] trade_response: ' + str(trade_response))
        except Exception as e:
            logger.exception('Exception occurred while executing buy trade.')
            logger.exception(e)
            buy_failures += 1
            raise

        if len(trade_response['resultingTrades']) > 0:
            order_details = process_trade_response(trade_response, position)
            logger.debug('[BUY] order_details: ' + str(order_details))

            try:
                mongo_response = db[coll_current].insert_one({'amount': float(order_details['amount']), 'price': float(order_details['rate']), 'side': position, 'date': order_details['date']})
                logger.debug('[BUY] mongo_response: ' + str(mongo_response))
                logger.info('Buy logged to MongoDB database collection ' + coll_current)
            except Exception as e:
                logger.exception('[BUY] Failed to write to MongoDB log!')
                logger.exception(e)
                mongo_failures += 1
                raise

        else:
            logger.warning('No trades were executed on buy attempt.')
        
    elif position == 'sell':
        try:
            trade_response = polo.sell(trade_market, limit, amount, 'immediateOrCancel')  # CHANGE TO REGULAR LIMIT ORDER?
            logger.debug('[SELL] trade_response: ' + str(trade_response))
        except Exception as e:
            logger.exception('Exception occurred while executing sell trade.')
            logger.exception(e)
            sell_failures += 1
            raise

        if len(trade_response['resultingTrades']) > 0:
            amount_unfilled = Decimal(trade_response['amountUnfilled'])
            logger.debug('amount_unfilled: ' + "{:.4f}".format(amount_unfilled))
            
            order_details = process_trade_response(trade_response, position)
            logger.debug('[SELL] order_details: ' + str(order_details))

            try:
                mongo_response = db[coll_current].insert_one({'amount': float(order_details['amount']), 'price': float(order_details['rate']), 'side': position, 'date': order_details['date']})
                logger.debug('[SELL] mongo_response: ' + str(mongo_response))
                logger.info('Sell logged to MongoDB database collection ' + coll_current)
            except Exception as e:
                logger.exception('[SELL] Failed to write to MongoDB log!')
                logger.exception(e)
                mongo_failures += 1
                raise

            coll_current_prev = coll_current
            modify_collections('create')    # Create new collection
            if coll_current == coll_current_prev:
                logger.error('Failed to create new MongoDB database!')
                sys.exit(1)
            
            # If order not completely filled, handle unfilled amount
            if amount_unfilled > Decimal(0):
                # Add amount_unfilled and previous base price to new MongoDB database
                try:
                    mongo_response = db[coll_current].insert_one({'amount': float(amount_unfilled), 'price': float(base_price_initial), 'side': 'buy', 'date': order_details['date']})
                    logger.debug('[UNFILLED/NEW] mongo_response: ' + str(mongo_response))
                    logger.info('Added unfilled trade amount to new MongoDB collection ' + coll_current)
                except Exception as e:
                    logger.exception('[UNFILLED/NEW] Failed to write to MongoDB log!')
                    logger.exception(e)
                    mongo_failures += 1
                    raise
            
            else:
                logger.debug('Sell completely filled. New collection starting empty.')

                calc_base_initialized = False
                logger.debug('calc_base_initialized: ' + str(calc_base_initialized))

            # Reset trade amount/allotment to maximum for start of new buy phase
            reset_trade_maxima()

        else:
            logger.warning('No trades were executed on sell attempt.')

    if len(trade_response['resultingTrades']) > 0:
        if csv_logging == True:
            csv_list = [order_details['date'],
                        position,
                        "{:.8f}".format(order_details['amount']),
                        "{:.8f}".format(order_details['rate']),
                        "{:.8f}".format(base_price_initial),
                        "{:.8f}".format(calc_base())]
            logger.debug('csv_list: ' + str(csv_list))
            log_trade_csv(csv_list)

        if telegram_active == True:
            if len(connected_users) > 0:
                if position == 'buy':
                    pos_msg = 'Bought '
                elif position == 'sell':
                    pos_msg = 'Sold '

                trade_details_msg = pos_msg + "{:.4f}".format(order_details['amount']) + ' @ ' + "{:.4f}".format(order_details['rate']) + '\n'
                
                base_current = calc_base()
                logger.debug('base_current: ' + "{:.8f}".format(base_current))
                base_msg = 'Base Price:   ' + "{:.6f}".format(base_current) + '\n'

                spent_msg = 'USDT Spent: ' + "{:.4f}".format(calc_trade_totals('spent')) + '\n'
                bought_msg = 'STR Bought: ' + "{:.4f}".format(calc_trade_totals('bought'))# + '\n'
            
                
                telegram_message = trade_details_msg + base_msg + spent_msg + bought_msg
                logger.debug('telegram_message: ' + telegram_message)
                
                logger.info('Sending Telegram alert.')

                telegram_delay = time.time() - telegram_time_last
                logger.debug('telegram_delay: ' + str(telegram_delay))
                if position == 'buy' and telegram_delay < 300:  # If buying and last buy less than 5 min ago, don't send message
                    logger.info('Telegram buy message delay hasn\'t elapsed. Skipping trade update.')
                    return
                elif position == 'buy':
                    telegram_time_last = time.time()
                    logger.debug('Telegram buy message delay reset.')
                
                telegram_send_message(updater.bot, telegram_message)

            else:
                logger.info('No users connected to Telegram. Skipping alert.')


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

    logger.debug('rate_calc_total: ' + "{:.8f}".format(rate_calc_total))
    logger.debug('amount_total: ' + "{:.8f}".format(amount_total))
    logger.debug('order_average_rate: ' + "{:.8f}".format(order_average_rate))
    #logger.debug('trade_amount: ' + "{:.8f}".format(trade_amount)) # TRADES AREN'T EXEC AT THIS PRICE UNLESS NO DYNAMIC AMOUNT
    #logger.debug('Fees (STR): ' + "{:.8f}".format(trade_amount - amount_total))
    
    #logger.debug('Calc. Error Margin: ' + "{:.2f}".format((trade_amount - Decimal(response['amountUnfilled'])) - amount_total))
    
    return {'date': trade_date, 'amount': amount_total, 'rate': order_average_rate}


def log_trade_csv(csv_row): # Must pass list as argument
    global csv_failures
    
    logger.info('Logging trade details to csv file.')
    try:
        with open(log_file, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(csv_row)
    #except csv.Error as e:
    except Exception as e:
        logger.exception('Exception occurred while writing to csv file.')
        logger.exception(e)
        csv_failures += 1
        raise


def calc_profit_csv():
    global csv_failures
    
    trade_list = []

    logger.debug('Reading csv file.')
    with open(log_file, newline='') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
        try:
            for row in csv_reader:
                #logger.debug(row)
                trade_list.append(row)
        #except csv.Error as e:
        except Exception as e:
            logger.exception('Exception occurred while writing to csv file.')
            logger.exception(e)
            csv_failures += 1
            raise

    #logger.debug('len(trade_list): ' + str(len(trade_list)))
    logger.debug('Calculating profit from csv data.')

    bought_amount = Decimal(0)
    spent_amount = Decimal(0)
    buy_count = 0
    sold_amount = Decimal(0)
    gain_amount = Decimal(0)
    sell_count = 0
    for x in range(0, len(trade_list)):
        trade_position = trade_list[x][1]
        amount = Decimal(trade_list[x][2])
        rate = Decimal(trade_list[x][3])

        if trade_position == 'buy':
            bought_amount += amount
            spent_amount += amount * rate
            buy_count += 1
        elif trade_position == 'sell':
            sold_amount += amount
            gain_amount += amount * rate
            sell_count += 1
    
    rate_avg = spent_amount / bought_amount

    logger.debug('bought_amount: ' + "{:.8f}".format(bought_amount))
    logger.debug('spent_amount: ' + "{:.8f}".format(spent_amount))
    logger.debug('buy_count: ' + str(buy_count))
    logger.debug('sold_amount: ' + "{:.8f}".format(sold_amount))
    logger.debug('gain_amount: ' + "{:.8f}".format(gain_amount))
    logger.debug('sell_count: ' + str(sell_count))
    logger.debug('rate_avg: ' + "{:.8f}".format(rate_avg))

    if gain_amount > 0:
        profit = gain_amount - spent_amount
        
    else:
        profit = Decimal(-1)

    logger.debug('profit: ' + "{:.8f}".format(profit))

    return {'profit': profit}


def telegram_connect(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id

    if connected_users.count(telegram_user) == 0:
        connected_users.append(telegram_user)
        
        logger.debug('[CONNECT] chat_id: ' + str(telegram_user))
        logger.info('Telegram user connected: ' + str(telegram_user))
        #logger.debug('Connected Users: ' + str(connected_users))

        telegram_message = 'Subscribed to Lorenzbot alerts.'

    else:
        telegram_message = 'Already subscribed to Lorenzbot alerts.'
        
    logger.debug('[CONNECT] telegram_message:\n' + telegram_message)
    
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)  # Do I really need more random comments? Yep.
    except Exception as e:
        logger.exception('[CONNECT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1
        raise


def telegram_disconnect(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id

    if connected_users.count(telegram_user) > 0:
        connected_users.remove(telegram_user)
        
        logger.debug('[DISCONNECT] chat_id: ' + str(telegram_user))
        logger.info('Telegram user disconnected: ' + str(telegram_user))
        #logger.debug('Connected Users: ' + str(connected_users))
        
        telegram_message = 'Unsubscribed from Lorenzbot alerts.'

    else:
        telegram_message = 'Not currently subscribed to Lorenzbot alerts.'

    logger.debug('[DISCONNECT] telegram_message:\n' + telegram_message)
    
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.exception('[DISCONNECT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1
        raise


def telegram_status(bot, update):
    global trade_usdt_remaining
    global telegram_failures
    
    telegram_user = update.message.chat_id
    
    logger.debug('[STATUS] chat_id: ' + str(telegram_user))
    logger.info('Telegram user requesting status: ' + str(telegram_user))

    if connected_users.count(telegram_user) > 0:
        logger.debug('Access confirmed for requesting user.')
                
        spent_msg = 'Tot. Spent:  ' + "{:.4f}".format(calc_trade_totals('spent')) + ' (USDT)\n'
        bought_msg = 'Tot. Bought:  ' + "{:.4f}".format(calc_trade_totals('bought')) + ' (STR)\n'
        
        base_current = calc_base()
        logger.debug('base_current: ' + "{:.8f}".format(base_current))
        base_msg = 'Base Price:    ' + "{:.6f}".format(base_current) + ' (USDT)\n'

        logger.debug('sell_price_target: ' + "{:.8f}".format(sell_price_target))
        sell_target_msg = 'Sell Target: ' + "{:.6f}".format(sell_price_target) + ' (USDT)\n'
        
        market_current = Decimal(polo.returnTicker()[trade_market]['last'])
        logger.debug('market_current: ' + "{:.8f}".format(market_current))
        market_msg = 'Mkt. Price:    ' + "{:.6f}".format(market_current) + '\n'

        price_diff = (market_current - sell_price_target) / sell_price_target
        logger.debug('price_diff: ' + "{:.8f}".format(price_diff))
        price_diff_msg = 'Difference: ' + "{:.2f}".format(price_diff * Decimal(100) + '%'

        telegram_message = spent_msg + bought_msg + base_msg + sell_target_msg + market_msg + price_diff_msg

    else:
        logger.warning('Access denied for requesting user.')
        telegram_message = 'Not currently in list of connected users. Type \"/connect\" to subscribe to alerts.'

    logger.debug('[STATUS] telegram_message:\n' + telegram_message)
    
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.exception('[STATUS] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1
        raise


def telegram_profit(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id
    
    logger.debug('[PROFIT] chat_id: ' + str(telegram_user))
    logger.info('Telegram user requesting profit calculation: ' + str(telegram_user))

    if connected_users.count(telegram_user) > 0:
        logger.debug('Access confirmed for requesting user.')

        if csv_logging == True:
            trade_profit_return = calc_profit_csv()
            logger.debug('trade_profit_return: ' + str(trade_profit_return))

            trade_profit = trade_profit_return['profit']
            logger.debug('[CSVPROFIT] trade_profit: ' + "{:.8f}".format(trade_profit))
    
            if float(trade_profit) < 0:
                telegram_message = 'No sell trades executed.'
                logger.debug('No sell trades executed.')

            else:
                telegram_message = 'Total Profit: ' + "{:.4f}".format(profit)   # CSV PROFIT CALCULATION

        else:
            telegram_message = 'CSV logging not active. Cannot calculate profit.'
    
    else:
        logger.warning('Access denied for requesting user.')        
        telegram_message = 'Not currently in list of connected users. Type \"/connect\" to connect to Lorenzbot.'

    logger.debug('[PROFIT] telegram_message:\n' + telegram_message)
    
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.exception('[PROFIT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1
        raise


def telegram_send_message(bot, trade_message):
    global telegram_failures
    
    logger.debug('[SEND] trade_message:\n' + trade_message)

    if len(connected_users) > 0:
        for user in connected_users:
            try:
                bot.send_message(chat_id=user, text=trade_message)
                logger.debug('Sent alert to user ' + str(user) + '.')
            except Exception as e:
                logger.exception('[SEND] Exception occurred while sending telegram message.')
                logger.exception(e)
                telegram_failures += 1
                raise
    
    else:
        logger.debug('No Telegram users connected. Message not sent.')


def telegram_send_exception(bot):
    global telegram_failures
    
    exception_msg = datetime.datetime.now().strftime('%m-%d-%Y, %H:%M:%S') + ' - Exception'

    if len(connected_users) > 0:
        for user in connected_users:
            try:
                bot.send_message(chat_id=user, text=exception_msg)
                bot.send_document(chat_id=user, document=open(exception_last_file, 'rb'))
            except Exception as e:
                logger.exception('[SEND] Exception occurred while sending telegram message.')
                logger.exception(e)
                telegram_failures += 1
                # IF RAISED AND TELEGRAM ISSUE NOT RESOLVED, WILL LOOP FOREVER
                #raise
    
    else:
        logger.debug('No Telegram users connected. Message not sent.')


def calc_dynamic(selection, base, limit):
    global trade_usdt_remaining
    
    diff = (base - limit) / base
    logger.debug('diff: ' + "{:.8f}".format(diff) + ' [' + selection + ']')
    #logger.info('Price Difference from Base: ' + "{:.4f}".format(diff * Decimal(100) * Decimal(-1)) + '%')

    # Map magnitude of difference b/w base price and buy price to loop time
    if selection == 'loop':
        if loop_dynamic == True:
            logger.debug('Calculating loop time.')
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
            logger.debug('Using static loop time.')
            lt = loop_time

        logger.debug('lt: ' + "{:.2f}".format(lt))

        return lt

    # Map magnitude of difference b/w base price and buy price to buy amount
    elif selection == 'amount':
        if amount_dynamic == True:
            logger.debug('Calculating trade amount.')

            if diff > Decimal(0):
                logger.debug('diff > 0')
                
                #trade_proportion_low = trade_proportion_initial # Default = 0.01
                trade_proportion_low = Decimal(0.005)
                logger.debug('trade_proportion_low: ' + "{:.2f}".format(trade_proportion_low))
                trade_proportion_high = Decimal(0.25)    # If limit price 100% less than base price, trade with this proportion of available USDT remaining
                logger.debug('trade_proportion_high: ' + "{:.2f}".format(trade_proportion_high))
                trade_proportion_adj = trade_proportion_low + (diff * (trade_proportion_high - trade_proportion_low))
                logger.debug('trade_proportion_adj: ' + "{:.2f}".format(trade_proportion_adj))

                logger.debug('trade_usdt_remaining: ' + "{:.2f}".format(trade_usdt_remaining))                
                amount_usdt = trade_usdt_remaining * trade_proportion_adj  # USDT
                logger.debug('[DYNAMIC]amount_usdt: ' + "{:.8f}".format(amount_usdt))

                amount = calc_limit_price(amount_usdt, 'buy', reverseLookup=True)

                logger.debug('[DYNAMIC]amount: ' + "{:.8f}".format(amount))

            else:
                logger.debug('diff < 0')
                amount = trade_amount

            logger.debug('[DYNAMIC] amount: ' + "{:.8f}".format(amount))

        else:
            logger.debug('Using static loop time.')
            
            amount = trade_amount  # STELLAR LUMENS
            logger.debug('[STATIC]amount: ' + "{:.8f}".format(amount))

        return amount


def verify_amounts():
    global base_price
    global trade_amount, trade_usdt_max, trade_usdt_remaining
    
    verification = True
    
    # Get account balances
    account_balances = get_balances()
    balance_str = account_balances['str']
    balance_usdt = account_balances['usdt']
    logger.info('Balance STR:  ' + "{:.4f}".format(balance_str))
    logger.info('Balance USDT: ' + "{:.4f}".format(balance_usdt))

    # Present trade totals
    logger.info('Total STR Bought: ' + "{:.4f}".format(calc_trade_totals('bought')))
    logger.info('Total USDT Spent: ' + "{:.4f}".format(calc_trade_totals('spent')))

    # If USDT and STR balances both ~0, then exit
    if balance_usdt < Decimal(0.0001) and float(balance_str) == 0:
        logger.error('USDT and STR balances both 0. Exiting.')
        sys.exit(1)

    coll_count = db[coll_current].count()
    logger.info('Total Buy Count: ' + str(coll_count))
    trade_amount_avg = calc_trade_totals('bought') / Decimal(coll_count)
    logger.info('Avg. Trade Amount: ' + "{:.4f}".format(trade_amount_avg))

    # Verify STR balance with recorded amount bought
    if float(balance_str) < float(calc_trade_totals('bought')):
        logger.warning('STR balance less than recorded bought amount.')
        
        logger.warning('Creating new MongoDB database with available STR balance as total bought.')
        
        # Create new database and add available STR balance as buy trade
        coll_current_prev = coll_current
        modify_collections('create')    # Create new collection
        if coll_current == coll_current_prev:
            logger.error('Failed to create new MongoDB database!')
            sys.exit(1)

        if float(balance_str) > 0:
            try:
                mongo_response = db[coll_current].insert_one({'amount': float(balance_str), 'price': float(base_price), 'side': 'buy', 'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                logger.debug('[BALANCE ADJUSTMENT] mongo_response: ' + str(mongo_response))
                logger.info('Adjustment logged to new MongoDB database collection ' + coll_current)
            except Exception as e:
                logger.exception('[BALANCE ADJUSTMENT] Failed to write to MongoDB log!')
                logger.exception(e)
                mongo_failures += 1
                raise

        else:
            logger.warning('STR balance is 0. Leaving new collection empty.')

        verification = False

    # Verify remaining USDT balance with expected available trade amount
    trade_usdt_remaining = trade_usdt_max - calc_trade_totals('spent')
    logger.debug('trade_usdt_remaining: ' + "{:.8f}".format(trade_usdt_remaining))
    if float(balance_usdt) < float(trade_usdt_remaining):
        logger.warning('USDT balance less than remaining USDT amount allotted for trading. Adjusting allotment to available balance.')
        trade_usdt_max = (balance_usdt + calc_trade_totals('spent')) * Decimal(0.98)
        trade_usdt_remaining = trade_usdt_max - calc_trade_totals('spent')
        logger.debug('[ADJUSTED]trade_usdt_remaining: ' + "{:.8f}".format(trade_usdt_remaining))
        logger.info('Remaining Tradable USDT Balance Adjusted: ' + "{:.4f}".format(trade_usdt_remaining))

        verification = False

    logger.debug('trade_usdt_remaining: ' + "{:.8f}".format(trade_usdt_remaining))
    logger.info('Tradable USDT Remaining: ' + "{:.4f}".format(trade_usdt_remaining))

    # Verify that base trade amount can be covered by current USDT balance and adjust if necessary
    buy_amount_max = calc_limit_price(trade_usdt_remaining, 'buy', reverseLookup=True, withFees=True)
    logger.debug('buy_amount_max: ' + "{:.8f}".format(buy_amount_max))
    #if float(trade_amount) > float(buy_amount_max * Decimal(0.5)):
    if float(trade_amount) > float(buy_amount_max):
        trade_amount = buy_amount_max * Decimal(0.05)   # NEED TO DETERMINE PROPER PROPORTION TO USE WHEN ADJUSTED
        logger.debug('[ADJUSTED]trade_amount: ' + "{:.8f}".format(trade_amount))
        logger.info('USDT balance low. Adjusting base trade amount to ' + "{:.4f}".format(trade_amount))

        verification = False

    return verification


def reset_trade_maxima():
    global trade_amount, trade_usdt_max, trade_usdt_remaining
    global trade_amount_start, trade_usdt_max_start

    logger.info('Resetting STR trade amount and USDT allotment to initial values.')

    trade_usdt_max = trade_usdt_max_start
    logger.debug('trade_usdt_max: ' + "{:.8f}".format(trade_usdt_max))
    trade_usdt_remaining = trade_usdt_max - calc_trade_totals('spent')
    logger.debug('trade_usdt_remaining: ' + "{:.8f}".format(trade_usdt_remaining))

    if amount_dynamic == True:
        trade_amount = (trade_usdt_max * trade_proportion_initial) / Decimal(polo.returnTicker()[trade_market]['lowestAsk'])
    else:
        trade_amount = trade_amount_start
    logger.debug('trade_amount: ' + "{:.8f}".format(trade_amount))


if __name__ == '__main__':
    # Check if MongoDB is running before beginning
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
    
    # Connect to MongoDB
    if mongo_alt == False:
        db = MongoClient().lorenzbot
        logger.info('Using default MongoDB database \"lorenzbot\".')
    else:
        db = MongoClient().lorenzbotalt
        logger.info('Using alternate MongoDB database \"lorenzbotalt\".')

    if clean_logs == True:
        logger.warning('Selected option to delete existing collections and archive current csv trade log.')
        user_confirm = input('Continue? (y/n): ')

        if user_confirm == 'y':
            logger.info('Confirmed. Deleting all collections and csv trade log.')
        elif user_confirm == 'n':
            logger.warning('Collection deletion cancelled by user. Exiting.')
            sys.exit()
        else:
            logger.error('Unrecognized user input. Exiting.')
            sys.exit(1)
        
        logger.info('Dropping all collections from database.')
        modify_collections('drop')
        logger.info('Process complete. Restart program without boolean switch.')

        if csv_logging == True:
            if os.path.isfile(log_file):
                logger.info('Archiving old csv trade log.')
                os.rename(log_file, ('logs/old/' + 'lorenzbot_log_' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.csv'))
            else:
                logger.info('No csv log found to archive.')
        
        sys.exit()  # COULD JUST PROCEED WITH MAIN PROGRAM...
    
    else:
        # Handle all of the arguments delivered appropriately
        if trade_usdt_max >= Decimal(10):
            logger.warning('Total USDT trade amount is set to $' + "{:.2f}".format(trade_usdt_max) + '.')
            user_confirm = input('Is this correct? (y/n): ')

            if user_confirm == 'y':
                logger.info('USDT trade amount confirmed.')
            elif user_confirm == 'n':
                logger.warning('Startup cancelled by user due to USDT trade amount. Exiting.')
                sys.exit()
            else:
                logger.error('Unrecognized user input. Exiting.')
                sys.exit(1)

        if amount_dynamic == True:
            logger.info('Dynamic trade amount calculation activated.')
            if float(trade_amount) != 1.0:
                logger.warning('Ignoring trade amount argument passed. Will set initial trade amount on program start.')
        
        elif amount_dynamic == False and trade_amount >= Decimal(10):
            logger.warning('Total STR trade amount is set to ' + "{:.2f}".format(trade_amount) + '.')
            user_confirm = input('Is this correct? (y/n): ')

            if user_confirm == 'y':
                logger.info('STR trade amount confirmed.')
            elif user_confirm == 'n':
                logger.warning('Startup cancelled by user due to STR trade amount. Exiting.')
                sys.exit()
            else:
                logger.error('Unrecognized user input. Exiting.')
                sys.exit(1)

        if loop_dynamic == True:
            logger.info('Dynamic loop time calculation activated. Base loop time set to ' + str(loop_time) + ' seconds.')
        else:
            logger.info('Using fixed loop time of ' + str(loop_time) + ' seconds.')

        if csv_logging == True:
            #log_file = 'logs/' + 'lorenzbot_log_' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.csv'
            logger.info('CSV logging activated.')
            logger.debug('CSV log file path: ' + log_file)

        if telegram_active == True:
            logger.info('Telegram logging active. Send \"/connect\" to @lorenzbot_bot to receive alerts.')

        try:
            # Try to retrieve latest collection
            coll_names = db.collection_names()
            logger.debug('coll_names: ' + str(coll_names))

            coll_names.sort()   # Sort collection names so newest is on the end
            
            coll_current = coll_names[(len(coll_names) - 1)]    # Retrieve the last collection from the list
            logger.info('Found existing collection: ' + coll_current)
        except:
            # If none found, create new
            logger.info('No collections found in database. Creating new.')
            modify_collections('create')    # Create new collection

    # Get config file(s) and set program values from it/them
    config = configparser.ConfigParser()

    if telegram_active == True:
        if not os.path.isfile(telegram_config_path):
            logger.error('No Telegram config file found! Must create \".telegram.ini\". Exiting.')
            sys.exit(1)
        else:
            logger.info('Found Telegram config file.')
        
        # Set Telegram token
        config.read(telegram_config_path)
        telegram_token = config['lorenzbot']['token']
        logger.debug('telegram_token: ' + str(telegram_token))

        updater = Updater(token=telegram_token)
        dispatcher = updater.dispatcher

        connect_handler = CommandHandler('connect', telegram_connect)
        dispatcher.add_handler(connect_handler)

        disconnect_handler = CommandHandler('disconnect', telegram_disconnect)
        dispatcher.add_handler(disconnect_handler)

        status_handler = CommandHandler('status', telegram_status)
        dispatcher.add_handler(status_handler)

        profit_handler = CommandHandler('profit', telegram_profit)
        dispatcher.add_handler(profit_handler)

        updater.start_polling()

        connected_users = []

    if not os.path.isfile(poloniex_config_path):
        logger.error('No Poloniex config file found! Must create \".poloniex.ini\". Exiting.')
        sys.exit(1)
    else:
        logger.info('Found Poloniex config file.')

    # Set Poloniex API keys
    config.read(poloniex_config_path)
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
    except Exception as e:
        logger.exception('Poloniex API key and/or secret incorrect. Exiting.')
        logger.exception(e)
        #if connected_users.count(telegram_user) > 0:
            #connected_users.remove(telegram_user)
        
        sys.exit(1)

    # If dynamic amount calculation active, set the base trade amount using current conditions
    if amount_dynamic == True:
        trade_amount = (trade_usdt_max * trade_proportion_initial) / Decimal(polo.returnTicker()[trade_market]['lowestAsk'])
    else:
        trade_amount_start = trade_amount

    # Store initial value to allow reset after sell if adjustment occurred
    trade_usdt_max_start = trade_usdt_max

    # Get and set user maker/taker fees
    user_fees = polo.returnFeeInfo()
    maker_fee = Decimal(user_fees['makerFee'])
    taker_fee = Decimal(user_fees['takerFee'])
    logger.info('Current Maker Fee: ' + "{:.4f}".format(maker_fee * Decimal(100)) + '%')
    logger.info('Current Taker Fee: ' + "{:.4f}".format(taker_fee * Decimal(100)) + '%')

    # Calculate base price
    base_price = calc_base()
    logger.debug('base_price: ' + "{:.8f}".format(base_price))
    logger.info('Base Price: ' + "{:.6f}".format(base_price))
    #base_price_target = base_price - buy_threshold    # IS BUY_THRESHOLD NEEDED IF CALCULATING FEES TOO?
    
    verify_initial = verify_amounts()
    logger.debug('verify_initial: ' + str(verify_initial))

    if verify_initial == True:
        logger.info('Initial balance/trade log amounts VERIFIED.')
    else:
        logger.info('Initial balance/trade log amounts ADJUSTED.')
    

# Functions Used/Arguments Required/Values Returned:
#
# calc_base() --> Decimal(base_price)
# calc_limit_price(book, amt, position, book_depth=20) --> Decimal(price_actual)
# calc_trade_totals(position = 'bought' or 'spent') --> Decimal(trade_total)
# exec_trade(position, price_limit=None, trade_amount=None) --> None
# get_balances() --> {'str': Decimal(bal_str), 'usdt': Decimal(bal_usdt)}
# loop_time_dynamic(base, amt, book) --> Decimal(lt)

    loop_count = 0
    while (True):
        try:
            logger.info('----[LOOP START]----')

            # Calculate base price
            base_price = calc_base()
            logger.debug('base_price: ' + "{:.8f}".format(base_price))
            logger.info('Base Price: ' + "{:.6f}".format(base_price))

            base_price_target = base_price * (Decimal(1) - taker_fee)
            #base_price_target = base_price - buy_threshold    # IS BUY_THRESHOLD NEEDED IF CALCULATING FEES TOO?
            logger.debug('base_price_target: ' + "{:.8f}".format(base_price_target))
            logger.info('Base Price Target: ' + "{:.6f}".format(base_price_target))

            trade_check_ready = verify_amounts()
            logger.debug('trade_check_ready: ' + str(trade_check_ready))

            # If balances and trade logs agree, proceed with check for trade conditions
            if trade_check_ready == True:
                # Calculate buy amount based on current conditions
                buy_amount_current = calc_dynamic('amount', base_price_target, calc_limit_price(trade_amount, 'buy', withFees=True))
                logger.debug('buy_amount_current: ' + "{:.8f}".format(buy_amount_current))
                logger.info('Current Buy Amount: ' + "{:.4f}".format(buy_amount_current))

                # Calculate true low ask (sufficient volume for buy)
                low_ask_actual = calc_limit_price(buy_amount_current, 'buy', withFees=True)
                logger.debug('low_ask_actual: ' + "{:.8f}".format(low_ask_actual))
                logger.info('Low Ask (Actual): ' + "{:.6f}".format(low_ask_actual))

                # Set sell amount based on total amount bought
                sell_amount_current = calc_trade_totals('bought')
                logger.debug('sell_amount_current: ' + "{:.8f}".format(sell_amount_current))
                logger.info('Current Sell Amount: ' + "{:.4f}".format(sell_amount_current))

                # Calculate true high bid (sufficient volume for sell)
                high_bid_actual = calc_limit_price(sell_amount_current, 'sell', withFees=True)
                logger.debug('high_bid_actual: ' + "{:.8f}".format(high_bid_actual))
                logger.info('High Bid (Actual): ' + "{:.6f}".format(high_bid_actual))

                # Calculate target sell price
                sell_price_target = base_price * (Decimal(1) + profit_threshold + taker_fee)  # Add fee in calc_limit_price()
                logger.debug('sell_price_target: ' + "{:.8f}".format(sell_price_target))
                logger.info('Sell Target: ' + "{:.6f}".format(sell_price_target))

                # Display % differences from base and sell targets
                bt_diff = (low_ask_actual - base_price_target) / base_price_target
                logger.debug('bt_diff: ' + "{:.8f}".format(bt_diff))
                logger.info('Base/Ask Target Difference: ' + "{:.2f}".format(bt_diff * Decimal(100)) + '%')
                
                st_diff = (high_bid_actual - sell_price_target) / sell_price_target
                logger.debug('st_diff: ' + "{:.8f}".format(st_diff))
                logger.info('Sell/Bid Target Difference: ' + "{:.2f}".format(st_diff * Decimal(100)) + '%')

                # Check for sell conditions
                if float(high_bid_actual) >= float(sell_price_target):
                    # Check if sell total greater than minimum allowed
                    if (sell_amount_current * sell_price_target) <= Decimal(0.0001):
                        logger.warning('Trade total must be >= $0.0001. Skipping Trade.')
                        sell_skips += 1
                    else:
                        logger.info('TRADE CONDITIONS MET --> SELLING')
                        exec_trade('sell', sell_price_target, sell_amount_current)

                # Check for buy conditions
                elif float(low_ask_actual) <= float(base_price):
                    # Check if buy total greater than minimum allowed
                    if (buy_amount_current * low_ask_actual) <= Decimal(0.0001):
                        logger.warning('Trade total must be >= $0.0001. Skipping Trade.')
                        buy_skips += 1
                    else:
                        logger.info('TRADE CONDITIONS MET --> BUYING')
                        exec_trade('buy', base_price_target, buy_amount_current)

                # Calculate loop time based on current conditions
                loop_time_dynamic = calc_dynamic('loop', base_price, low_ask_actual)

            else:
                logger.warning('Skipping trade check until balances and trade logs agree.')
                loop_time_dynamic = loop_time

            logger.info('Trade loop complete. Sleeping for ' + "{:.2f}".format(loop_time_dynamic) + ' seconds.')

            logger.info('----[LOOP END]----')
            loop_count += 1
            logger.debug('loop_count: ' + str(loop_count))
            
            time.sleep(loop_time_dynamic)

        except Exception as e:
            logger.exception('Exception raised and caught in main loop.')
            logger.exception(e)
            
            with open(exception_log_file, 'w') as ex_file:
                ex_file.write(str(e))
                logger.debug('Wrote exception to exception log file.')

            with open(exception_last_file, 'a') as ex_file:
                ex_file.write(str(e))
                logger.debug('Wrote exception to recent exception file.')

            if telegram_active == True:
                telegram_send_exception(updater.bot)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')

            logger.info('Loop Count: ' + str(loop_count))

            shutil.copy(log_out, log_out_last)
            shutil.copy(log_file, log_file_last)
            logger.info('Copied most recent log file and trade log to root directory.')
            
            logger.info('Mongo write errors: ' + str(mongo_failures))
            logger.info('Buy trades skipped: ' + str(buy_skips))
            logger.info('Buy trades failed: ' + str(buy_failures))
            logger.info('Sell trades skipped: ' + str(sell_skips))
            logger.info('Sell trades failed: ' + str(sell_failures))
            
            if csv_logging == True:
                logger.info('CSV write errors: ' + str(csv_failures))

            if telegram_active == True:
                logger.info('Telegram sends failed: ' + str(telegram_failures))
                updater.stop()
            
            sys.exit()
