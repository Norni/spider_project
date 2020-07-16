import requests
import json
import time
import random
from qianqianyinyue.utils.mongo_pool import MongoPool
from qianqianyinyue.utils.random_useragent import random_user_agent
from qianqianyinyue.utils.log import logger
from pprint import pprint


class AuthorInfoUpdate(object):
    """更新数据库中，作者的其他相关信息"""
    def __init__(self):
        self.mongo_pool = MongoPool(collection='artist')
        self.url = "http://music.taihe.com/data/tingapi/v1/restserver/ting?method=baidu.ting.artist.getInfo&from=web&tinguid={}"
        self.user_agent = random_user_agent

    def get_response(self, url, user_agent):
        headers = {
            "User-agent": user_agent
        }
        try:
            response = requests.get(url=url, headers=headers)
            # print(response.text)
            if response.ok:
                response = json.loads(response.content.decode())
                if "name" in response.keys():
                    return response
                return dict()
        except Exception as e:
            logger.warning(e)
        time.sleep(random.uniform(1, 3))

    def parse_data(self, data):
        item = dict()
        item['author_tinguid'] = data['ting_uid']
        item['author_name'] = data['name']
        item['author_share_num'] = data['share_num']
        item['author_hot'] = data['hot']
        item['author_from_area'] = data['country']
        item['author_gender'] = "男" if data['gender'] == "0" else "女"
        item['author_image_url'] = data['avatar_s1000']
        item["author_intro"] = data['intro']
        item['author_birthday'] = data['birth']
        item['author_constellation'] = data['constellation']
        item['author_stature'] = data['stature']
        item['author_weight'] = data['weight']
        item['author_songs_total'] = data['songs_total']
        return item

    def update_data_to_mongodb(self, item):
        conditions = {
            "author_name": item['author_name'],
            'author_tinguid': item['author_tinguid']
        }
        self.mongo_pool.update_one(conditions=conditions, document=item)

    def run(self):
        artists = self.mongo_pool.find_all()
        for artist in artists:
            ting_uid = artist['author_tinguid']
            if "author_intro" in artist.keys():
                pass
            else:
                url = self.url.format(ting_uid)
                dict_data = self.get_response(url=url, user_agent=self.user_agent)
                if dict_data:
                    item = self.parse_data(data=dict_data)
                    self.update_data_to_mongodb(item=item)


if __name__ == "__main__":
    obj = AuthorInfoUpdate()
    obj.run()
