import requests
from lxml import etree
import json
import time
import random
from qianqianyinyue.utils.mongo_pool import MongoPool
from qianqianyinyue.utils.random_useragent import random_user_agent
from qianqianyinyue.utils.log import logger
from pprint import pprint


class SongTotal(object):
    """根据作者的名字,获取作者的所有音乐作品"""

    def __init__(self):
        self.mongo_pool_ = MongoPool(collection="artist")
        self.mongo_pool = MongoPool(collection="songs")
        self.user_agent = random_user_agent

    def get_author_info(self, author_name):
        conditions = {"author_name": author_name}
        author_info = self.mongo_pool_.find_one(conditions)
        if author_info:
            author_info = {
                "author_name": author_info['author_name'],
                "author_tinguid": author_info['author_tinguid'],
                "author_url": author_info['author_url']
            }
            return author_info
        return None

    def get_requests(self, url, referer=None):
        headers = {
            "User-Agent": self.user_agent,
            "Referer": referer,
        }
        try:
            response = requests.get(url=url, headers=headers)
            if response.ok:
                html_str = response.content.decode()
                return html_str
            return None
        except Exception as e:
            logger.warning(e)
        time.sleep(random.uniform(0, 2))

    def parse_one_li(self, li):
        item = dict()
        song_name = li.xpath('./div[contains(@class,"songlist-title")]/span[@class="songname"]/a[1]/@title')
        item["song_name"] = song_name[0] if song_name else None
        song_href = li.xpath('./div[contains(@class,"songlist-title")]/span[@class="songname"]/a[1]/@href')
        song_id = song_href[0].rsplit('/', 1)[-1] if song_href else None
        item["song_id"] = song_id
        item['song_href'] = "http://music.taihe.com" + song_href[0] if song_href else "-1"
        # mv_id获取的有误
        song_mv_href = li.xpath('./div[contains(@class,"songlist-title")]/span[@class="songname"]/a[2]/@href')
        if song_mv_href:
            song_mv_id = song_href[0].rsplit('/', 1)[-1]
            item["song_mv_id"] = song_mv_id
            item['song_mv_href'] = "http://music.taihe.com" + song_mv_href[0]
        return item

    def parse_firstpage_html_str(self, html_str):
        html_str = etree.HTML(html_str)
        page_count = html_str.xpath(
            '//div[@class="list-box song-list-box active"]//div[@class="page_navigator-box"]//div[@class="page-inner"]/a[last()-1]/text()')
        page_count = int(page_count[0]) if page_count else -1
        li_list = html_str.xpath('//div[contains(@class,"song-list-wrap")]/ul/li')
        song_list = list()
        for li in li_list:
            item = self.parse_one_li(li=li)
            song_list.append(item)
        return song_list, page_count

    def parse_nextpage_html_str(self, data):
        data = json.loads(data)
        html_str = data["data"]["html"] if data else None
        if html_str:
            html_str = etree.HTML(html_str)
            li_list = html_str.xpath('//div[contains(@class, "song-list")]/ul/li')
            song_list = list()
            for li in li_list:
                item = self.parse_one_li(li=li)
                song_list.append(item)
            return song_list

    def parse_song_list(self, song_list, author_info):
        # 处理歌曲，构造存储结构
        song_ = {
            "author_info": author_info,
            "song_list": [],
        }
        for song in song_list:
            song.update(author_info)
            song_['song_list'].append(song)
        return song_

    def construct_url_list(self, ting_uid, page_count):
        base_url = "http://music.taihe.com/data/user/getsongs?start={}&size=15" + "&ting_uid={}".format(
            ting_uid)
        url_list = [base_url.format(i * 15) for i in range(1, page_count)]
        return url_list

    def insert_song_to_mongodb(self, song_):
        conditions = {"author_info.author_tinguid": song_["author_info"]["author_tinguid"]}
        song = self.mongo_pool.find_one(conditions)
        if not song:
            self.mongo_pool.insert_one(document=song_)

    def run(self, author_name=None):
        author_info = self.get_author_info(author_name)
        if author_info is None:
            print("该歌手不存在，请确认无误后再输入")
        else:
            # 验证数据库，有没有这个歌手的数据
            song__ = self.mongo_pool.find_one({'author_info.author_tinguid': author_info['author_tinguid']})
            if song__:
                print("歌手数据已存在，无需再发送请求")
            else:
                firstpage_html_str = self.get_requests(url=author_info["author_url"])
                if firstpage_html_str:
                    # 获取首页歌曲信息
                    song_list, page_count = self.parse_firstpage_html_str(html_str=firstpage_html_str)
                    # 该页面采用ajax接口，需要设计下一页url
                    url_list = self.construct_url_list(author_info['author_tinguid'], page_count)
                    for url in url_list:
                        # 发送单页请求
                        nextpage_html_data = self.get_requests(url=url, referer=author_info["author_url"])
                        song_list_next = self.parse_nextpage_html_str(data=nextpage_html_data)
                        song_list.extend(song_list_next)
                    song_ = self.parse_song_list(song_list, author_info)
                    self.insert_song_to_mongodb(song_)


if __name__ == "__main__":
    obj = SongTotal()
    obj.run(author_name="许嵩")
