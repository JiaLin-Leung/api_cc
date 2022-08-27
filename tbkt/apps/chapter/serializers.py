from rest_framework import serializers

from libs.utils import db
from libs.utils.exceptions import CustomError


class ChapterCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(required=True, min_value=1)
    name = serializers.CharField(required=True, max_length=10)
    status = serializers.IntegerField(required=True, max_value=2, min_value=1)

    def validate_course_id(self, attr: int):
        if not db.tbkt_ywscsf.sskt_course.filter(id=attr, del_state=0).exists():
            raise CustomError(msg='所属分类不存在')
        return attr


class ChapterUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=10)
    status = serializers.IntegerField(required=False, max_value=2, min_value=1)


class VideoSectionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=10)
    status = serializers.IntegerField(required=True, max_value=2, min_value=1)
    url = serializers.CharField(required=True, max_length=100)
    duration = serializers.IntegerField(required=True, min_value=0)


class VideoSectionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=10)
    status = serializers.IntegerField(required=False, max_value=2, min_value=1)
    url = serializers.CharField(required=False, max_length=100)
    duration = serializers.IntegerField(required=False, min_value=0)


class ChapterTeachingPlanSerializer(serializers.Serializer):
    teaching_goals = serializers.CharField(required=False)
    teaching_preparation = serializers.CharField(required=False)
    teaching_reminder = serializers.CharField(required=False)
    teaching_process = serializers.CharField(required=False)
    teaching_process = serializers.CharField(required=False)


class ChapterLearningPlanSerializer(serializers.Serializer):
    learning_goals = serializers.CharField(required=False, allow_blank=True)
    learning_preparation = serializers.ListField(required=False)

    def validate_learning_preparation(self, attr: list):
        if not attr:
            return attr
        for item in attr:
            if not 'index' in item:
                raise CustomError(msg='课前准备没有index')
            if not isinstance(item['index'], int):
                raise CustomError(msg='课前准备index类型错误')
            if not 'name' in item:
                raise CustomError(msg='课前准备缺少名称')
            if not isinstance(item['name'], str):
                raise CustomError(msg='课前准备名称类型错误')
            if not 'desc' in item:
                raise CustomError(msg='课前准备缺少描述')
            if not isinstance(item['desc'], str):
                raise CustomError(msg='课前准备描述类型错误')
        return attr


class LearningPrepareTemplateListSerializer(serializers.Serializer):
    page_no = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1)


class LearningPrepareTemplateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=10)
    num = serializers.CharField(required=True, max_length=10)


class LearningPrepareTemplateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=10)
    num = serializers.CharField(required=False, max_length=10)
