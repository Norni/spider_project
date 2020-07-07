import requests
from pprint import pprint

url = 'https://api.m.jd.com/client.action?functionId=wareBusiness&clientVersion=8.5.10&build=72823&client=android&d_brand=Xiaomi&d_model=MI9&osVersion=5.1.1&screen=1920*1080&partner=BS2020042200004&aid=a44bfb04345954f7&oaid=&eid=eidAb9cf812159sdW80MdwlTTkiGfs2T6BDFtlvNDeoEINW8iaOEqMgCyGbNY51cW3B6Mk5PF6WCJjLg5336i/fqDi57tEYoVFjP1dZ6nm18YFisqdxn&sdkVersion=22&lang=zh_CN&uuid=355757541854721-5C5F67252FF6&area=22_2070_2079_28437&networkType=wifi&wifiBssid=b8d04aa492461a9fd3832ac557e3fb86&st=1594127491154&sign=04de3c1c507212b401e58960f6159be1&sv=102'

data = {
    "body": {"abTest800": True, "brand": "Xiaomi", "eventId": "Searchlist_Productid", "fromType": 0, "isDesCbc": True,
             "latitude": "30.998676", "lego": True, "longitude": "102.565007", "model": "MI 9", "pluginVersion": 85100,
             "plusClickCount": 0, "provinceId": "22", "skuId": "57251126212", "uAddrId": "0"}
}

headers = {
    "User-Agent": "okhttp/3.12.1"
}

response = requests.post(url=url, headers=headers, data=data)

pprint(response.text)
