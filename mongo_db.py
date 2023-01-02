import pymongo


def auth_to_mongo_db():
    client = pymongo.MongoClient("mongodb+srv://admin:admin@mycluster.ezxpvsw.mongodb.net/?retryWrites=true&w=majority")
    database = client['scrap_comments']
    return database


def create_collection(database):
    return database['comments']


def insert_into_collection(collection, document):
    collection.insert_one(document)

