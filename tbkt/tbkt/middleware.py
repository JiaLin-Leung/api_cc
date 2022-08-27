# coding: utf-8
import time
import logging
import traceback
import threading
import os
from django.http.request import QueryDict
from django.http import HttpRequest, HttpResponse, Http404

from com.com_user import get_user
from libs.utils import ajax, auth_token, casts, loads
from libs.utils.exceptions import CustomError
from libs.utils.validate import argument
log = logging.getLogger(__name__)
# 给request.GET, request.POST, request.QUERY注入新方法
QueryDict.casts = casts
QueryDict.argument = argument
HttpRequest.loads = loads
local = threading.local()

write_list = ["/apidoc/", "/login/"]


class SlsFilter(logging.Filter):
    """
    日志过滤器，将当前请求线程的request信息保存到日志的record上下文
    record带有formater需要的信息。
    """
    def filter(self, record):
        try:
            record.user_id = getattr(local, 'user_id', None)
            record.req_path = getattr(local, 'req_path', None)
            record.req_client_ip = getattr(local, 'req_client_ip', None)
            record.req_referer = getattr(local, 'req_referer', None)
            record.host_ip = getattr(local, 'host_ip', None)
            record.host_name = getattr(local, 'host_name', None)
            record.host_env = getattr(local, 'host_env', None)
        except:
            pass
        return True



def get_token(request):
    """
    获取token
    """
    token = request.GET.get("tbkt_token") \
        or request.META.get('HTTP_TBKT_TOKEN') \
        or request.COOKIES.get('tbkt_token')
    # 暂时写死
    token = 'OX0wNzcwMzUyNDQzfTA3NzA1MDk4MzA'
    return token


def get_user_id(self):
    """
    从cookie中获取user_id, 失败返回None
    """
    token = get_token(self)
    r = auth_token.decode_token(token)
    user_id = r['user_id'] if r else None
    self._expire = expire = r['expire'] if r else None
    # 过期从新登陆
    if expire and time.time() >= expire:
        return 0
    return user_id


def get_user_info(self):
    """
    远程调用获取user, 失败返回None
    """
    if not hasattr(self, '_user'):
        user_id = get_user_id(self)
        self._user = get_user(self) if user_id else None
    return self._user


# 添加user_id属性,保存角色ID信息
HttpRequest.user_id = property(get_user_id)
# 添加User属性,保存用户信息
HttpRequest.user_info = property(get_user_info)


class AuthenticationMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response
        super(AuthenticationMiddleware,self).__init__()

    def __call__(self, request):
        response = None
        if hasattr(self, "process_request"):
            response = self.process_request(request)
        if not response:
            response = self.get_response(request)
        if hasattr(self, "process_response"):
            response = self.process_response(request, response)
        return response

    def _infologuser(self, request):
        try:
            local.user_id = request.user_id if request.user_id else 0
            local.req_path = request.path

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
            if x_forwarded_for:
                remote_ip = x_forwarded_for.split(",")[0]
            else:
                remote_ip = request.META.get('REMOTE_ADDR', '')
            local.req_client_ip = remote_ip
            local.host_ip = os.getenv("__HOST_IP", '')
            local.host_name = os.getenv("__HOST_NAME", '')
            local.host_env = os.getenv("__HOST_ENV", '')
            local.req_referer = request.environ.get('HTTP_REFERER', '')
            # log.error(f"req_referer={local.req_referer}")
        except Exception as e:
            log.error(e)

    @staticmethod
    def process_exception(request, exception):
        """
        功能说明:view函数抛出异常处理
        -------------------------------
        修改人     修改时间
        --------------------------------
        徐威      2013-07-17
        """
        if isinstance(exception, Http404):
            return ajax.jsonp_fail(request, error="404", message="not found!")
        if isinstance(exception, CustomError):
            return ajax.jsonp_fail(request, error=exception.code, message=exception.message)
        exc = traceback.format_exc()
        log.error(exc)
        r = ajax.jsonp_fail(request, error="500", message="服务器开小差,请稍后重试")
        r.status_code = 500
        return r

    def process_request(self, request):
        self._infologuser(request)

        # 白名单过滤
        path = request.path
        for i in write_list:
            if i in path:
                return
        if not request.user_id:
            return ajax.jsonp_fail(request, message='no_user', error='no_user')
        # 更新token
        if getattr(request, '_newtoken', None):
            auth_token.login_response(request, request._newtoken)

    def process_response(self, request, response):
        origin = request.META.get('HTTP_ORIGIN', '*')
        if request.method == 'OPTIONS' and not response:
            response = HttpResponse()
        if not response:
            return
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,OPTIONS,PATCH,PUT'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,Tbkt-Token,App-Type'
        response['Access-Control-Max-Age'] = '1728000'
        response["Allow"] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response



