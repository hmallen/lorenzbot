import configparser
import logging
import os
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

telegram_config_path = './.telegram_test.ini'
test_file = './test.txt'


def telegram_test(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='New file!')
    bot.send_document(chat_id=update.message.chat_id, document=open(test_file, 'rb'))


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

    test_handler = CommandHandler('test', telegram_test)
    dispatcher.add_handler(test_handler)
    
    updater.start_polling()

    try:
        while (True):
            logger.info('Hello, world!')
            time.sleep(10)

    except Exception as e:
        logger.debug(e)

    except KeyboardInterrupt:
        logger.info('Exiting.')

    finally:
        updater.stop()
        sys.exit()
