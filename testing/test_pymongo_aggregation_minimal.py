from decimal import *
from pymongo import MongoClient
import sys

client = MongoClient()
client.drop_database('test_db')

db = client.test_db
coll_current = 'test_coll'

for x in range(0, 5):
    result = db.test_coll.insert_one({'amount': 2, 'price': (x + 1)})

# Amount total
pipeline = [{
    '$group': {
        '_id': None,
        'amount_sum': {'$sum': '$amount'}
        }
    }]

agg = db.command('aggregate', coll_current, pipeline=pipeline)
print(agg)
print()
print('----')
print()

# Spending total
pipeline = [{
     '$project': {
        '_id': None,
        'amount_spent': {'$multiply': ['$amount', '$price']}
        }
     }]

agg = db.command('aggregate', coll_current, pipeline=pipeline)['result']

spending_total = Decimal(0)
for x in range(0, len(agg)):
    spending_total += Decimal(agg[x]['amount_spent'])
print(spending_total)
sys.exit()
