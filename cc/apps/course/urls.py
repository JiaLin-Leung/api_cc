from django.conf.urls import url

from apps.course.common import get_classify_info
from apps.course.views import ClassifyListView, ClassifyDetailView, CourseListView, CourseDetailView, \
    CourseHighlightDetailView, CourseTeacherDetailView

urlpatterns = [
    url(r'^classify/$', ClassifyListView.as_view()),
    url(r'^classify/(?P<pk>\d+)/$', ClassifyDetailView.as_view()),

    url(r'^$', CourseListView.as_view()),
    url(r'^(?P<pk>\d+)/$', CourseDetailView.as_view()),

    url(r'^highlight/(?P<course_id>\d+)/$', CourseHighlightDetailView.as_view()),
    url(r'^teacher/(?P<course_id>\d+)/$', CourseTeacherDetailView.as_view()),


]

# 公共方法
urlpatterns += [
    url(r'^get_classify_info/$', get_classify_info),  # 课程分类选择框数据

]
