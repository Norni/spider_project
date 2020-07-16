import requests
from lxml import etree
from qianqianyinyue.utils.mongo_pool import MongoPool
from qianqianyinyue.utils.random_useragent import random_user_agent
from qianqianyinyue.utils.log import logger


class ArtistTotal(object):
    """
        预先执行的程序，获取该网站曲库，所有的音乐作者的信息
        信息包括：
            作者id: 对应数据库字段--->>>“author_tinguid”
            作者的首页url：对应数据库字段--->>>“author_url”
            作者的名字：对应数据库字段--->>>“author_name”
    """
    def __init__(self):
        self.mongo_pool = MongoPool(collection='artist')
        self.url = "http://music.taihe.com/artist"
        self.user_agent = random_user_agent

    def get_response(self, url, user_agent):
        headers = {
            "User-Agent": user_agent
        }
        try:
            response = requests.get(url=url, headers=headers)
            if response.ok:
                return response.content.decode()
        except Exception as e:
            logger.warning(e)

    def parse_html_str(self, html_str):
        html_str = etree.HTML(html_str)
        b_li_list = html_str.xpath("//ul[@class=\"container\"]/li[position()>1]")
        for b_li in b_li_list:
            s_li = b_li.xpath('./ul/li')
            for li in s_li:
                item = dict()
                item["author_name"] = li.xpath('./a/@title')[0] if li.xpath('./a/@title') else None
                author_url = "http://music.taihe.com"+li.xpath('./a/@href')[0] if li.xpath('./a/@href') else "-1"
                item["author_url"] = author_url
                item["author_tinguid"] = author_url.rsplit('/', 1)[-1]
                yield item

    def insert_to_mongodb(self, documents):
        for document in documents:
            self.mongo_pool.insert_one(document=document)

    def run(self):
        response = self.get_response(url=self.url, user_agent=self.user_agent)
        author_infos = self.parse_html_str(html_str=response)
        self.insert_to_mongodb(documents=author_infos)


if __name__ == "__main__":
    obj = ArtistTotal()
    obj.run()
