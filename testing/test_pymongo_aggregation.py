from decimal import *
from pymongo import MongoClient
import sys

client = MongoClient()
client.drop_database('test_db')

db = client.test_db

for x in range(0, 5):
    result = db.stuff.insert_one({'x': (x + 1), 'y': 2})

# Weighted total
pipeline = [{
     '$project': {
        '_id': None,
        'weighted_total': {'$multiply': ['$x', '$y']}
        }
     }]
agg_result = db.command('aggregate', 'stuff', pipeline=pipeline)['result']

result_tot = Decimal(0)
for x in range(0, len(agg_result)):
    result_tot += Decimal(agg_result[x]['weighted_total'])
    print(result_tot)

# Trade amount sum
pipeline = [{
    '$group': {
        '_id': None,
        'amount_sum': {'$sum': '$y'}
        }
    }]
agg_result = db.command('aggregate', 'stuff', pipeline=pipeline)['result']
print('----')
print(agg_result)
print('----')
amount_total = Decimal(agg_result[0]['amount_sum'])
print(amount_total)
print('----')
base_price = result_tot / amount_total
print(base_price)
sys.exit()
