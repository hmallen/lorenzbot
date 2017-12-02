import configparser
from decimal import *
import logging
import poloniex

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

withdraw_address = 'GBHB5IEQA7YMIGQ6J4B2S7T7AN5RJXRQZUTMUOFRP2OJBP3NBX67DDOC'

config = configparser.ConfigParser()
config.read('../config/poloniex.ini')

polo = poloniex.Poloniex()
polo.key = config['live']['key']
polo.secret = config['live']['secret']


def withdraw_profit(withdraw_amount):
    response = polo.withdraw('STR', withdraw_amount, withdraw_address)
    logger.debug('withdraw_response: ' + str(response))
    # Should be --> {'response': 'Withdrew 1.00000000 STR.'}

    return response


if __name__ == '__main__':
    try:
        amt = Decimal(1)
        withdraw_response = withdraw_profit(amt)
    except Exception as e:
        logger.debug(e)

    try:
        withdraw_message = withdraw_response['response']
        logger.info('Withdraw successful.')
    except:
        logger.info('Withdraw failed.')
