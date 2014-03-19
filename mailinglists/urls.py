from django.conf.urls.defaults import *

urlpatterns = patterns('mailinglists.views',
    (r'^subscribe/$', 'subscribe'),
    (r'^confirm/(?P<listid>[^/]+)/$', 'confirm'),
    (r'^unsubscribe/$', 'unsubscribe'),
)