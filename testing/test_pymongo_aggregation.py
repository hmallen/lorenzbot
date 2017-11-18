from decimal import *
from pymongo import MongoClient

client = MongoClient()
client.drop_database('test_db')

db = client.test_db

for x in range(0, 5):
    result = db.stuff.insert_one({'x': (x + 1), 'y': 2})

"""
pipeline = [{
    '$project': {
        '_id': None,
        'weighted_total': {
            '$multiply': [ '$amount', '$price' ]
            }
        }},
            {
    '$project': {
        '_id': None,
        'weighted_average': {
            '$divide': [ '$weighted_total', 5 ]
            }
      }}]

pipeline = [{'$group': {
    '_id': None,
    'amount': {'$avg': '$x'},
    'price': {'$sum': '$y'},
    'combined': {'$multiply': ['$x', '$y']}
    }}]
"""

pipeline = [{
    '$project': {
        '_id': None,
        'weighted_total': {
            '$multiply': [ '$x', '$y' ]
            }
        }}]
agg_result = db.command('aggregate', 'stuff', pipeline=pipeline)['result']

#print(agg)

#agg_result = agg['result']
print(agg_result)
print()

result_tot = Decimal(0)
for x in range(0, len(agg_result)):
    result_tot += Decimal(agg_result[x]['weighted_total'])
result_avg = result_tot / Decimal(len(agg_result))
print(result_avg)

#mult = agg['result']
#print(mult)

#price_mean = Decimal(agg['result'][0]['price_mean'])
#amount_sum = Decimal(agg['result'][0]['amount_sum'])
#combined = Decimal(agg['result'][0]['combined'])
#print(price_mean)
#print(amount_sum)
#print(combined)

#print(price_mean / amount_sum)
#print((1.123 + 2.123 + 3.123 + 4.123 + 5.123) / 5)
