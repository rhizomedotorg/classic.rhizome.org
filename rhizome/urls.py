from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import *
from proxy_server.views import *
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy
from mailinglists.views import *
from hitcount.views import update_hit_count_ajax

from sitemap.sitemap import (
    RhizomeSitemap, ArtWorkSitemap, BlogSitemap, DiscussSitemap, 
    EventSitemap, ExhibitionSitemap, JobSitemap, OpportunitySitemap, 
    ProfilesSitemap, RhizEventSitemap, RhizExhibitionsSitemap
)

from tastypie.api import Api
from api import (
    BlockResource, CampaignResource, CreateDonationResource, QuickStatsResource
)

v1_api = Api(api_name='v1')
v1_api.register(BlockResource())
v1_api.register(CreateDonationResource())
v1_api.register(CampaignResource())
v1_api.register(QuickStatsResource())

sitemaps = {
    'about': RhizomeSitemap,
    'artworks': ArtWorkSitemap,
    'blog': BlogSitemap,
    'discuss': DiscussSitemap,
    'events': EventSitemap,
    'exhibitions': ExhibitionSitemap,
    'jobs': JobSitemap,
    'opportunities': OpportunitySitemap,
    'profiles': ProfilesSitemap,
    'rhizevents': RhizEventSitemap,
    'rhizexhibitions': RhizExhibitionsSitemap,
}

from django.contrib import admin
admin.autodiscover()

from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from djcelery.models import (
    CrontabSchedule, IntervalSchedule, PeriodicTask, TaskState, WorkerState
)
from countries.models import Country, UsState
from hitcount.models import ( 
    BlacklistIP, BlacklistUserAgent, Hit, HitCount
)
from inlines.models import InlineType
from oembed.models import ProviderRule, StoredOEmbed
from tastypie.models import ApiKey

admin.site.unregister([
    # Group, 
    # CrontabSchedule, 
    # IntervalSchedule, 
    # PeriodicTask, 
    # TaskState, 
    # WorkerState, 
    # Country, 
    # UsState, 
    # BlacklistIP, 
    # BlacklistUserAgent, 
    # Hit, 
    # HitCount, 
    # InlineType, 
    # ProviderRule, 
    # StoredOEmbed, 
    # ApiKey
])

# enabling profiles view
from accounts.views import *

pxs = [
    url(r'^$', 'frontpage.views.frontpage', name='frontpage'),
    url(r'^hit/update/$', update_hit_count_ajax, name='hitcount_update_ajax'),
    url(r'^rza/', include(admin.site.urls)),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^blog/', 'blog.views.forward'), 
    url(r'^search/', 'search.views.rhizome_search'), 
    url(r'^api/', include(v1_api.urls)),
    url(r'^tasks/', include('djcelery.urls')),

    url(r'^staffblog/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        'blog.views.post_detail'), 

    url(r'^staffblog/$', 'blog.views.staff_blog'),   

    #sitemap (use these create calls to write a static file via cronjob)
    url(r'^create/sitemap\.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemaps}),
    url(r'^create/sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    url(r'^news-sitemaps/', include('news_sitemaps.urls')),
    
    ###NON PROFILE ACCOUNTS VIEWS
    #django contrib login/out and password handling
    url(r'^login/$', 'accounts.views.login',
        {'template_name': 'accounts/login.html'}, name="login"),
    
    url(r'^ajax_login/$', 'accounts.views.ajax_login', name="ajax_login"),

    url(r'^accounts/login/$', 'accounts.views.login', 
        {'template_name': 'accounts/login.html'}),
    
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),  
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),  
    url(r'^register/thanks/$', 'accounts.views.register_thanks', name="register_thanks"), 
    url(r'^welcome/$', 'accounts.views.welcome', name='welcome'),
    url(r'^welcome/orgsub/$', 'accounts.views.orgsub_invite_welcome'),

    url(r'^register/$', 'accounts.views.register', name='accounts_register'), 

    #admin login as user
    url(r'^login/user/(?P<user_id>[\d_]+)$', 'accounts.views.login_as_user'),  

    url(r'^accounts/emails/membership/$', 'accounts.views.conversion_email', 
        name="conversion_email"),    

    url(r'^accounts/emails/renewal/$', 'accounts.views.renewal_email', 
        name="renewal_email"),    
    
    url(r'^accounts/emails/welcome/$', 'accounts.views.welcome_email', 
        name="welcome_email"),    

    #nginx ssi includes
    url(r'^topnav-login/$', 'proxy_server.views.topnav_login', name='topnav_login'),
    
    url(r'^editorial/comment_fragment/$', 
        'proxy_server.views.blog_comment_fragment', 
        name='blog_comment_fragment'),
    
    url(r'^announce/comment_fragment/$', 
        'proxy_server.views.announce_comment_fragment', 
        name='announce_comment_fragment'),
    
    url(r'^commissions/comment_fragment/$', 
        'proxy_server.views.commissions_comment_fragment', 
        name='commissions_comment_fragment'),
 
    url(r'^color-picker/$', TemplateView.as_view(template_name='widgets/colorpicker/popup.html'), name='color_picker'),
    
    #password reset/change
    url(r'^password/$', 'accounts.views.password'), 
    url(r'^forgot_password/$','django.contrib.auth.views.password_reset',
            {'template_name': 'accounts/password_reset_form.html',
             'email_template_name':'accounts/password_reset_email.html'}),
    
    url(r'^password_reset/$','django.contrib.auth.views.password_reset',
            {'template_name': 'accounts/password_reset_form.html',
             'email_template_name':'accounts/password_reset_email.html'}),

    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
            'django.contrib.auth.views.password_reset_confirm',
            {'template_name': 'accounts/password_reset_confirm.html', 
             'post_reset_redirect':'/password_reset_complete/'}),
    
    url(r'^password_reset_done/$', 'django.contrib.auth.views.password_reset_done',  
            {'template_name': 'accounts/password_reset_done.html'}),  

    url(r'^password_reset_complete/$', 'django.contrib.auth.views.password_reset_complete',  
            {'template_name': 'accounts/password_reset_complete.html'}),  
   
    url(r'^password_change/$', 'django.contrib.auth.views.password_change',
            {'template_name': 'accounts/password_change_form.html'}),

    url(r'^password_change_done/$', 'django.contrib.auth.views.password_change_done',
            {'template_name': 'accounts/password_change_done.html'}),
    
    url(r'^users/(?P<username>.+|\d+)/$', 'accounts.views.username_forward'),
    url(r'^community/profile/$', 'accounts.views.profiles_list'), 
    url(r'^community/profiles/$', 'accounts.views.profiles_list'), 
    url(r'^community/$', 'accounts.views.community', name='community'),
    url(r'^jobs/$', 'announce.views.jobs_forward', name='jobs'),

    
    url(r'^supporters/$', 'support.views.supporters'),

    url(r'^campaign/$', 'support.views.community_campaign', name='campaign'),
    
    url(r'^policy/$', 'about.views.policy'),

    #membership_required
    url(r'^membership_required/$', 'accounts.views.membership_required', 
        name="membership_required"),

    #for grabbing admin js
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog'),
    
    #newsletters    
    url(r'^editorial/news/$', 'mailinglists.views.newsletter'),
    url(r'^netartnews/$', 'mailinglists.views.newsletter'),
    
    #member newsletter
    url(r'^member-newsletter/$', 'mailinglists.views.member_newsletter'),

    #old news forward
    url(r'^news/story.rhiz','blog.views.old_news_forward'),
    url(r'^news/story.php','blog.views.old_news_forward'),
    url(r'^netartnews/story.rhiz','blog.views.old_news_forward'),

    #benefit
    url(r'^benefit_auction/$', TemplateView.as_view(template_name='benefit_auction.html'), name='benefit_auction'),
    # url(r'^demo/$', TemplateView.as_view(template_name='demo.html'), name='demo'),

    url(r'^the-download/$', 'programs.views.downloadofthemonth', 
            name='downloadofthemonth'),
    
    url(r'^the-download/(?P<year>\d{4})/(?P<month>\w{3})/$', 
            'programs.views.downloadofthemonth_detail', 
            name='downloadofthemonth_detail'),

    # blog 
    url(r'^editorial/', include('blog.urls')),

    # custom apps
    url(r'^about/', include('about.urls')),
    url(r'^profiles/', include('accounts.urls')),#ACCOUNTS URLS HERE
    url(r'^profile/', include('accounts.urls')),

    #view for non-artbase works (portfolio work)
    url(r'^portfolios/artwork/(?P<id>\d+)/$', 'artbase.views.artwork'),

    url(r'^portfolios/$', 'accounts.views.portfolios', name='portfolios'),
    url(r'^community/portfolios/$', 'accounts.views.portfolios'),
    
    url(r'^announce/', include('announce.urls')),
    url(r'^art/', include('artbase.urls')),
    url(r'^artbase/', include('artbase.urls')),
    url(r'^commissions/', include('commissions.urls')),
    url(r'^discuss/', include('discuss.urls')), 
    url(r'^sevenonseven/', include('sevenonseven.urls')), 

    #old forwarding for artbase
    url(r'object.php$', 'artbase.views.object_forward'), #/object..php?id_number&.... 
    url(r'object.rhiz$', 'artbase.views.object_forward'), #/object..php?id_number&.... 
   
    url(r'^join/', include('support.urls')),
    url(r'^support/', include('support.urls')),
    
    #donate reroute
    url(r'^donate/$', 'support.views.make_donation'),
    
    #membership
    url(r'^membership/$', 'support.views.individual'), 

    #feeds
    url(r'^feeds/', include('feeds.urls')),

    # deploy button
    url(r'^deploy/$', 'deploy_button.views.deploy', name='deploy-buttom-deploy'), 

    url(r'^programs/$', 'programs.views.index', name='programs'),
    url(r'^subscribe/$', 'mailinglists.views.subscribe', name='mailinglists'),   
    url(r'^subscribe/news/$', lambda request: 
            HttpResponseRedirect('http://rhizome.list-manage.com/subscribe?u=a1487b13ca8ed17d052f71f12&id=6f6e0ea86b'), 
            name="subscribe_news"), 

    url(r'^unsubscribe/$', 'mailinglists.views.unsubscribe'),   
    url(r'^unsubscribe/news/$', lambda request: 
            HttpResponseRedirect('http://rhizome.list-manage.com/unsubscribe?u=a1487b13ca8ed17d052f71f12&id=6f6e0ea86b'), 
            name="unsubscribe_news"),      

    url(r'^events/$', 'programs.views.events_list', name='programs_events'),
    url(r'^events/(?P<slug>[\w-]+)/$', 'programs.views.event_details'),
    url(r'^exhibitions/$', 'programs.views.exhibitions_list', name='programs_exhibitions'),
    url(r'^exhibitions/(?P<slug>[\w-]+)/$', 'programs.views.exhibition_details'),
    url(r'^videos/$', 'programs.views.video_index'),
    url(r'^videos/(?P<id>[^/]+)/$', 'programs.views.video_details'),
    
    url(r'^frontpage-preview/(?P<slug>[\w-]+)/$', 'exhibitions.views.frontpage_exhibition_preview', name='frontpage_preview'),

    url(r'^email/', include('eazyemail.urls')),
    url(r'^prix-net-art/', 'commissions.views.submit_grant_proposal', {'grant_slug': 'prix-net-art'}),
    url(r'^today/', 'blog.views.today'),
]

if settings.DEBUG:
    pxs.append((r'^media/(?P<path>.*)$', 'django.views.static.serve', 
        {'document_root': settings.MEDIA_ROOT}))

urlpatterns = patterns('', *pxs)
