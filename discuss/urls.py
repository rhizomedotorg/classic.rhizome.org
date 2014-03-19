from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView


urlpatterns = patterns('discuss.views',
    url(r'^$', 'index', name='discuss-index'),
    
    url(r'^submit', 'new', name='discuss-new'),
    url(r'^edit/(?P<id>[^/]+)/$', 'edit', name='discuss-edit'),

    url(r'^view/(?P<id>\d+)/$', 'post_detail', name='discuss-post-detail'),
    url(r'^view_forward/(?P<id>\d+)/$', 'post_detail'),
    url(r'^(?P<id>\d+)/$', 'post_detail'),

    url(r'^view_forward/$', 'view_forward', name='discuss-view-forward'),

    url(r'^bbcode/$', TemplateView.as_view(template_name='bbcode/help.html')),
)
