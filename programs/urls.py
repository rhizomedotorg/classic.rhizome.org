from django.conf.urls.defaults import *

urlpatterns = patterns('programs.views',
    (r'^programs/$', 'index', name='programs_index'),
    (r'^events/$', 'events_list', name='programs_events'),
    (r'^exhibitions/$', 'exhibitions_list', name='programs_exhibitions'),
    (r'^event/(?P<slug>.+|\d+)/$', 'event_details'),
    (r'^exhibition/(?P<slug>.+|\d+)/$', 'exhibition_details'),
    (r'^videos/$', 'video_index'),
    (r'^videos/(?P<id>[^/]+)/$', 'video_details'),
)   