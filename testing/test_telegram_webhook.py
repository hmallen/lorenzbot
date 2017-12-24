import configparser
import logging
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('../config/telegram.ini')
telegram_token = config['lorenzbot']['token']

telegram_active = False
connected_users = []


def telegram_connect(bot, update):
    global msg_chat_id, connected_users, telegram_active
    
    msg_chat_id = update.message.chat_id
    connected_users.append(msg_chat_id)
    
    logger.debug('[CONNECT] chat_id: ' + str(msg_chat_id))
    logger.info('Connected User: ' + str(msg_chat_id))
    logger.info('Connected Users: ' + str(connected_users))

    telegram_active = True
    
    bot.send_message(chat_id=msg_chat_id, text="Connected to Lorenzbot.")


def telegram_disconnect(bot, update):
    global msg_chat_id, connected_users, telegram_active
    
    msg_chat_id = update.message.chat_id
    connected_users.remove(msg_chat_id)
    
    logger.debug('[DISCONNECT] chat_id: ' + str(msg_chat_id))
    logger.info('Disconnected User: ' + str(msg_chat_id))
    logger.info('Connected Users: ' + str(connected_users))

    telegram_active = False
    
    bot.send_message(chat_id=msg_chat_id, text="Disconnected from Lorenzbot.")


def telegram_echo(bot, update):
    global msg_chat_id
    
    msg_chat_id = update.message.chat_id
    logger.info('[ECHO] chat_id: ' + str(msg_chat_id))

    if telegram_active == True:
        bot.send_message(chat_id=msg_chat_id, text=update.message.text)
    else:
        logger.warning('Telegram not active. Send \'/connect\' to activate.')


def telegram_send_message(bot, trade_message):
    global msg_chat_id, connected_users, telegram_active

    msg_chat_id = connected_users[0]
    logger.info('[SEND] chat_id: ' + str(msg_chat_id))

    bot.send_message(chat_id=msg_chat_id, text=trade_message)


if __name__ == '__main__':
    try:
        updater = Updater(token=telegram_token)
        dispatcher = updater.dispatcher

        connect_handler = CommandHandler('connect', telegram_connect)
        dispatcher.add_handler(connect_handler)

        disconnect_handler = CommandHandler('disconnect', telegram_disconnect)
        dispatcher.add_handler(disconnect_handler)

        echo_handler = MessageHandler(Filters.text, telegram_echo)
        dispatcher.add_handler(echo_handler)

        #updater.start_polling()
        wh_url = 'https://47.185.146.37.com:8443/' + telegram_token
        updater.start_webhook(listen='0.0.0.0',
                              port=8443,
                              url_path=telegram_token,
                              key='private.key',
                              cert='cert.pem',
                              webhook_url=wh_url)

        telegram_state_last = None
        loop_start = time.time()
        while (True):
            if telegram_active != telegram_state_last:
                logger.info('telegram_active: ' + str(telegram_active))
                telegram_state_last = telegram_active

            if (time.time() - loop_start) > 30:
                if telegram_active == True:
                    telegram_send_message(updater.bot, 'Hello, world!')
                    logger.info('Sent message.')
                else:
                    logger.info('Telegram not active.')
                loop_start = time.time()

    except Exception as e:
        logger.exception(e)

    except KeyboardInterrupt:
        logger.debug('Pre-stop')
        updater.stop()
        logger.debug('Post-stop')
        sys.exit()
