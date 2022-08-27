# coding=utf-8

from django.conf.urls import include, url

urlpatterns = [
    url(r'^course/', include('apps.course.urls')),  # 课程相关
    url(r'^chapter/', include('apps.chapter.urls')),  # 章节相关

]
