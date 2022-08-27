from libs.utils import Struct, tbktapi, ajax, db


def get_user(request):
    """
    根据user_id, account_id 获取User对象
    :param self: request 对象
    :return:
    """
    user_id = request.user_id
    if not user_id:
        return
    sql = f"""
            SELECT id,username,real_name,userroles,userpswd,userphone,createDate,status
            from auth_user where id = {user_id} and status = 1; 
        """
    data = db.default.fetchone_dict(sql)
    if not data:
        return
    return User(data)


class User:
    """
    同步课堂资源用户用户类, 取代django的User模型
    用法:
    auth = User(profile接口数据)
    if auth: ...
    """
    def __init__(self, profile):
        """init User Object by profile"""
        self.base = profile or {}
        for k, v in self.base.items():
            setattr(self, k, v)

    def __len__(self):
        if hasattr(self, 'user_id'):
            return 1
        return 0


def need_login(func):
    """
    ajax强制登录修饰器
    """
    def wrap(request, *args, **kw):
        user = request.user_id
        if not user:
            return ajax.jsonp_fail(request, data='', error='no_user', message="请您先登录")
        else:
            return func(request, *args, **kw)
    return wrap
