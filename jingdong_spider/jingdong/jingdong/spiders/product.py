import scrapy
import re
from pprint import pprint


class ProductSpider(scrapy.Spider):
    name = 'product'
    allowed_domains = ['jd.com']
    a = list()
    start_urls = ['https://search.jd.com/Search?keyword=%E6%B8%B8%E6%88%8F%E6%89%8B%E6%9C%BA&qrst=1&stock=1&page=1']

    def parse(self, response):
        html_str = response.body.decode()
        page_info = dict()
        # 获取页面总数
        page_count = re.compile(r'page_count:\"(.*?)\"', re.S).findall(html_str)
        page_info["page_count"] = int(page_count[0]) if page_count else None
        # 获取页面当页数
        page_current = re.compile(r'page:"(.*?)",page_count', re.S).findall(html_str)
        page_info["page_current"] = int(page_current[0]) if page_count else None
        # 获取所有的产品信息
        page_info["product_list"] = list()
        product_info_list = re.compile(r'class="p-img"(.*?)class="p-icons"', re.S).findall(html_str)
        ## 获取单个产品的信息
        for one_product_info in product_info_list:
            info = dict()
            # 获取标题及链接
            str_ = re.compile(r'p-name p-name-type-2(.*?)</div>', re.S).findall(one_product_info)[0]
            title = re.compile(r'em>(.*?)</em>', re.S).findall(str_)
            info["title"] = re.sub(r'\n|\t|\s|(<.*?>)', '', title[0]).strip() if title else None
            href = re.compile(r'href="(.*?)"', re.S).findall(str_)
            info["href"] = "https:" + href[0] if href else None
            # 获取价格
            str_ = re.compile(r'class="p-price"(.*?)</div>', re.S).findall(one_product_info)[0]
            price = re.compile(r'i>(.*?)</i>', re.S).findall(str_)
            info["price"] = price[0] if price else None
            # 获取图片
            info["pic_info"] = list()
            img_list = re.compile(r'class="ps-item">(.*?)</li>', re.S).findall(one_product_info)
            if img_list:
                for img in img_list:
                    pic_info_ = dict()
                    pic_title = re.compile(r'title="(.*?)">', re.S).findall(img)
                    pic_info_["pic_title"] = pic_title[0] if pic_title else None
                    pic_href = re.compile(r'data-lazy-img="(.*?)"', re.S).findall(img)
                    pic_info_["pic_href"] = "https:" + pic_href[0] if pic_href else "---"
                    info["pic_info"].append(pic_info_)
            else:
                pic_url = re.compile(r'data-img="1" src="(.*?)" data-lazy-img', re.S).findall(one_product_info)
                img_url = "https:" + pic_url[0] if pic_url else "---"
                info['pic_info'].append(img_url)
            # 获取评价连接
            info["comment_href"] = info["href"] + "#comment"
            # 获取售卖店铺及链接
            info["store"] = dict()
            str_ = re.compile(r'class="p-shop"(.*?)</div>', re.S).findall(one_product_info)[0]
            shop_name = re.compile(r'title="(.*?)"', re.S).findall(str_)
            info["store"]["shop_name"] = shop_name[0] if shop_name else None
            shop_href = re.compile(r'href="(.*?)"', re.S).findall(str_)
            info["store"]["shop_href"] = "https:" + shop_href[0] if shop_href else None
            # 将单个产品添加到产品列表
            page_info["product_list"].append(info)
        pprint(page_info)
        next_page = "page={}".format(int(page_info["page_current"])+1)
        keyword = re.findall(r'keyword=(.*?)&', response.url, re.S)[0]
        url_ = "https://search.jd.com/s_new.php?keyword={}&s=30&page=1".format(keyword)
        next_url = url_.split('page=')[0] + next_page
        if page_info['page_current']:
            while int(page_info['page_current']) <= int(page_info['page_count']):
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse
                )

