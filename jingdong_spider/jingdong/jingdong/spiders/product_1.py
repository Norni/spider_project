import scrapy
from urllib import parse
from jingdong.items import ProductItem
import re
import json
import jsonpath
from copy import deepcopy
from pprint import pprint
from scrapy_redis import spiders
import pickle


class Product1Spider(spiders.RedisSpider):
    name = 'product_1'
    allowed_domains = ['jd.com', 'p.3.cn']
    redis_key = 'product_1:category'
    # start_urls = ['https://search.jd.com/Search?keyword=%E6%B8%B8%E6%88%8F%E6%89%8B%E6%9C%BA']

    # def start_requests(self):
    #     category = {
    #         'b_cate':
    #             [
    #                 {'b_name': '美妆', 'b_url': 'https://beauty.jd.com/'},
    #                 {'b_name': '个护清洁', 'b_url': 'https://channel.jd.com/beauty.html'},
    #                 {'b_name': '宠物', 'b_url': 'https://channel.jd.com/pet.html'}],
    #         'm_cate':
    #             [
    #                 {'m_name': '面部护肤', 'm_url': 'https://channel.jd.com/1316-1381.html'}],
    #         's_cate':
    #             [
    #                 {'s_name': '精华', 's_url': 'https://list.jd.com/list.html?cat=1316,1381,13546'}]}
    #     yield scrapy.Request(
    #         url="https://search.jd.com/Search?keyword={}".format(parse.quote(category["s_cate"][0]['s_name'])),
    #         callback=self.parse,
    #         meta={"item": category}
    #     )

    def make_request_from_data(self, data):
        # 根据redis中读取的数据构建请求
        category = pickle.loads(data)
        return scrapy.Request(
            url="https://search.jd.com/Search?keyword={}".format(parse.quote(category["s_cate"][0]['s_name'])),
            callback=self.parse,
            meta={"item": category}
        )

    def parse(self, response):
        product_category = response.meta['item']
        product = ProductItem()
        product['product_category'] = product_category
        html_str = response.body.decode()
        li_list = response.xpath('//div[contains(@id,"J_goodsList")]/ul/li')
        for li in li_list:
            sku_id = li.xpath('./@data-sku').extract_first()
            product['product_sku_id'] = sku_id
            product['product_detail_url'] = "https://item.jd.com/{}.html".format(sku_id)
            # 获取店铺信息，类别信息，版本，图片等
            request_url = "https://cdnware.m.jd.com/c1/skuDetail/apple/7.3.0/{}.json".format(sku_id)
            yield scrapy.Request(
                url=request_url,
                meta={"item": deepcopy(product)},
                callback=self.parse_skuid_content
            )
        # 构造下页请求
        base_url = "https://search.jd.com/s_new.php?keyword={}&s=30&page=1"
        page_count = re.compile(r'page_count:\"(.*?)\"', re.S).findall(html_str)
        page_count = int(page_count[0]) if page_count else None
        page_current = re.compile(r'page:"(.*?)",page_count', re.S).findall(html_str)
        page_current = int(page_current[0]) if page_current else None
        next_page = "page={}".format(page_current + 1)
        keyword = parse.quote(product['product_category']['s_cate'][0]["s_name"])
        url_ = "https://search.jd.com/s_new.php?keyword={}&s=30&page=1".format(keyword)
        next_url = url_.split('page=')[0] + next_page
        if page_current and page_count:
            while page_current <= page_count:
                yield scrapy.Request(
                    url=next_url,
                    meta={'item': product['product_category']},
                    callback=self.parse
                )

    def parse_skuid_content(self, response):
        product = response.meta['item']
        data = json.loads(response.text)
        if 'wareInfo' in data:
            product['product_name'] = data['wareInfo']['basicInfo']['name']
            # data['wareInfo']['basicInfo']['wareImage']
            product['product_img_url'] = jsonpath.jsonpath(data, '$..wareImage..big')
            product['product_book_info'] = data['wareInfo']['basicInfo']['bookInfo']
            color_size = jsonpath.jsonpath(data, "$..colorSize")
            product_options = dict()
            if color_size:
                for s_ in color_size[0]:
                    title = s_['title']
                    buttons = jsonpath.jsonpath(s_, '$..text')
                    product_options[title] = buttons
                product['product_options'] = product_options
            shop = jsonpath.jsonpath(data, '$..shop')
            if shop:
                shop = shop[0]
                shop_info = dict()
                if shop:
                    shop_info['shopId'] = shop['shopId']
                    shop_info['shopName'] = shop['name']
                    shop_info['shopScore'] = shop['score']
                else:
                    shop_info['shopName'] = "京东自营"
                product['product_shop'] = shop_info
            product['product_category_id'] = data['wareInfo']['basicInfo']['category'].replace(';', ',')
        # 获取促销信息
        ad_url = "https://cd.jd.com/promotion/v2?skuId={}&area=17_2980_23644_0&cat={}".format(product["product_sku_id"], product['product_category_id'])
        yield scrapy.Request(
            url=ad_url,
            meta={"item": product},
            callback=self.get_ad_info
        )

    def get_ad_info(self, response):
        product = response.meta['item']
        data = json.loads(response.text)
        product["product_ad"] = data["ads"][0]['ad']
        # 获取价格
        price_url = "https://p.3.cn/prices/mgets?&skuIds=J_{}".format(product['product_sku_id'])
        yield scrapy.Request(
            url=price_url,
            meta={'item': product},
            callback=self.get_price_info
        )

    def get_price_info(self, response):
        product = response.meta['item']
        data = response.json()
        price_info = dict()
        price_info['original_price'] = data[0]['m']
        price_info['current_price'] = data[0]['p']
        product['product_price'] = price_info
        # 获取评价
        comment_url = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds={}".format(product['product_sku_id'])
        yield scrapy.Request(
            url=comment_url,
            meta={'item': product},
            callback=self.get_comment_info
        )

    def get_comment_info(self, response):
        product = response.meta['item']
        data = response.json()["CommentsCount"][0]
        comments_info = dict()
        comments_info['customer_comment_first_url'] = "https://club.jd.com/comment/productPageComments.action?&productId={}&score=0&sortType=5&page=0&pageSize=10".format(product['product_sku_id'])
        comments_info['CommentCount'] = data['CommentCount']
        comments_info['DefaultGoodCount'] = data['DefaultGoodCount']
        comments_info['GoodCount'] = data['GoodCount']
        comments_info['GeneralCount'] = data['GeneralCount']
        comments_info['PoorCount'] = data['PoorCount']
        comments_info['GoodRate'] = data["GoodRate"]
        product['product_comments'] = comments_info
        yield product
        pprint(product)
