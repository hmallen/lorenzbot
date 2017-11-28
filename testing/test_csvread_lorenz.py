import csv
from decimal import *
import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

log_file = '../logs/lorenzbot_log_newest.csv'

trade_list = []

with open(log_file, newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
    try:
        for row in csv_reader:
            #logger.debug(row)
            trade_list.append(row)
    except csv.Error as e:
        logger.exception('Exception occurred while reading csv file.')

#logger.debug(trade_list)

bought_amount = Decimal(0)
spent_amount = Decimal(0)
sold_amount = Decimal(0)
gain_amount = Decimal(0)
buy_count = 0
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
        pass
        sold_amount += amount
        gain_amount += amount * rate
        sell_count += 1
    
    #logger.debug(t[x])

rate_avg = spent_amount / bought_amount

logger.debug('bought_amount: ' + str(bought_amount))
logger.debug('spent_amount: ' + str(spent_amount))
logger.debug('sold_amount: ' + str(sold_amount))
logger.debug('gain_amount: ' + str(gain_amount))
logger.debug('sell_count: ' + str(sell_count))
logger.debug('rate_avg: ' + str(rate_avg))

if gain_amount > 0:
    profit = gain_amount - spent_amount
    
else:
    profit = Decimal(-1)

logger.info(profit)

sys.exit()
