import requests
import time
import random
import json
import re
from lxml import etree
from qianqianyinyue.utils.mongo_pool import MongoPool
from qianqianyinyue.utils.log import logger
from qianqianyinyue.utils.random_useragent import random_user_agent
from pprint import pprint


class SongInfoTotalUpdate(object):
    """
    根据作者的名字，更新该歌手的所有歌曲信息
    添加的信息有：
        发行日期
        发行公司
        歌曲下载链接及相关
        mv下载链接及相关
    """
    def __init__(self):
        self.mongo_pool = MongoPool(collection="songs")
        self.user_agent = random_user_agent

    def get_song_list(self, author_name):
        conditions = {"author_info.author_name": author_name}
        song_info = self.mongo_pool.find_one(conditions)
        song_list = song_info['song_list']
        return song_list

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

    def parse_html_str(self, html_str):
        html_str = etree.HTML(html_str)
        song_album = html_str.xpath('//div[@class="song-info-box fl"]/p[contains(@class, "album")]/a/text()')
        song_album = song_album[0] if song_album else None
        song_publish = html_str.xpath('//div[@class="song-info-box fl"]/p[contains(@class,"publish")]/text()')
        song_publish_date = song_publish[0].split(r"：", 1)[-1].strip() if song_publish else None
        song_company = html_str.xpath('//div[@class="song-info-box fl"]/p[contains(@class,"company")]/text()')
        song_publish_company = song_company[0].split(r"：", 1)[-1].strip() if song_company else None
        return song_album, song_publish_date, song_publish_company

    def parse_data(self, data):
        data = json.loads(data)
        if "bitrate" in data.keys():
            download_url = data['bitrate']['file_link']
            song_lrc_link = data['songinfo']['lrclink']
            return download_url, song_lrc_link
        return None, None

    def parse_mv_data(self, data):
        data = json.loads(data)
        mv_download_info = list()
        if "result" in data.keys():
            if "files" in data['result'].keys():
                file_info = data['result']['files']
                for k, v in file_info.items():
                    item = dict()
                    item['definition_name'] = v["definition_name"]
                    item['file_link'] = v['file_link']
                    mv_download_info.append(item)
        return mv_download_info

    def parse_mv_html_str(self, mv_html_str):
        mv_id = re.findall(r'href="/playmv/(.*?)"', mv_html_str, re.S)
        return mv_id[0] if mv_id else None

    def update_songs_info(self, info):
        conditions = {"author_info.author_tinguid": info["author_tinguid"]}
        songs_info = self.mongo_pool.find_one(conditions)
        for song_ in songs_info['song_list']:
            if info["song_id"] == song_['song_id']:
                song_.update(info)
        self.mongo_pool.update_one(conditions, songs_info)

    def get_content(self, song):
        global song_album, song_publish_date, song_publish_company
        mv_download_url_info = dict()
        song_href = song['song_href']
        html_str = self.get_requests(url=song_href)
        if html_str:
            song_album, song_publish_date, song_publish_company = self.parse_html_str(html_str)
        url = "http://musicapi.taihe.com/v1/restserver/ting?method=baidu.ting.song.playAAC&format=jsonp&songid={}&from=web".format(
            song['song_id'])
        data = self.get_requests(url=url, referer=song['song_href'])
        download_url, song_lrc_link = self.parse_data(data)
        if song.get("song_mv_href"):
            mv_html_str = self.get_requests(url=song['song_mv_href'])
            mv_id = self.parse_mv_html_str(mv_html_str)
            if mv_id:
                song["mv_id"] = mv_id
                mv_data_url = "http://musicapi.taihe.com/v1/restserver/ting?method=baidu.ting.mv.playMV&mv_id={}".format(
                    song['mv_id'])
                mv_data = self.get_requests(url=mv_data_url, referer=song["song_mv_href"])
                mv_download_url_info = self.parse_mv_data(mv_data)
        info = {
            "song_album": song_album,
            "song_publish_date": song_publish_date,
            "song_publish_company": song_publish_company,
            "download_url": download_url,
            "song_lrc_link": song_lrc_link,
            "mv_download_url_info": mv_download_url_info,
            'song_id': song['song_id'],
            "song_mv_id": song['song_mv_id'] if song.get('song_mv_id') else None,
            "author_tinguid": song["author_tinguid"],
        }
        return info

    def run(self, author_name=None):
        if author_name:
            song_list = self.get_song_list(author_name)
            for song in song_list:
                info = self.get_content(song)
                self.update_songs_info(info)
        else:
            print("请输入歌手名字")


if __name__ == "__main__":
    obj = SongInfoTotalUpdate()
    obj.run(author_name="许嵩")
