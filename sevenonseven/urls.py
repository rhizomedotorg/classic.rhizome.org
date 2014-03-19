from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


urlpatterns = patterns('discuss.views',
    url(r'^$', TemplateView.as_view(template_name='sevenonseven/early.html'), name='sevenonseven_landing'),
    url(r'^past/$', TemplateView.as_view(template_name='sevenonseven/landing.html'), name='sevenonseven_past'),
	url(r'^preview/$',login_required(TemplateView.as_view(template_name='sevenonseven/2014.html'))),
    url(r'^2010/$', TemplateView.as_view(template_name='sevenonseven/2010.html')),
    url(r'^2011/$', TemplateView.as_view(template_name='sevenonseven/2011.html')),
    url(r'^2012/$', TemplateView.as_view(template_name='sevenonseven/2012.html')),
    url(r'^2013/$', TemplateView.as_view(template_name='sevenonseven/2013.html')),
    url(r'^2013-london/$', TemplateView.as_view(template_name='sevenonseven/2013_london.html')),
)
