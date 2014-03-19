from django.conf.urls.defaults import patterns, url
from about.views import about, policy, press

urlpatterns = patterns('',
    url(r'^$', about, name='about-about'),
    url(r'^policy/$', policy, name='about-policy'),
    url(r'^press/$', press, name='about-press'),
) 