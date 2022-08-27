# coding: utf-8

import base64
import time
from django.conf import settings


def encode_key():
    """
    功能说明: 生成api间认证密匙
    -------------------------------
    修改人       修改时间
    --------------------------------
    高海飞        2018.6.11
    :return: key
    """
    key = '%s%s' % (settings.PROJECT_KEY, str(int(time.time())))  # 拼接加密key 项目名称+当前时间戳
    return base64.b64encode(str.encode(key))


def decode_key(key_token):
    """
    功能说明： 解密api间认证密匙
    ----------------------------------
    修改人     修改时间
    ----------------------------------
    高海飞     2018.6.11
    :param key_token: key
    :return: true 认证通过 false 认证失败
    """
    str_key_token = base64.b64decode(key_token).decode()  # 解密密匙
    ts = int(str_key_token[-10:])       # 取出时间戳
    object_name = str_key_token[:-10]   # 取出项目名称
    current_t = int(time.time())
    # 所有业务项目名称
    project_names = ['user_api_dj', 'base_sys_api_dj', 'task_sys_api_dj', 'tournament_sys_api_dj']
    if object_name not in project_names:
        return False
    # 判断时间戳60s内的请求有效
    if current_t - ts <= 60:
        return True
    return False
