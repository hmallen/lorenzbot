import configparser
import datetime
import logging
import os
import sys
from telegram.ext import Updater, CommandHandler
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

telegram_config_path = './.telegram_test.ini'
test_file = './test.txt'
exception_last_file = './exception_last.txt'


def telegram_send_exception(bot):
    user = '382606465'

    exception_msg = datetime.datetime.now().strftime('%m-%d-%Y, %H:%M:%S') + ' - Exception'
    
    bot.send_message(chat_id=user, text=exception_msg)
    bot.send_document(chat_id=user, document=open(exception_last_file, 'rb'))


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
    
    updater.start_polling()

    logger.debug('Sleeping 5 seconds.')
    time.sleep(5)
    logger.debug('Beginning...')

    try:
        a = float(1)
        b = float(0)

        c = a / b
        #c = b / a
        
    except Exception as e:
        logger.debug('[Exception]')
        logger.debug(e)

        with open(exception_last_file, 'w') as ex_file:
            ex_file.write(str(e))

        logger.debug('Wrote to file.')

        telegram_send_exception(updater.bot)

    except KeyboardInterrupt:
        logger.debug('[KeyboardInterrupt]')
        logger.debug('Exiting.')

    else:
        logger.debug('No exception.')

    finally:
        updater.stop()
        sys.exit()
