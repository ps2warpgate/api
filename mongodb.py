from pymongo import MongoClient
from pprint import pprint

client = MongoClient('mongodb://192.168.1.247:27017/')
db = client.warpgate
collection = db.connery

pprint(collection.find_one())