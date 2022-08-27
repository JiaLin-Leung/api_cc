from libs.utils import db, ajax


def get_classify_info(request):
    # 公共方法  获取分类  选择框使用
    classify_info = db.tbkt_ywscsf.sskt_classify.filter(del_state=0).select('id', 'name')
    data = [{'value':item.id,"lable":item.name} for item in classify_info]
    return ajax.ajax_ok(data=data)

