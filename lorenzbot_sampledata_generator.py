import datetime
import logging
import poloniex
from pymongo import MongoClient
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

taker_fee = 0.0025

try:
    polo = poloniex.Poloniex()
except:
    logger.exception('Failed to connect to Poloniex API. Exiting.')
    sys.exit(1)

db = MongoClient().lorenzbot

drop_collections = True

if drop_collections == True:
    logger.info('Dropping all collections from database.')
    for name in db.collection_names():
        db.drop_collection(name)

coll_names = db.collection_names()

try:
    # Retrieve latest collection
    coll_current = coll_names[(len(coll_names) - 1)]
    logger.info('Found existing collection: ' + coll_current)
except:
    # If none found, create new
    logger.error('No collections found in database.')
    coll_current = datetime.datetime.now().strftime('%m%d%Y_%H%M%S')
    db.create_collection(coll_current)
    #sys.exit(1)

#trade_price = polo.returnTicker()['USDT_STR']['lowestAsk']
#print('lowestAsk: ' + trade_price)
response = db[coll_current].insert_one({'amount': (1 - taker_fee), 'price': float(polo.returnTicker()['USDT_STR']['lowestAsk'])})
print(response)
