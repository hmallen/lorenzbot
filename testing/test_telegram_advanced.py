import configparser
import logging
import os
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import textwrap
import time

global telegram_failures

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

telegram_config_path = './.telegram_test.ini'

telegram_failures = 0


def telegram_connect(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id

    if connected_users.count(telegram_user) == 0:
        connected_users.append(telegram_user)
        
        logger.debug('[CONNECT] chat_id: ' + str(telegram_user))
        logger.info('Telegram user connected: ' + str(telegram_user))
        #logger.info('Connected Users: ' + str(connected_users))

        telegram_message = 'Subscribed to Lorenzbot alerts.'

    else:
        telegram_message = 'Already subscribed to Lorenzbot alerts.'
        
    logger.debug('[CONNECT] telegram_message: ' + telegram_message)
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.error('[CONNECT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1


def telegram_disconnect(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id

    if connected_users.count(telegram_user) > 0:
        connected_users.remove(telegram_user)
        
        logger.debug('[DISCONNECT] chat_id: ' + str(telegram_user))
        logger.info('Telegram user disconnected: ' + str(telegram_user))
        #logger.info('Connected Users: ' + str(connected_users))
        
        telegram_message = 'Unsubscribed from Lorenzbot alerts.'

    else:
        telegram_message = 'Not currently subscribed to Lorenzbot alerts.'

    logger.debug('[DISCONNECT] telegram_message: ' + telegram_message)
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.error('[DISCONNECT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1


def telegram_status(bot, update):
    global trade_usdt_remaining
    global telegram_failures
    
    telegram_user = update.message.chat_id
    
    logger.debug('[STATUS] chat_id: ' + str(telegram_user))
    logger.info('Telegram user requesting status: ' + str(telegram_user))

    if connected_users.count(telegram_user) > 0:
        logger.debug('Access confirmed for requesting user.')

        spent_msg = 'USDT Spent: ' + "{:.4f}".format(1234.123456) + '\n'
        bought_msg = 'STR Bought: ' + "{:.4f}".format(1234.123456) + '\n'
        rate_msg = 'Avg. Rate: ' + "{:.4f}".format(1234.123456) + '\n'
        base_msg = 'Base Price: ' + "{:.4f}".format(1234.123456) + '\n'
        market_msg = 'Mkt. Price: ' + "{:.4f}".format(1234.123456)# + '\n'

        telegram_message = spent_msg + bought_msg + rate_msg + base_msg + market_msg

    else:
        logger.warning('Access denied for requesting user.')
        
        telegram_message = 'Not currently in list of connected users. Type \"/connect\" to subscribe to alerts.'

    logger.debug('[STATUS] telegram_message: ' + telegram_message)
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.error('[STATUS] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1


def telegram_profit(bot, update):
    global telegram_failures
    
    telegram_user = update.message.chat_id
    
    logger.debug('[PROFIT] chat_id: ' + str(telegram_user))
    logger.info('Telegram user requesting profit calculation: ' + str(telegram_user))

    if connected_users.count(telegram_user) > 0:
        logger.debug('Access confirmed for requesting user.')

        telegram_message = 'Profit.'
    
    else:
        logger.warning('Access denied for requesting user.')
        
        telegram_message = 'Not currently in list of connected users. Type \"/connect\" to connect to Lorenzbot.'

    logger.debug('[PROFIT] telegram_message: ' + telegram_message)
    try:
        bot.send_message(chat_id=telegram_user, text=telegram_message)
    except Exception as e:
        logger.error('[PROFIT] Exception occurred while sending telegram message.')
        logger.exception(e)
        telegram_failures += 1


def telegram_test(bot, update):
    bot.send_chat_action(chat_id=update.message.chat_id, action=updater.ChatAction.TYPING)

    time.sleep(5)

    bot.send_message(chat_id=update.message.chat_id, text='Hello, world!')


def telegram_send_message(bot, trade_message):
    global telegram_failures
    
    logger.debug('trade_message: ' + trade_message)

    if len(connected_users) > 0:
        for user in connected_users:
            try:
                bot.send_message(chat_id=user, text=trade_message)
                logger.debug('Sent alert to user ' + str(user) + '.')
            except Exception as e:
                logger.error('[SEND] Exception occurred while sending telegram message.')
                logger.exception(e)
                telegram_failures += 1
    
    else:
        logger.debug('No Telegram users connected. Message not sent.')


if __name__ == '__main__':
    if not os.path.isfile(telegram_config_path):
        logger.error('No Telegram config file found! Must create \".telegram.ini\". Exiting.')
        sys.exit(1)
    else:
        logger.info('Found Telegram config file.')

    config = configparser.ConfigParser()

    # Set Telegram token
    config.read(telegram_config_path)
    telegram_token = config['lorenzbot_test']['token']
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

    test_handler = CommandHandler('test', telegram_test)
    dispatcher.add_handler(test_handler)

    connected_users = []

    try:
        updater.start_polling()

#    try:
#        while (True):
#            logger.debug('Waiting for input...')
#            time.sleep(30)

    except Exception as e:
        logger.debug(e)

    except KeyboardInterrupt:
        logger.info('Exiting.')
        updater.stop()
        sys.exit()
