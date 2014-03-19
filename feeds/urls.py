from django.conf.urls.defaults import patterns
from models import (
    AnnounceFeed, AnnounceEventsFeed, AnnounceJobFeed, AnnounceOpportunityFeed, 
    ArtBaseFeed, DiscussFeed, FrontPageFeed
)

urlpatterns = patterns('feeds.views',
    (r'^announce/$', AnnounceFeed()),
    (r'^announce/events/$', AnnounceEventsFeed()),
    (r'^announce/jobs/$', AnnounceJobFeed()),
    (r'^announce/opportunities/$', AnnounceOpportunityFeed()),
    (r'^artbase/$', ArtBaseFeed()),
    (r'^blog/$', FrontPageFeed()),
    (r'^discuss/$', DiscussFeed()),
    (r'^frontpage/$', FrontPageFeed()),
)
