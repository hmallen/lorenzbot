#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import logging
from multiprocessing.dummy import Process as Thread
from poloniex import Poloniex
from pymongo import MongoClient
import websocket

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Ticker(object):
    def __init__(self, api=None):
        self.api = api
        if not self.api:
            self.api = Poloniex(jsonNums=float)
            
        self.db = MongoClient().poloniex['ticker']
        self.db.drop()
        
        self._ws = websocket.WebSocketApp("wss://api2.poloniex.com/",
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)

    def on_message(self, ws, message):
        message = json.loads(message)
        if 'error' in message:
            return logger.error(message['error'])

        if message[0] == 1002:
            if message[1] == 1:
                return logger.info('Subscribed to ticker.')

            if message[1] == 0:
                return logger.info('Unsubscribed from ticker')

            data = message[2]

            self.db.update_one(
                {"id": float(data[0])},
                {"$set": {'last': data[1],
                          'lowestAsk': data[2],
                          'highestBid': data[3],
                          'percentChange': data[4],
                          'baseVolume': data[5],
                          'quoteVolume': data[6],
                          'isFrozen': data[7],
                          'high24hr': data[8],
                          'low24hr': data[9]
                          }},
                upsert=True)

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws):
        if self._t._running:
            try:
                self.stop()
            except Exception as e:
                logger.exception(e)
            try:
                self.start()
            except Exception as e:
                logger.exception(e)
                self.stop()
        else:
            logger.info("Websocket closed!")

    def on_open(self, ws):
        tick = self.api.returnTicker()
        for market in tick:
            self.db.update_one(
                {'_id': market},
                {'$set': tick[market]},
                upsert=True)
        self._ws.send(json.dumps({'command': 'subscribe', 'channel': 1002}))

    @property
    def status(self):
        try:
            return self._t._running
        except:
            return False

    def start(self):
        self._t = Thread(target=self._ws.run_forever)
        self._t.daemon = True
        self._t._running = True
        self._t.start()
        logger.info('Websocket thread started.')

    def stop(self):
        self._t._running = False
        self._ws.close()
        self._t.join()
        logger.info('Websocket thread stopped.')

    def __call__(self, market=None):
        """ returns ticker from mongodb """
        if market:
            return self.db.find_one({'_id': market})
        return list(self.db.find())
