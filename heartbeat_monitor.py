#!./env/bin/python

import argparse
import configparser
import logging
import os
import sys
from telegram.ext import Updater
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Include DEBUG level output.')
parser.add_argument('-t', '--time', type=float, required=True, help='Loop time used on heartbeat client.')
parser.add_argument('--notelegram', action='store_true', default=False, help='Disable Telegram alert messages.')
args = parser.parse_args()

debug = args.debug
if debug == False:
    logger.setLevel(level=logging.INFO)
logger.debug('[SERVER] debug: ' + str(debug))

check_time = args.time
logger.debug('[SERVER] check_time: ' + "{:.2f}".format(check_time))

telegram_disable = args.notelegram
logger.debug('[SERVER] telegram_disable: ' + str(telegram_disable))

heartbeat_file = 'hb.txt'
telegram_config_path = 'config/telegram.ini'
telegram_user_file = 'telegram_users.txt'

telegram_time_last = time.time() - 900  # Subtract inter-alert delay to ensure alert sent on first attempt, if necessary


def heartbeat_check():
    try:
        with open(heartbeat_file, 'r') as hb:
            hb_time = float(hb.read())

        return hb_time

    except Exception as e:
        logger.exception('[SERVER] Exception occurred while checking heartbeat.')
        raise


def telegram_send_alert(bot, telegram_users):
    global msg_chat_id, connected_users, telegram_active

    if len(telegram_users) > 0:
        for user in telegram_users:
            try:
                bot.send_message(chat_id=user, text='No heartbeat detected!')           
            except Exception as e:
                logger.exception('[SERVER] Exception occurred while sending Telegram alert.')
                raise
    else:
        logger.debug('[SERVER] No Telegram users connected. Alert not sent.')


def telegram_load_users():
    telegram_users = []
    
    if os.path.isfile(telegram_user_file):
        logger.info('[SERVER] Found Telegram user file. Loading connected users.')
        with open(telegram_user_file, 'r') as user_file:
            user_string = user_file.read()
        user_array = user_string.split('\n')
        for user in user_array:
            if user != '' and telegram_users.count(int(user)) == 0:
                telegram_users.append(int(user))
                logger.info('Connected User: ' + user)
    
    else:
        logger.info('[SERVER] No Telegram user file found. Creating empty file.')
        with open(telegram_user_file, 'w') as user_file:
            pass

    return telegram_users


if __name__ == '__main__':
    heartbeat_still_count = 0

    try:
        if telegram_disable == False:
            config = configparser.ConfigParser()
            config.read(telegram_config_path)
            telegram_token = config['lorenzbot']['token']
            
            updater = Updater(token=telegram_token)
            dispatcher = updater.dispatcher

            updater.start_polling()

            connected_users = []
            
        while (True):
            heartbeat_diff = time.time() - heartbeat_check()
            logger.debug('[SERVER] Last heartbeat ' + "{:.2f}".format(heartbeat_diff) + ' seconds ago.')

            if heartbeat_diff > check_time:
                heartbeat_still_count += 1
            else:
                heartbeat_still_count = 0

            if heartbeat_still_count >= 3:
                logger.error('[SERVER] Heartbeat not detected for at least 3 checks.')

                if telegram_disable == False:
                    if (time.time() - telegram_time_last) < 900:
                        logger.debug('[SERVER] Telegram alert delay hasn\'t elapsed. Skipping Telegram alert.')
                    else:
                        # Load connected Telegram users from file
                        connected_users = telegram_load_users()
                        logger.debug('connected_users: ' + str(connected_users))
                        
                        # Alert user of heartbeat timeout
                        logger.debug('[SERVER] Heartbeat timeout. Sending Telegram alert.')
                        telegram_send_alert(updater.bot, connected_users)

                        telegram_time_last = time.time()

            logger.debug('[SERVER] heartbeat_still_count: ' + str(heartbeat_still_count))

            time.sleep(check_time)

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        logger.debug('[SERVER] Exit signal received.')
        if telegram_disable == False:
            updater.stop()
        sys.exit()
