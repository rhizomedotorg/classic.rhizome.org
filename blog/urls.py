from django.conf.urls.defaults import patterns, url 
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import RedirectView


urlpatterns = patterns('blog.views',
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        view='post_detail',
        name='blog_detail'
    ),
    url(r'^(?P<post_id>\d+)/$',
        view='post_detail_forward',
        name='blog_detail_forward'
    ),
    url(r'^body/(?P<post_id>\d+)/$', view='post_body', name='post_body'),
    url(r'^tease/(?P<post_id>\d+)/$', view='post_tease', name='post_tease'),
    url(r'^article-2.0.php',
        view='old_post_forward',
        name='old_post_forward'
    ),
    url(r'^fp/blog.php/(?P<post_id>\d+)/$',
        view='post_detail_forward',
        name='post_detail_forward'
    ),
    url(r'^fp/month.php',
        view='old_month_forward',
        name='old_month_forward'
    ),    
    url(r'^reblog_forward/$',
        view='reblog_forward',
        name='reblog_forward'
    ),
    url(r'^featured/$', RedirectView.as_view(url=reverse_lazy('blog_index'))),
    url(r'^artist-profiles/$',
        view='artist_profiles',
        name='artist_profiles'
    ),
    url(r'^reblog_forward/(?P<reblog_id>\d+)/$',
        view='reblog_forward',
        name='reblog_forward_id'
    ),
    url(r'^archive/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/$',
        view='post_archive_day',
        name='blog_archive_day'
    ),
    url(r'^archive/(?P<year>\d{4})/(?P<month>\w{3})/$',
        view='post_archive_month',
        name='blog_archive_month'
    ),
    url(r'^archive/(?P<year>\d{4})/$',
        view='post_archive_year',
        name='blog_archive_year'
    ),
    url(r'^archive/(?P<year>\d{4})/$',
        view='post_archive_year',
        name='blog_archive_year'
    ),
    url(r'^archive/$',
        view='post_archive_year',
        name='blog_archive_year'
    ),
    url(r'^tags/(?P<slug>[-.\w]+)/$',
        view='tag_detail',
        name='blog_tag_detail'
    ),
    url(r'^tag/(?P<slug>[-.\w]+)/$',
        view='tag_detail',
        name='blog_tag_detail'
    ),
    url(r'^tags/$', RedirectView.as_view(url=reverse_lazy('blog_index'))),
    url(r'^tag.php',
        view='old_tag_forward',
        name='old_tag_forward'
    ),
    url (r'^search/$',
        view='search',
        name='blog_search'
    ),
    url(r'^page/(?P<page>\w)/$',
        view='index',
        name='blog_index'
    ),
    url(r'^$',
        view='index',
        name='blog_index'
    ),
)
