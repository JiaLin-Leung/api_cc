import json
import time

from rest_framework.views import APIView

from apps.chapter.serializers import ChapterCreateSerializer, ChapterUpdateSerializer, VideoSectionCreateSerializer, \
    VideoSectionUpdateSerializer, ChapterTeachingPlanSerializer, ChapterLearningPlanSerializer, \
    LearningPrepareTemplateUpdateSerializer, LearningPrepareTemplateListSerializer, \
    LearningPrepareTemplateCreateSerializer
from libs.utils import db, ajax, Struct, get_serializer_first_errors_msg


class ChapterListView(APIView):

    def get(self, request):
        # 获取课程课时列表
        course_id = request.query_params.get('course_id', 0)
        if not course_id:
            return ajax.ajax_fail(message="course_id参数错误")
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(course_id=course_id, del_state=0).select('id', 'name', 'status', 'sequence').order_by('sequence')[:]
        if not chapter_info:
            return ajax.ajax_ok(data=[])
        return ajax.ajax_ok(data=chapter_info)

    def post(self, request):
        # 添加课时
        serializer = ChapterCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        course_id, name, status = args.course_id, args.name, args.status
        # 找当前最大的sequence
        last_chapter = db.tbkt_ywscsf.sskt_chapter.filter(course_id=course_id, del_state=0).order_by("-sequence").first()
        sequence = last_chapter.sequence + 1 if last_chapter else 1
        nowt = int(time.time())
        chapter_id = db.tbkt_ywscsf.sskt_chapter.create(name=name, course_id=course_id, status=status, sequence=sequence, add_time=nowt)
        # 将课时视频、教案、学案一并创建出来
        db.tbkt_ywscsf.sskt_chapter_video.create(chapter_id=chapter_id, add_time=nowt)
        db.tbkt_ywscsf.sskt_chapter_teaching_plan.create(chapter_id=chapter_id, add_time=nowt)
        db.tbkt_ywscsf.sskt_chapter_learning_plan.create(chapter_id=chapter_id, learning_preparation=json.dumps([]),
                                                         add_time=nowt)
        return ajax.ajax_ok(message="success")


class ChapterDetailView(APIView):

    def get(self, request, pk):
        # 课时详情
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=pk).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        data = {
            "id": chapter_info.id,
            "name": chapter_info.name,
            "status": chapter_info.status,
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, pk):
        # 课时修改
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=pk).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        serializer = ChapterUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, status = args.name, args.status
        nowt = int(time.time())
        update_condition = {"update_time": nowt}
        if name:
            # TODO: 课时名称是否可以重复
            update_condition.update({"name": name})
        if status:
            update_condition.update({"status": status})
        db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(**update_condition)
        return ajax.ajax_ok(message="success")

    def delete(self, reuqest, pk):
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=pk).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(del_state=1, update_time=int(time.time()))
        # 后面的章节sequence-1
        sql = f"""
            update tbkt_ywscsf.sskt_chapter set sequence = sequence - 1 
            where course_id={chapter_info.course_id} and status in (1, 2) and sequence > {chapter_info.sequence}
        """
        db.tbkt_ywscsf.execute(sql)
        return ajax.ajax_ok(message="success")


class ChapterOperateView(APIView):

    def put(self, request, pk, action):
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=pk).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        nowt = int(time.time())
        if action == "disable":
            # 禁用
            db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(status=2, update_time=nowt)
            return ajax.ajax_ok(message='success')
        elif action == "enable":
            # 启用
            db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(status=1, update_time=nowt)
            return ajax.ajax_ok(message='success')
        elif action == "up":
            # 上移
            if chapter_info.sequence == 1:
                return ajax.ajax_fail(message="当前课时不支持上移操作")
            if not db.tbkt_ywscsf.sskt_chapter.filter(course_id=chapter_info.course_id, status__in=(1, 2),
                                               sequence=chapter_info.sequence-1).exists():
                return ajax.ajax_fail(message="当前课时无法完成上移操作")
            db.tbkt_ywscsf.sskt_chapter.filter(course_id=chapter_info.course_id, status__in=(1, 2),
                                               sequence=chapter_info.sequence-1).update(
                sequence=chapter_info.sequence)
            db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(sequence=chapter_info.sequence-1)
            return ajax.ajax_ok(message='success')
        elif action == 'down':
            # 下移
            last_chapter = db.tbkt_ywscsf.sskt_chapter.filter(course_id=chapter_info.course_id, status__in=(1, 2)).order_by('-sequence').first()
            if last_chapter.sequence == chapter_info.sequence:
                return ajax.ajax_fail(message="当前课时不支持下移操作")
            if not db.tbkt_ywscsf.sskt_chapter.filter(course_id=chapter_info.course_id, status__in=(1, 2),
                                               sequence=chapter_info.sequence + 1).exists():
                return ajax.ajax_fail(message="当前课时无法完成上移操作")
            db.tbkt_ywscsf.sskt_chapter.filter(course_id=chapter_info.course_id, status__in=(1, 2),
                                               sequence=chapter_info.sequence + 1).update(
                sequence=chapter_info.sequence)
            db.tbkt_ywscsf.sskt_chapter.filter(id=pk).update(sequence=chapter_info.sequence + 1)
            return ajax.ajax_ok(message='success')
        else:
            return ajax.ajax_fail(message="非法的action操作")


class ChapterVideoDetailView(APIView):

    def get(self, request, chapter_id):
        # 获取课时  视频信息
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=chapter_id).first()
        if not chapter_info:
            return ajax.ajax_fail(message="未找到对应章节视频信息")
        video_info = db.tbkt_ywscsf.sskt_chapter_video.filter(chapter_id=chapter_id, del_state=0).first()
        video_section_info = db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_info.id, del_state=0).select(
            'id', 'name', 'type', 'url', 'duration', 'sequence').order_by('sequence')[:]
        data = {
            "chapter_id": chapter_info.id,
            "chapter_sequence": chapter_info.sequence,
            "chapter_name": chapter_info.name,
            "video_id": video_info.id,
            "video_img": video_info.video_img,
            "total_duration": video_info.total_duration,
            "pic_num": video_info.pic_num,
            "video_num": video_info.pic_num,
            "video_section_list": video_section_info
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, chapter_id):
        """
        请求参数：
        type: json
        传当前页面所有数据
        {
            "video_img": "test/123.jpg",
            "video_section_info": [
                {
                    "id": 123,          # 修改的传id
                    "name": "名称",
                    "type": 1,          # 1视频  2图片
                    "url": "test/123.mp4",
                    "duration":  180,   # 单位：秒
                    "sequence": 1,      # 顺序
                },
                {
                    "id": 0,          # 新增的id传0
                    "name": "名称",
                    "type": 2,
                    "url": "test/123.jpg",
                    "duration":  180,
                    "sequence": 2,
                }
            ]
        }
        """
        # 获取chapter_video
        video_info = db.tbkt_ywscsf.sskt_chapter_video.filter(chapter_id=chapter_id, del_state=0).first()
        if not video_info:
            return ajax.ajax_fail(message="未找到章节视频主记录")
        video_img = request.data.get('video_img', '')
        video_section_info = request.data.get('section_info', [])
        if not 0 < len(video_img) <= 100:
            return ajax.ajax_fail(message="video_img长度超限")
        ret, msg = validate_video_section_info(video_section_info)
        if not ret:
            return ajax.ajax_fail(message=msg)
        video_section_info = [Struct(item) for item in video_section_info]
        nowt = int(time.time())
        # 先更新视频小节，再更新视频主记录
        # 查当前启用视频小节
        current_video_section_info = db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_info.id, del_state=0)
        current_video_section_ids = [item.id for item in current_video_section_info]
        update_video_section_ids = []
        bulk_data = []
        total_duration, pic_num, video_num = 0, 0, 0
        for item in video_section_info:
            total_duration += item.duration
            if item.type == 1:
                video_num += 1
            else:
                pic_num += 1
            if item.id == 0:
                # 新增的视频小节
                bulk_data.append({
                    "video_id": video_info.id,
                    "name": item.name,
                    "type": item.type,
                    "url": item.url,
                    "duration": item.duration,
                    "sequence": item.sequence,
                    "add_time": nowt,
                    "update_time": nowt,
                })
            else:
                # 修改的视频小节
                update_video_section_ids.append(item.id)
                db.tbkt_ywscsf.sskt_video_section.filter(id=item.id).update(name=item.name,
                                                                            type=item.type,
                                                                            url=item.url,
                                                                            duration=item.duration,
                                                                            sequence=item.sequence,
                                                                            update_time=nowt)
        # 需要删除的视频小节
        need_del_video_section_ids = set(current_video_section_ids) - set(update_video_section_ids)
        db.tbkt_ywscsf.sskt_video_section.filter(id__in=need_del_video_section_ids).update(del_state=1, update_time=nowt)
        # 创建新增的视频小节
        db.tbkt_ywscsf.sskt_video_section.bulk_create(bulk_data)

        # 更新视频主记录d
        db.tbkt_ywscsf.sskt_chapter_video.filter(chapter_id=chapter_id, del_state=0).\
            update(video_img=video_img, total_duration=total_duration, pic_num=pic_num, video_num=video_num,
                   update_time=nowt)
        return ajax.ajax_ok(message='success')


class VideoSectionCreateView(APIView):

    def post(self, request, video_id):
        # 添加视频小节  video_id是sskt_chapter_video  主记录表id
        serializer = VideoSectionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, type_, url, duration = args.name, args.type_, args.url, args.duration
        nowt = int(time.time())
        # 获取最大的sequence
        last_video_section = db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_id, del_state=1).order_by('-sequence').first()
        sequence = last_video_section.sequence + 1 if last_video_section else 1
        video_section_id = db.tbkt_ywscsf.sskt_video_section.create(video_id=video_id, name=name, type=type_, url=url,
                                                                    duration=duration, del_status=0, sequence=sequence,
                                                                    add_time=nowt)
        data = {
            "id": video_section_id,
            "name": name,
            "type": type_,
            "url": url,
            "sequence": sequence
        }
        return ajax.ajax_ok(data=data)


class VideoSectionUpdateView(APIView):

    def put(self, request, video_section_id):
        if not db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).exists():
            return ajax.ajax_fail(message="未找到该视频小节")
        serializer = VideoSectionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, type_, url, duration = args.name, args.type_, args.url, args.duration
        nowt = int(time.time())
        update_condition = {"update_time": nowt}
        if name:
            update_condition.update({"name": name})
        if type_:
            update_condition.update({"type": type_})
        if url:
            update_condition.update({"url": url})
        if duration:
            update_condition.update({"duration": duration})
        db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).update(**update_condition)
        return ajax.ajax_ok(message='success')


class VideoSectionOperateView(APIView):

    def put(self, request, video_section_id, action):
        video_section_info = db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).first()
        if not video_section_info:
            return ajax.ajax_fail(message="未找到该视频小节")
        nowt = int(time.time())
        if action == 'up':
            # 上移
            if video_section_info.sequence == 1:
                return ajax.ajax_fail(message="当前小节不支持上移操作")
            if db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_section_info.video_id, del_state=0,
                                                        sequence=video_section_info.sequence-1).exists():
                return ajax.ajax_fail(message="当前小节无法执行上移操作")
            db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_section_info.video_id, del_state=0,
                                                     sequence=video_section_info.sequence-1).\
                update(sequence=video_section_info.sequence, update_time=nowt)
            db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).update(sequence=video_section_info.sequence-1,
                                                                                 update_time=nowt)
            return ajax.ajax_ok(message="success")
        elif action == 'down':
            last_video_section = db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_section_info.video_id,
                                                                          del_state=0).order_by('-sequence').first()
            if last_video_section.sequence == video_section_info.sequence:
                return ajax.ajax_fail(message="当前课时不支持下移操作")
            if not db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_section_info.video_id, del_state=0,
                                                      sequence=video_section_info.sequence + 1).exists():
                return ajax.ajax_fail(message="当前课时无法完成上移操作")
            db.tbkt_ywscsf.sskt_video_section.filter(video_id=video_section_info.video_id, del_state=0,
                                               sequence=video_section_info.sequence + 1).update(
                sequence=video_section_info.sequence)
            db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).update(sequence=video_section_info.sequence+1)
            return ajax.ajax_ok(message='success')
        elif action == 'delete':
            # 删除video_section  调整顺序
            db.tbkt_ywscsf.sskt_video_section.filter(id=video_section_id).update(del_state=1, update_time=nowt)
            sql = f"""
            update tbkt_ywscsf.sskt_video_section set sequence = sequence - 1 
            where video_id = {video_section_info.video_id} and status in (1, 2) 
            and sequence > {video_section_info.sequence}
            """
            db.tbkt_ywscsf.execute(sql)
            return ajax.ajax_ok(message='success')


class ChapterTeachingPlan(APIView):

    def get(self, request, chapter_id):
        # 获取章节教案
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=chapter_id).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        # 获取教案
        teaching_plan_info = db.tbkt_ywscsf.sskt_chapter_teaching_plan.filter(chapter_id=chapter_id).first()
        data = {
            "chapter_id": chapter_id,
            "chapter_name": chapter_info.name,
            "teaching_goals": teaching_plan_info.teaching_goals if teaching_plan_info.teaching_goals else "",
            "teaching_preparation": teaching_plan_info.teaching_preparation if teaching_plan_info.teaching_preparation else "",
            "teaching_reminder": teaching_plan_info.teaching_reminder if teaching_plan_info.teaching_reminder else "",
            "teaching_process": teaching_plan_info.teaching_process if teaching_plan_info.teaching_process else "",
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, chapter_id):
        # 修改章节教案
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=chapter_id).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        serializer = ChapterTeachingPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        teaching_goals, teaching_preparation, teaching_reminder, teaching_process = args.teaching_goals, args.teaching_preparation, args.teaching_reminder, args.teaching_process
        update_condition = {"update_time": int(time.time())}
        if teaching_goals:
            update_condition.update({"teaching_goals": teaching_goals})
        if teaching_preparation:
            update_condition.update({"teaching_preparation": teaching_preparation})
        if teaching_reminder:
            update_condition.update({"teaching_reminder": teaching_reminder})
        if teaching_process:
            update_condition.update({"teaching_process": teaching_process})
        db.tbkt_ywscsf.sskt_chapter_teaching_plan.filter(chapter_id=chapter_id).update(**update_condition)
        return ajax.ajax_ok(message="success")


class ChapterLearningPlan(APIView):

    def get(self, request, chapter_id):
        # 获取章节学案
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=chapter_id).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        # 获取学案
        learning_plan_info = db.tbkt_ywscsf.sskt_chapter_learning_plan.filter(chapter_id=chapter_id).first()
        learning_preparation = json.loads(learning_plan_info.learning_preparation) if learning_plan_info.learning_preparation else []
        data = {
            "chapter_id": chapter_id,
            "chapter_name": chapter_info.name,
            "learning_goals": learning_plan_info.teaching_goals if learning_plan_info.teaching_goals else "",
            "learning_preparation": learning_preparation,
        }
        return ajax.ajax_ok(data=data)

    def put(self, request, chapter_id):
        # 修改章节学案
        chapter_info = db.tbkt_ywscsf.sskt_chapter.filter(id=chapter_id).first()
        if not chapter_info:
            return ajax.ajax_fail(message='未找到对应的课时记录')
        serializer = ChapterLearningPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        learning_goals, learning_preparation = args.learning_goals, args.learning_preparation
        update_condition = {"update_time": int(time.time())}
        if learning_goals:
            update_condition.update({"learning_goals": learning_goals})
        if learning_preparation:
            update_condition.update({"learning_preparation": json.dumps(learning_preparation)})
        db.tbkt_ywscsf.sskt_chapter_learning_plan.filter(chapter_id=chapter_id).update(**update_condition)
        return ajax.ajax_ok(message="success")


class LearningPrepareTemplateListView(APIView):

    def get(self, request):
        # 获取课前准备模板列表
        serializer = LearningPrepareTemplateListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        page_no, page_size = args.get('page_no', 1), args.get('page_size', 10)
        start, end = (page_no - 1) * page_size, page_no * page_size
        total = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(del_state=0).count()
        info = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(del_state=0).select('id', 'name', 'num').order_by('-id')[start: end]
        for item in info:
            item.id_num = str(item.id).zfill(3)
        return ajax.ajax_ok(data={"total": total, "page": info})

    def post(self, request):
        # 添加课前准备模板
        serializer = LearningPrepareTemplateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, num = args.name, args.num
        if db.tbkt_ywscsf.sskt_learning_prepare_template.filter(del_state=0, name=name, num=num).exists():
            return ajax.ajax_fail(message="已存在同名同数量记录")
        nowt = int(time.time())
        db.tbkt_ywscsf.sskt_learning_prepare_template.create(name=name, num=num, add_time=nowt, update_time=nowt)
        return ajax.ajax_ok(message='success')


class LearningPrepareTemplateDetailView(APIView):

    def get(self, request, pk):
        # 模板详情
        template_info = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(id=pk, del_state=0).\
            select('id', 'name', 'num').first()
        if not template_info:
            return ajax.ajax_fail(message="未找到该模板记录")
        return ajax.ajax_ok(data=template_info)

    def put(self, request, pk):
        # 编辑模板
        template_info = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(id=pk, del_state=0).exists()
        if not template_info:
            return ajax.ajax_fail(message="未找到该模板记录")
        serializer = LearningPrepareTemplateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ajax.ajax_fail(message=get_serializer_first_errors_msg(serializer.errors))
        args = Struct(serializer.validated_data)
        name, num = args.name, args.num
        if db.tbkt_ywscsf.sskt_learning_prepare_template.filter(del_state=0, name=name, num=num, id__ne=pk).exists():
            return ajax.ajax_fail(message="已存在其他同名同数量记录")
        nowt = int(time.time())
        update_condition = {"update_time": nowt}
        if name:
            update_condition.update({"name": name})
        if num:
            update_condition.update({"num": num})
        db.tbkt_ywscsf.sskt_learning_prepare_template.filter(id=pk).update(**update_condition)
        return ajax.ajax_ok(message='success')

    def delete(self, request, pk):
        template_info = db.tbkt_ywscsf.sskt_learning_prepare_template.filter(id=pk, del_state=0).exists()
        if not template_info:
            return ajax.ajax_fail(message="未找到该模板记录")
        nowt = int(time.time())
        db.tbkt_ywscsf.sskt_learning_prepare_template.filter(id=pk).update(update_time=nowt, del_state=1)
        return ajax.ajax_ok(message='success')


def validate_video_section_info(video_section_info):
    try:
        for index, item in enumerate(video_section_info, start=1):
            # 参数校验
            video_section_id, name, type_, url, duration, sequence = item['id'], item['name'], item['type'], \
                                                                     item['url'], item['duration'], item['sequence']
            if not isinstance(video_section_id, int):
                return False, "视频小节id参数类型错误"
            if not isinstance(name, str) or not 0 < len(name) <= 10:
                return False, "视频小节name参数错误"
            if not type_ or type_ not in (1, 2):
                return False, "视频小节类型错误"
            if not url or not 0 < len(url) <= 100:
                return False, "视频小节url错误"
            if not duration or not duration > 0:
                return False, "视频小节时长错误"
            if not sequence or sequence != index:
                return False, "视频小节顺序错误"
        return True, ''
    except Exception as e:
        return False, 'video_section_info校验失败'
