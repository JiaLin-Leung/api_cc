import time

from rest_framework.views import APIView

from apps.course.serializers import ClassifySerializer, ClassifyListSerializer, CourseListSerializer, \
    CourseCreateSerializer, CourseUpdateSerializer
from libs.utils import trancate_date, db, ajax, Struct, num_to_ch, get_serializer_first_errors_msg


class ClassifyListView(APIView):
    # 课程分类列表视图

    def get(self, request):
        # 分类列表
        serializer = ClassifyListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        page_no = args.page_no or 1
        page_size = args.page_size or 10
        start, end = (page_no - 1) * page_size, page_no * page_size
        total = db.tbkt_ywscsf.sskt_classify.filter(del_state=0).count()
        if total == 0:
            return ajax.ajax_ok(data={"total": 0, "page": []})
        classify_info = db.tbkt_ywscsf.sskt_classify.filter(del_state=0).select('id', 'name', 'status', 'add_time').order_by('-id')[start: end]
        classify_ids = [str(x.id) for x in classify_info]
        # 获取级联  关联课程数量
        sql = f"""
        select classify_id, count(*) as num from tbkt_ywscsf.sskt_course where classify_id in ({','.join(classify_ids)})
        and del_state = 0 group by classify_id
        """
        relate_course_info = db.tbkt_ywscsf.fetchall_dict(sql)
        classify_id_to_course_num = {item.classify_id: item.num for item in relate_course_info}
        for item in classify_info:
            item.add_time = trancate_date(item.add_time, format="%Y-%m-%d %H:%M")
            item.course_num = classify_id_to_course_num.get(item.id, 0)
            item.id_num = str(item.id).zfill(3)
        return ajax.ajax_ok(data={"page": classify_info, "total": total})

    def post(self, request):
        # 添加分类
        serializer = ClassifySerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name = args.name
        status = args.status
        # 检查分类名称是否存在
        if db.tbkt_ywscsf.sskt_classify.filter(name=name, del_state=0).exists():
            return ajax.ajax_fail(message="分类名已存在，添加失败")
        db.tbkt_ywscsf.sskt_classify.create(name=name, status=status, add_time=int(time.time()))
        return ajax.ajax_ok(message="success")


class ClassifyDetailView(APIView):
    # 课程分类详情视图

    def get(self, request, pk):
        # 课程分类详情
        classify_info = db.tbkt_ywscsf.sskt_classify.filter(id=pk).first()
        if not classify_info:
            return ajax.ajax_fail(message='未找到对应的课程分类记录')
        data = {
            "id": pk,
            "name": classify_info.name,
            "status": classify_info.status
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, pk):
        # 课程分类修改
        classify_info = db.tbkt_ywscsf.sskt_classify.filter(id=pk).first()
        if not classify_info:
            return ajax.ajax_fail(message='未找到对应的课程分类记录')
        serializer = ClassifySerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name = args.name
        status = args.status
        # 检查分类名称是否重复
        if db.tbkt_ywscsf.sskt_classify.filter(name=name, id__ne=pk).exists():
            return ajax.ajax_fail(message="分类名已存在, 修改失败")
        # 修改记录
        db.tbkt_ywscsf.sskt_classify.filter(id=pk).update(name=name, status=status, update_time=int(time.time()))
        return ajax.ajax_ok(message="success")

    def delete(self, request, pk):
        # 课程分类删除
        classify_info = db.tbkt_ywscsf.sskt_classify.filter(id=pk).first()
        if not classify_info:
            return ajax.ajax_fail(message='未找到对应的课程分类记录')
        # 检查级联
        if db.tbkt_ywscsf.sskt_course.filter(classify_id=pk, del_state=0).exists():
            return ajax.ajax_fail(message="该分类下存在课程，无法删除！")
        db.tbkt_ywscsf.sskt_classify.filter(id=pk).update(del_state=1, update_time=int(time.time()))
        return ajax.ajax_ok(message='success')


class CourseListView(APIView):
    # 课程列表接口

    def get(self, request):
        serializer = CourseListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        page_no = args.page_no
        page_size = args.page_size
        start, end = (page_no - 1) * page_size, page_no * page_size
        filter_condition = {"del_state": 0}
        if args.name:
            filter_condition.update({"name__contains": args.name})
        total = db.tbkt_ywscsf.sskt_course.filter(**filter_condition).count()
        if total == 0:
            return ajax.ajax_ok(data={"total": 0, "page": []})
        course_info = db.tbkt_ywscsf.sskt_course.filter(**filter_condition).\
            select('id', 'name', 'classify_id', 'grade_level', 'status', 'add_time').order_by('-id')[start: end]
        course_ids = []
        classify_ids = []
        for item in course_info:
            course_ids.append(item.id)
            classify_ids.append(item.classify_id)
        course_id_str = ','.join([str(item) for item in course_ids])
        # 查课时数量
        sql = f"""
        select course_id, count(id) as num
        from tbkt_ywscsf.sskt_chapter 
        where del_state=0 and course_id in ({course_id_str}) 
        group by course_id
        """
        chapter_info = db.tbkt_ywscsf.fetchall_dict(sql)
        course_id_to_chapter_num = {item.id: item.num for item in chapter_info}
        # 查分类名称
        classify_info = db.tbkt_ywscsf.sskt_classify.filter(id__in=classify_ids).select('id', 'name')
        classify_id_to_name = {item.id: item.name for item in classify_info}
        for item in course_info:
            item.chapter_num = course_id_to_chapter_num.get(item.id, 0)
            item.classify_name = classify_id_to_name.get(item.classify_id, '')
            item.add_time = trancate_date(item.add_time, format="%Y-%m-%d %H:%M")
            item.grade_level_str = parse_grade_level(item.grade_level)
            item.id_num = str(item.id).zfill(3)
        return ajax.ajax_ok(data={"page": course_info, "total": total})

    def post(self, request):
        # 新增课程
        serializer = CourseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, slogan, classify_id, grade_level, status, index_url, banner_url = args.name, args.slogan, \
                                                                                args.classify_id, args.grade_level, \
                                                                                args.status, args.index_url, \
                                                                                args.banner_url
        # 处理grade_level
        grade_ids = list(set([int(item) for item in grade_level.split(',')]))
        grade_ids.sort()
        grade_level = ','.join(str(item) for item in grade_ids)
        db.tbkt_ywscsf.sskt_course.create(name=name,
                                          slogan=slogan,
                                          classify_id=classify_id,
                                          grade_level=grade_level,
                                          status=status,
                                          index_url=index_url,
                                          banner_url=banner_url,
                                          add_time=int(time.time())
                                          )
        return ajax.ajax_ok(message="success")


class CourseDetailView(APIView):

    def get(self, request, pk):
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=pk, del_state=0).first()
        print(course_info)
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        # TODO: 这里的index_url和banner_url是否需要加前缀
        data = {
            "id": course_info.id,
            "slogan": course_info.slogan,
            "classify_id": course_info.classify_id,
            "grade_level": course_info.grade_level,
            "status": course_info.status,
            "index_url": course_info.index_url,
            "banner_url": course_info.banner_url,
            "name": course_info.name,
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, pk):
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=pk, del_state=0).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        serializer = CourseUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, slogan, classify_id, grade_level, status, index_url, banner_url = args.name, args.slogan, \
                                                                                args.classify_id, args.grade_level, \
                                                                                args.status, args.index_url, \
                                                                                args.banner_url
        update_condition = {"update_time": int(time.time())}
        if name:
            # 校验课程名存在
            if db.tbkt_ywscsf.sskt_course.filter(name=name, del_state=0, id__ne=pk).exists():
                return ajax.ajax_fail(message="同名课程已存在, 修改失败")
            update_condition.update({"name": name})
        if slogan:
            update_condition.update({"slogan": slogan})
        if classify_id:
            update_condition.update({"classify_id": classify_id})
        if grade_level:
            # 处理grade_level
            grade_ids = list(set([int(item) for item in grade_level.split(',')]))
            grade_ids.sort()
            grade_level = ','.join(str(item) for item in grade_ids)
            update_condition.update({"grade_level": grade_level})
        if status:
            update_condition.update({"status": status})
        if index_url:
            update_condition.update({"index_url": index_url})
        if banner_url:
            update_condition.update({"banner_url": banner_url})
        db.tbkt_ywscsf.sskt_course.filter(id=pk).update(**update_condition)
        return ajax.ajax_ok(message="success")

    def delete(self, request, pk):
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=pk).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        db.tbkt_ywscsf.sskt_course.filter(id=pk).update(del_state=1, update_time=int(time.time()))
        return ajax.ajax_ok(message="success")


class CourseHighlightDetailView(APIView):
    # 课程亮点详情视图

    def get(self, request, course_id):
        # 获取课程亮点
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=course_id).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        highlight_info = db.tbkt_ywscsf.sskt_course_highlight.filter(course_id=course_id).select('id', 'title', 'content', 'sequence').order_by('sequence')

        highlight_info = db.tbkt_ywscsf.sskt_course_highlight.filter(course_id=course_id, del_state=0).select('id',
                                                                                                              'title',
                                                                                                              'content',
                                                                                                              'sequence').order_by(
            'sequence')[:]
        print(highlight_info)
        return ajax.ajax_ok(data=highlight_info)



    def put(self, request, course_id):
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=course_id).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        highlight_info = request.data.get('highlight_info', [])
        if not highlight_info:
            return ajax.ajax_fail(message="Invalid param highlight_info, except list")
        for item in highlight_info:
            if not 0 < len(item['title']) <= 10:
                return ajax.ajax_fail(message="亮点标题长度超限")
            if not 0 < len(item['content']) <= 40:
                return ajax.ajax_fail(message="亮点内容长度超限")
        current_highlight_ids = []
        bulk_data = []
        nowt = int(time.time())
        for item in highlight_info:
            if 0 == item['id']:
                # 创建课程亮点
                bulk_data.append({
                    "course_id": course_id,
                    "title": item['title'],
                    "content": item['content'],
                    "del_state": 0,
                    "sequence": item['sequence'],
                    "add_time": nowt,
                    "update_time": nowt,
                })
            else:
                current_highlight_ids.append(item['id'])
                # 更新课程亮点
                db.tbkt_ywscsf.sskt_course_highlight.filter(id=item['id']).update(
                    title=item['title'],
                    content=item['content'],
                    sequence=item['sequence'],
                    del_state=0,
                    update_time=nowt
                )
        # 清理多余的课程亮点
        db.tbkt_ywscsf.sskt_course_highlight.filter(course_id=course_id, id__ni=current_highlight_ids).update(del_state=1, update_time=nowt)
        # 新增的课程亮点入库
        db.tbkt_ywscsf.sskt_course_highlight.bulk_create(bulk_data)
        return ajax.ajax_ok(message="success")


class CourseTeacherDetailView(APIView):
    # 课程教研团队详情视图

    def get(self, request, course_id):
        # 获取课程教研团队
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=course_id).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        teacher_info = db.tbkt_ywscsf.sskt_course_teacher.filter(course_id=course_id, del_state=0).\
            select('id', 'name', 'intro', 'portrait', 'sequence').order_by('sequence')[:]
        # TODO: 头像链接是否加前缀
        return ajax.ajax_ok(data=teacher_info)

    def put(self, request, course_id):
        course_info = db.tbkt_ywscsf.sskt_course.filter(id=course_id).first()
        if not course_info:
            return ajax.ajax_fail(message='未找到对应的课程记录')
        teacher_info = request.data.get('teacher_info', [])
        if not teacher_info:
            return ajax.ajax_fail(message="Invalid param teacher_info, except list")
        for index, item in enumerate(teacher_info, start=1):
            if not 0 < len(item['name']) <= 5:
                return ajax.ajax_fail(message="教师姓名最多5个字")
            if not 0 < len(item['intro']) <= 40:
                return ajax.ajax_fail(message="教师介绍最多40个字")
            if not 0 < len(item['portrait']) <= 100:
                return ajax.ajax_fail(message="教师头像地址过长")
            item['sequence'] = index
        current_teacher_ids = []
        bulk_data = []
        nowt = int(time.time())
        for item in teacher_info:
            if 0 == item['id']:
                # 创建课程教师
                bulk_data.append({
                    "course_id": course_id,
                    "name": item['name'],
                    "intro": item['intro'],
                    "portrait": item['portrait'],
                    "del_state": 0,
                    "sequence": item['sequence'],
                    "add_time": nowt,
                    "update_time": nowt,
                })
            else:
                current_teacher_ids.append(item['id'])
                # 更新课程教师
                db.tbkt_ywscsf.sskt_course_teacher.filter(id=item['id']).update(
                    name=item['name'],
                    intro=item['intro'],
                    portrait=item['portrait'],
                    sequence=item['sequence'],
                    del_state=0,
                    update_time=nowt
                )
        # 清理多余的课程亮点
        db.tbkt_ywscsf.sskt_course_teacher.filter(course_id=course_id, id__ni=current_teacher_ids).update(del_state=1, update_time=nowt)
        # 新增的课程亮点入库
        db.tbkt_ywscsf.sskt_course_teacher.bulk_create(bulk_data)
        return ajax.ajax_ok(message="success")


def parse_grade_level(grade_level):
    # 将1,2,3,4,5,6形式的适用年级数据 解析为  一至六年级
    grade_ids = grade_level.split(',')
    grade_ids = [int(item) for item in grade_ids]
    grade_level_list = []
    tmp_str = ""
    for i in range(0, len(grade_ids)):
        if i == len(grade_ids) - 1:
            tmp_str += f"{num_to_ch(grade_ids[i])}年级"
            grade_level_list.append(tmp_str)
            tmp_str = ""
        elif grade_ids[i+1] - grade_ids[i] == 1:
            if "" == tmp_str:
                tmp_str = f"{num_to_ch(grade_ids[i])}至"
        else:
            tmp_str += f"{num_to_ch(grade_ids[i])}年级"
            grade_level_list.append(tmp_str)
            tmp_str = ""
    return '、'.join(grade_level_list)
