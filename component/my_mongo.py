import pymongo

from config import app_conf

mongo_host = app_conf["mongo"]["host"]
mongo_port = app_conf["mongo"]["port"]
mongo_db = app_conf["mongo"]["db"]
mongo_username = app_conf["mongo"]["username"]
mongo_password = app_conf["mongo"]["password"]

conn = pymongo.MongoClient("mongodb://%s:%s@%s:%s/" % (
    mongo_username, mongo_password, mongo_host, mongo_port))
mongodb = conn[mongo_db]
print("success init mongodb")
