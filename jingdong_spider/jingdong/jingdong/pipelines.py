# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from jingdong.settings import MONGO_URL


class CategoryPipeline(object):
    def open_spider(self, spider):
        if spider.name == 'cate':
            self.mongo_client = MongoClient(MONGO_URL)
            self.category = self.mongo_client['jingdong']["category"]

    def close_spider(self, spider):
        if spider.name == "cate":
            self.mongo_client.close()

    def process_item(self, item, spider):
        if spider.name == 'cate':
            self.category.insert_one(dict(item))
        return item


class ProductPipeline(object):
    def open_spider(self, spider):
        if spider.name == 'product_1':
            self.mongo_client = MongoClient(MONGO_URL)
            self.category = self.mongo_client['jingdong']["product"]

    def close_spider(self, spider):
        if spider.name == "product_1":
            self.mongo_client.close()

    def process_item(self, item, spider):
        if spider.name == 'product_1':
            self.category.insert_one(dict(item))
        return item
