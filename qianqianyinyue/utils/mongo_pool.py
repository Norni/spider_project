from pymongo import MongoClient
from qianqianyinyue.settings import MONGO_URL
from qianqianyinyue.utils.log import logger


class MongoPool(object):

    def __init__(self, collection):
        self.mongo_client = MongoClient(MONGO_URL)
        self.collections = self.mongo_client['qianqianyinyue'][collection]

    def __del__(self):
        self.mongo_client.close()

    def insert_one(self, document):
        self.collections.insert_one(document)
        logger.info("插入了新的数据:{}".format(document))

    def update_one(self, conditions, document):
        self.collections.update_one(filter=conditions, update={"$set": document})
        logger.info("更新了->{}<-的数据".format(conditions))

    def find_one(self, conditions):
        collections = self.collections.find(filter=conditions)
        for item in collections:
            item.pop('_id')
            return item

    def find_all(self):
        collections = self.collections.find()
        for item in collections:
            item.pop('_id')
            yield item
