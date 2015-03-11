from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('accounts.views',
    url(r'^commissions-voting/$', 'commissions_voting', name="accounts_commissions_voting"),
    url(r'^anonymous/$', 'anonymous_profile'),
    url(r'^edit/$', 'edit_profile', name="edit_profile"),
    url(r'^manage-orgsub/$', 'manage_orgsub'),
    url(r'^manage-membership/$', 'manage_membership'),
    # url(r'^manage-mailchimp/$', 'manage_mailchimp_subscriptions'),
    url(r'^favorites/(?P<user_id>\d+)/(?P<artwork_id>\d+)/$', 'add_artwork_to_favorites'),
    url(r'^(?P<user>.+|\d+)/edit/$', 'edit_profile_forward'),
    url(r'^manage-orgsub/$', 'manage_orgsub'),
    url(r'^(?P<user>.+|\d+)/miniprofile/$', 'miniprofile'),
    url(r'^(?P<user>.+|\d+)/$', 'user_profile', name="user_profile"),
    url(r'^(?P<user>.+|\d+)/profile/$', 'user_profile', name="anonymous_profile"),
    url(r'^id_forward', 'id_forward', name="id_forward"),
    url(r'^$', 'profiles_list', name='profiles'), 
)  
