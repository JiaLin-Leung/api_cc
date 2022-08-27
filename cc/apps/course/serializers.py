from rest_framework import serializers

from libs.utils import db
from libs.utils.exceptions import CustomError


class ClassifyListSerializer(serializers.Serializer):
    page_no = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1)


class ClassifySerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=10)
    status = serializers.IntegerField(required=True, max_value=2, min_value=1)


class CourseListSerializer(serializers.Serializer):
    page_no = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1)
    name = serializers.CharField(required=False, max_length=10)


class CourseCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=10)
    slogan = serializers.CharField(required=True, max_length=20)
    classify_id = serializers.IntegerField(required=True, min_value=1)
    grade_level = serializers.CharField(required=True, max_length=20)
    status = serializers.IntegerField(required=True, min_value=1, max_value=2)
    index_url = serializers.CharField(required=True, max_length=100)
    banner_url = serializers.CharField(required=True, max_length=100)

    def validate_classify_id(self, attr: int):
        if not db.tbkt_ywscsf.sskt_classify.filter(id=attr, del_state=0).exists():
            raise CustomError(msg='所属分类不存在')
        return attr

    def validate_name(self, attr: str):
        if db.tbkt_ywscsf.sskt_course.filter(name=attr, del_state=0).exists():
            raise CustomError(msg='存在同名课程，添加失败')
        return attr


class CourseUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=10)
    slogan = serializers.CharField(required=False, max_length=20)
    classify_id = serializers.IntegerField(required=False, min_value=1)
    grade_level = serializers.CharField(required=False, max_length=20)
    status = serializers.IntegerField(required=False, min_value=1, max_value=2)
    index_url = serializers.CharField(required=False, max_length=100)
    banner_url = serializers.CharField(required=False, max_length=100)

    def validate_classify_id(self, attr: int):
        if not attr:
            return attr
        if not db.tbkt_ywscsf.sskt_classify.filter(id=attr, del_state=0).exists():
            raise CustomError(msg='所属分类不存在')
        return attr

