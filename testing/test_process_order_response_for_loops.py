# BUY ORDER RESPONSE PROCESSING
order_list = []
logger.debug('len(order_trades): ' + str(len(order_trades)))
for x in range(0, len(order_trades)):
    order_rate = Decimal(order_trades[x]['rate'])
    order_amount = Decimal(order_trades[x]['amount']) * (Decimal(1) - Decimal(order_trades[x]['fee']))
    order_list.append([order_amount, order_rate])

logger.debug('len(order_list): ' + str(len(order_list)))
logger.debug('order_list: ' + str(order_list))

amount_total = Decimal(0)
rate_calc_total = Decimal(0)
for x in range(0, len(order_list)):
    rate_calc_total += order_list[x][0] * order_list[x][1]
    amount_total += order_list[x][0]
order_average_rate = rate_calc_total / amount_total

logger.debug('rate_calc_total:    ' + "{:.8f}".format(rate_calc_total))
logger.debug('amount_total:       ' + "{:.8f}".format(amount_total))
logger.debug('order_average_rate: ' + "{:.8f}".format(order_average_rate))

"""
    order_list = []
    trade_total = Decimal(0)
    for x in range(0, len(order_trades)):
        order_rate = Decimal(order_trades[x]['rate'])
        order_amount = Decimal(order_trades[x]['amount'])
        order_fee_multiplier = Decimal(1) - Decimal(order_trades[x]['fee'])
        
        trade_total = (order_rate * order_amount) * order_fee_multiplier

        list_item = [order_rate, trade_total]
        
        #order_list.append((order_rate, trade_total))
        order_list.append(list_item)

    rate_calc_total = Decimal(0)
    amount_total = Decimal(0)
    for x in range(0, len(order_list)):
        rate_calc_total += order_list[x][0] * order_list[x][1]
        amount_total += order_list[x][1]
    order_average_rate = rate_calc_total / amount_total
"""
