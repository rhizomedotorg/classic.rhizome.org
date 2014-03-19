from django.conf.urls.defaults import *
from django.views.generic import TemplateView


urlpatterns = patterns('support.views',
    url(r'^$', 'community_campaign', name="support_index"),
    url(r'^individual/$','individual', name='individual'),
    url(r'^individuals/$','individual'),
    url(r'^organizations/$','organizations', name='organization'),
    url(r'^donate/$', 'make_donation', name='support_donate'),
    url(r'^donate/confirm_donation/$', 'confirm_donation', name='confirm_donation'),
    url(r'^donate/thanks/paypal/$', 'thanks_paypal'),
    url(r'^donate/thanks/$', 'thanks', name="support_thanks"),
    url(r'^supporters/$', 'supporters', name="supporters"),
)  
