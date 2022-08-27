from django.conf.urls import url

from apps.chapter.common import get_template_info
from apps.chapter.views import ChapterListView, ChapterDetailView, ChapterOperateView, ChapterVideoDetailView, \
    VideoSectionCreateView, VideoSectionUpdateView, VideoSectionOperateView, ChapterTeachingPlan, ChapterLearningPlan, \
    LearningPrepareTemplateListView, LearningPrepareTemplateDetailView

urlpatterns = [
    url(r'^get_template_info$', get_template_info),  # 课前准备下拉框接口

    url(r'^$', ChapterListView.as_view()),
    url(r'^(?P<pk>\d+)/$', ChapterDetailView.as_view()),
    url(r'^(?P<pk>\d+)/(?P<action>\w+)/$', ChapterOperateView.as_view()),

    url(r'^video/(?P<chapter_id>\d+)/$', ChapterVideoDetailView.as_view()),
    # url(r'^video/add_section/(?P<video_id>\d+)/$', VideoSectionCreateView.as_view()),
    # url(r'^video/update_section/(?P<video_section_id>\d+)/$', VideoSectionUpdateView.as_view()),
    # url(r'^video/section/(?P<video_section_id>\d+)/(?P<action>\w+)/$', VideoSectionOperateView.as_view()),

    url(r'^teach_plan/(?P<chapter_id>\d+)/$', ChapterTeachingPlan.as_view()),
    url(r'^learn_plan/(?P<chapter_id>\d+)/$', ChapterLearningPlan.as_view()),

    url(r'^template/$', LearningPrepareTemplateListView.as_view()),
    url(r'^template/(?P<pk>\d+)/$', LearningPrepareTemplateDetailView.as_view()),

]


