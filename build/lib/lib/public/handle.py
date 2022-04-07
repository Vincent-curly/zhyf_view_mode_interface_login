# coding:utf-8
"""
  Time : 2022/4/3 2:56
  Author : vincent
  FileName: handle
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2022/4/3 2:56
"""
import base64
import configparser
import datetime
import decimal
import hashlib
import json
import os
import time
from xml.dom import minidom

from PrescriptionPushSystem.settings import BASE_DIR


def get_config(section_name, options):
    """
    读取配置文件信息
    :param section_name:
    :param options:
    :return:
    """
    config_dir = BASE_DIR / 'resources'
    config_path = os.path.join(config_dir, "config.ini")
    config = configparser.ConfigParser()
    config.read(config_path)
    options_back = {}
    if isinstance(options, list):
        for option in options:
            if section_name == 'hospital':
                options_back[option] = config.get(section_name, option).encode('utf-8').decode('unicode_escape')
            else:
                options_back[option] = config.get(section_name, option)
        return options_back
    else:
        if section_name == 'hospital':
            return config.get(section_name, options).encode('utf-8').decode('unicode_escape')
        else:
            return config.get(section_name, options)


def string_to_list(s):
    """将前端提交过来的数组类型数据转换成 python 列表，使用的前提条件：前端进行 Ajax 时，对 Array 进行 JSON.stringify() 序列化"""
    new_s = s.replace('[', '').replace(']', '').replace('"', '').split(',')
    return new_s


def current_time(interval_day):
    day_time = int(time.mktime(datetime.date.today().timetuple()))
    interval_seconds = interval_day * 86400
    date = datetime.datetime.fromtimestamp(day_time - interval_seconds)
    return date


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, decimal.Decimal):
            return float('%.5f' % obj)
        # super(DecimalEncoder, self).default(o)
        else:
            return json.JSONEncoder.default(self, obj)


class Envelope:
    def __init__(self, env_string):
        dom = minidom.parseString(env_string)
        self.root = dom.documentElement

    def get_context(self, node_name):
        """获取某一结点的值"""
        node = self.root.getElementsByTagName(node_name)
        node_text_node = node[0].childNodes[0]
        return node_text_node.data


def response_base64_decode(request_data):
    """对 request 解密"""
    data_encode = request_data.encode('utf-8')
    response_data_decode = base64.b64decode(data_encode).decode()
    return response_data_decode


def request_base64_encode(response_data):
    """对出参加密"""
    data_encode = response_data.encode('utf-8')
    request_data_encode = base64.b64encode(data_encode).decode()
    return request_data_encode


def md5_creat_password(en_data):
    hl = hashlib.md5()  # 创建 MD5 对象
    hl.update(en_data.encode(encoding='utf-8'))
    return hl.hexdigest().upper()


if __name__ == '__main__':

    print(get_config('hospital', 'companyNum'))
    print(get_config('hospital', 'companyPass'))
    connect_strings = get_config('jdbc', 'mysqlConnectString')
    options = ['companyprovince', 'companycity', 'companyzone', 'companyaddress', 'companyname', 'companytel']
    hos_properties = get_config('hospital', options)
    print(hos_properties)
    print(connect_strings)
