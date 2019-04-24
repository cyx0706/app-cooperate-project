# -*- coding:utf-8 -*-
import requests

sms_host = "https://sms.yunpian.com/v2/sms/single_send.json"

headers = {
    'Accept':'application/json;charset=utf-8',
    'Content-Type':'application/x-www-form-urlencoded;charset=utf-8',
}

params = {
    'apikey': 'cdaed4db7eae3807a22dc407c1dfdd19',
    'text': None,
    'mobile': None,
}

def send_msg(url, text, mobile):

    temp = requests.post(url, data={'apikey': 'cdaed4db7eae3807a22dc407c1dfdd19',
                        'text': text,
                        'mobile': str(mobile)})
    print(temp.text)

send_msg(sms_host, "测试", 17863955937)