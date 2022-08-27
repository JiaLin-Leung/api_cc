from libs.utils import db, ajax


def get_template_info(request):
    # 公共方法  获取课前准备管理  选择框使用
    classify_info = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(del_state=0).select('id', 'name', 'num')
    data = [{"value": item.id, "name": item.name, "num": item.num} for item in classify_info]
    return ajax.ajax_ok(data=data)
