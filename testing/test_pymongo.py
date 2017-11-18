from pymongo import MongoClient

client = MongoClient()

db_names = client.database_names()
print(db_names)

db = client.test_db

db_coll = db.collection_names()
print(db_coll)

result = db.stuff.insert_one({'x': 1, 'y': 2, 'z': 3})
print(result)

info = result.inserted_id
print(info)

db_coll = db.collection_names()
print(db_coll)
