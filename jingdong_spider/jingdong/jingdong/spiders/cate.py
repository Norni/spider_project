import scrapy
import json
from jingdong.items import CategoryItem


class CateSpider(scrapy.Spider):
    name = 'cate'
    allowed_domains = ['dc.3.cn']
    start_urls = ['https://dc.3.cn/category/get']

    def get_name_and_url(self, cate_info, cate_name, cate_url):
        cate = list()
        if isinstance(cate_info, list):
            for _ in cate_info:
                item = dict()
                item[cate_name] = _.split(r'|')[1]
                url = _.split(r'|')[0]
                if 'jd.com' in url:
                    item[cate_url] = "https://" + url
                elif url.count("-") == 1:
                    item[cate_url] = 'https://channel.jd.com/{}.html'.format(url)
                elif url.count("-") == 2:
                    item[cate_url] = 'https://list.jd.com/list.html?cat={}'.format(url.replace('-', ','))
                cate.append(item)
            return cate
        if isinstance(cate_info, str):
            item = dict()
            item[cate_name] = cate_info.split(r'|')[1]
            url = cate_info.split(r'|')[0]
            if 'jd.com' in url:
                item[cate_url] = "https://" + url
            elif url.count("-") == 1:
                item[cate_url] = 'https://channel.jd.com/{}.html'.format(url)
            elif url.count("-") == 2:
                item[cate_url] = 'https://list.jd.com/list.html?cat={}'.format(url.replace('-', ','))
            cate.append(item)
            return cate

    def get_info_from_s(self, data):
        n_cate_list = list()
        s_cate_list = list()
        if isinstance(data, list):
            for _ in data:
                # 获取单个条目下的数据
                name = _['n']
                info = _["s"]
                if name:
                    n_cate_list.append(name)
                if info:
                    s_cate_list.append(info)
            return n_cate_list, s_cate_list
        if isinstance(data, dict):
            name = data['n']
            info = data["s"]
            if name:
                n_cate_list.append(name)
            if info:
                s_cate_list.append(info)
            return n_cate_list, s_cate_list

    def parse(self, response):
        result = json.loads(response.body.decode("GBK"))
        data_list = result.get('data')
        for data in data_list:
            # 获取单个大分类
            category_info = CategoryItem()
            # 获取包含分类的数据
            s_data = data['s']
            b_n_cate_list, b_s_cate_list = self.get_info_from_s(s_data)
            category_info["b_cate"] = self.get_name_and_url(b_n_cate_list, "b_name", "b_url")  # 获取到大分类信息
            for m_ in b_s_cate_list:
                for m__ in m_:
                    m_n_cate_str = m__["n"]
                    category_info["m_cate"] = self.get_name_and_url(m_n_cate_str, "m_name", "m_url")  # 获取到中分类信息
                    m_s_cate_list = m__['s']
                    for s_ in m_s_cate_list:
                        s_n_cate_str = s_['n']
                        category_info["s_cate"] = self.get_name_and_url(s_n_cate_str, 's_name', 's_url')
                        yield category_info
