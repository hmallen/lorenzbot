import csv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

test_list = []
test_list_nosell = []
tests = []

with open('test_csv.csv', newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')

    try:
        for row in csv_reader:
            test_list.append(row)

    except csv.Error as e:
        logger.exception('EXCEPTION: ' + str(e))

tests.append(test_list)

with open('test_csv_nosell.csv', newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')

    try:
        for row in csv_reader:
            test_list_nosell.append(row)

    except csv.Error as e:
        logger.exception('EXCEPTION: ' + str(e))

tests.append(test_list_nosell)

for t in tests:
    logger.debug('')
    
    bought_amount = 0
    spent_amount = 0
    sold_amount = 0
    gain_amount = 0
    for x in range(0, len(t)):
        trade_position = t[x][1]
        amount = float(t[x][2])
        rate = float(t[x][3])

        if trade_position == 'buy':
            bought_amount += amount
            spent_amount += amount * rate
        elif trade_position == 'sell':
            sold_amount += amount
            gain_amount += amount * rate
        
        logger.debug(t[x])

    rate_avg = spent_amount / bought_amount

    logger.debug(bought_amount)
    logger.debug(spent_amount)
    logger.debug(rate_avg)

    if gain_amount > 0:
        profit = gain_amount - spent_amount
        logger.debug(profit)
    else:
        logger.debug('No sells.')
