#!../env/bin/python
# -*- coding: utf-8 -*-
"""Simple Bot to reply to Telegram messages.
This is built on the API wrapper, see echobot2.py to see the same example built
on the telegram.ext bot framework.
This program is dedicated to the public domain under the CC0 license.
"""

import configparser
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep


update_id = None

telegram_config_path = '../config/telegram.ini'

config = configparser.ConfigParser()
config.read(telegram_config_path)
telegram_token = config['lorenzbot']['token']


def main(token):
    """Run the bot."""
    global update_id
    # Telegram Bot Authorization Token
    bot = telegram.Bot(token)

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


def echo(bot):
    """Echo the message the user sent."""
    global update_id
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.message:  # your bot can receive updates without messages
            # Reply to the message
            #update.message.reply_text(update.message.text)
            send(bot)


def send(bot):
    try:
        bot.send_message(chat_id=382606465, text='Hello, world!')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main(telegram_token)
