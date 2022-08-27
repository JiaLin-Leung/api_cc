import json
import time

import datetime

from libs.utils import Struct


def argument(self, **kw):
    args = Struct()
    error = None
    for k, typ in kw.items():
        if not isinstance(typ, Schema):
            raise TypeError()
        v = self.get(k)
        try:
            typ.key = k
            args[k] = typ.validate(v)
        except Exception as e:
            error = str(e)
    return args, error


class Schema(object):
    """
    使用方法
    >>> def data_validate(request):
    >>>     args, e = request.QUERY.argument(
    >>>            name=Schema(type=str, required=True, error="姓名不能为空"),
    >>>            age=Schema(type=int, required=True, filter=lambda x: x > 0, error="年龄信息错误"),
    >>>            image=Schema(type=[str], default=""),
    >>>            data=Schema(type=[{"qid": int, "aid": [str]}])
    >>>    )
    """
    def __init__(self, type, required=False, default=None, filter=None, error=None, key=None):
        self.type = type
        self.default = default
        self.required = required
        self.filter = filter
        self.error = error
        self.key = key

    def _iterable_parse(self, val, typ=None):
        """可迭代格式验证"""
        e = self.error
        try:
            val = json.loads(val) if isinstance(val, str) else val
            if not isinstance(val, (list, tuple, set, frozenset)):
                raise TypeError("%s 不是数组格式" % self.key)
        except:
            raise TypeError("%s 格式转换错误" % self.key
                            if not e else e)
        self._required(val)
        data = []
        _typ = self.type if not typ else typ
        for i in _typ:
            for v in val:
                v = self._validate_method(v, i)
                data.append(v)
        return data or val

    def _type_parse(self, val, typ=None):
        """可转换格式验证"""
        e = self.error
        _typ = self.type if not typ else typ
        try:
            val = _typ(val)
        except:
            raise TypeError("%s类型错误" % self.key
                            if not e else e)
        return val

    def _dict_parse(self, val, typ=None):
        """dict格式验证"""
        e = self.error
        try:
            val = json.loads(val) if isinstance(val, str) else val
            if not isinstance(val, dict):
                raise TypeError("%s 不是json格式" % self.key)
        except:
            raise TypeError("%s 格式转换错误" % self.key
                            if not e else e)
        self._required(val)
        _typ = self.type if not typ else typ
        keys = _typ.keys()
        data = Struct()
        for i in keys:
            if i not in val.keys():
                raise TypeError("%s中缺少key: %s" % (self.key, i)
                                if not e else e)
        for k, v in val.items():
            t = _typ.get(k)
            if not t:
                data[k] = v
                continue
            data[k] = self._validate_method(v, t)
        return data or Struct(val)

    def _callable(self, data):
        """可调用方式验证"""
        e = self.error
        if not callable(self.filter):
            raise TypeError("%s 过滤器不支持调用" % self.key)
        if self.filter(data):
            return data
        raise TypeError("参数%s:不合法" % self.key
                        if not e else e)

    def _datetime(self, date, _):
        try:
            if date.endswith('24:00:00'):
                v = date.split()[0] + ' 23:59:59'
                v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                v = time.localtime(time.mktime(v) + 1)
                v = datetime.datetime(*v[:6])
            else:
                t = time.strptime(date, "%Y-%m-%d %H:%M:%S")
                v = datetime.datetime(*t[:6])
        except:
            raise TypeError("%s 时间转换错误" % self.key)
        return v

    def _timestamp(self, date, _):
        if not date:
            return 0
        try:
            if date.endswith('24:00:00'):
                v = date.split()[0] + ' 23:59:59'
                v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                v = int(time.mktime(v) + 1)
            else:
                t = time.strptime(date, "%Y-%m-%d %H:%M:%S")
                v = int(time.mktime(t))
        except:
            import traceback
            traceback.print_exc()
            raise TypeError("%s 时间戳转换错误" % self.key)
        return v

    def _validate_method(self, val, typ):
        med = {
            TYPE: self._type_parse,
            ITERABLE: self._iterable_parse,
            DICT: self._dict_parse,
            DATETIME: self._datetime,
            TIMESTAMP: self._timestamp,
        }.get(_priority(typ))
        return med(val, typ)

    def _required(self, val):
        if not val:
            if not self.required:
                return self.default if self.default else type_default_value(self.type)
            else:
                raise TypeError("%s 不能为空" % self.key)

    def validate(self, val):
        if val is None:
            if not self.required:
                return self.default if self.default else type_default_value(self.type)
            else:
                raise TypeError("%s 不能为空" % self.key if not self.error else self.error)
        data = self._validate_method(val, self.type)
        if self.filter:
            data = self._callable(data)
        return data


def _callable_str(callable_):
    if hasattr(callable_, '__name__'):
        return callable_.__name__
    return str(callable_)

RE, DATETIME, TIMESTAMP, CALLABLE, TYPE, DICT, ITERABLE = range(7)


def _priority(s):
    """Return priority for a given object."""
    if type(s) in (list, tuple, set, frozenset):
        return ITERABLE
    if type(s) is dict:
        return DICT
    if issubclass(type(s), type):
        return TYPE
    if callable(s):
        return CALLABLE
    if isinstance(s, str):
        if s == "datetime":
            return DATETIME
        if s == "timestamp":
            return TIMESTAMP
        return RE


def type_default_value(t):
    """返回基本类型默认值, 没有识别的类型返回None"""
    if type(t) in (list, tuple, set, frozenset):
        return []
    if type(t) is dict:
        return {}
    return {str: "", int: 0}.get(t)

