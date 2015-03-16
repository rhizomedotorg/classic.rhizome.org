from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView


urlpatterns = patterns('discuss.views',
    url(r'^$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/'), name='sevenonseven_landing'),
    url(r'^past/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/'), name='sevenonseven_past'),
    #url(r'^preview/$',login_required(RedirectView.as_view(url='http://sevenonseven.rhizome.org/'))),
    url(r'^2010/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
    url(r'^2011/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
    url(r'^2012/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
    url(r'^2013/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
    url(r'^2013-london/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
    url(r'^2014/$', RedirectView.as_view(url='http://sevenonseven.rhizome.org/')),
)
