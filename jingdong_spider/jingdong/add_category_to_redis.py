import sys

sys.path.append('../')
import pickle
from pymongo import MongoClient
from redis import StrictRedis
from jingdong.settings import MONGO_URL, REDIS_URL
from jingdong.spiders.product_1 import Product1Spider


def add_category_to_redis():
    mongo_client = MongoClient(MONGO_URL)
    redis_client = StrictRedis.from_url(REDIS_URL)
    collection = mongo_client['jingdong']['category']
    cursor = collection.find()
    for cur_ in cursor:
        cur_.pop('_id')
        cur = pickle.dumps(cur_)
        redis_client.lpush(Product1Spider.redis_key, cur)
        break
    mongo_client.close()
    redis_client.close()


if __name__ == "__main__":
    add_category_to_redis()
