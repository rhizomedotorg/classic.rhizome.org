from django.contrib.syndication.views import Feed

from announce.models import Event, Job, Opportunity, get_latest_announcements
from artbase.views import latest_additions
from blog.models import Post
from utils.helpers import bbcode_to_html, strip_bbcode

from threadedcomments.models import ThreadedComment


class FrontPageFeed(Feed):
    title = 'The Rhizome Frontpage RSS'
    link = '/feeds/frontpage/'
    description = 'The Rhizome Blog and Rhizome News'
    
    def items(self):
        return Post.objects.published().order_by('-publish')[:50]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        try:
            return item.body
        except:
            pass
    
    def item_author_name(self, item):
        return item.get_authors_as_text()
            
    def item_pubdate(self, item):
        return item.publish

class AnnounceFeed(Feed):
    title = 'Rhizome Announce RSS'
    link = '/feeds/announce/'
    description = 'Rhizome\'s Community Submitted Announcements'
    
    def items(self):
        return get_latest_announcements(50)
        
    def item_title(self, item):
        return item.title

    def item_author_name(self,item):
        return item.user.get_profile()

    def item_description(self, item):
        try:
            description = bbcode_to_html(item.description)
        except:
            description = strip_bbcode(item.description)
        return description
    
    def item_pubdate(self, item):
        return item.created

class AnnounceEventsFeed(Feed):
    title = 'Rhizome Announce RSS: Events'
    link = '/feeds/announce/events'
    description = 'Rhizome\'s Community Submitted Events'
    
    def items(self):
        return Event.objects.filter(status=True).order_by('-created')[:50]
        
    def item_title(self, item):
        return item.title
        
    def item_author_name(self,item):
        return item.user.get_profile()

    def item_description(self, item):
        try:
            description = bbcode_to_html(item.description)
        except:
            description = strip_bbcode(item.description)
        return description
    
    def item_pubdate(self, item):
        return item.created
        
class AnnounceOpportunityFeed(Feed):
    title = 'Rhizome Announce RSS: Opportunities'
    link = '/feeds/announce/opportunities'
    description = 'Rhizome\'s Community Submitted Opportunities'
    
    def items(self):
        return Opportunity.objects.filter(status=True).order_by('-created')[:50]
        
    def item_title(self, item):
        return item.title

    def item_author_name(self,item):
        return item.user.get_profile()

    def item_description(self, item):
        try:
            description = bbcode_to_html(item.description)
        except:
            description = strip_bbcode(item.description)
        return description
    
    def item_pubdate(self, item):
        return item.created

class AnnounceJobFeed(Feed):
    title = 'Rhizome Announce RSS: Jobs'
    link = '/feeds/announce/jobs'
    description = 'Rhizome\'s Community Submitted Jobs'
    
    def items(self):
        return Job.objects.filter(status=True).order_by("-created")[:50]
        
    def item_title(self, item):
        return item.title

    def item_author_name(self,item):
        return item.user.get_profile()

    def item_description(self, item):
        try:
            description = bbcode_to_html(item.description)
        except:
            description = strip_bbcode(item.description)
        return description
    
    def item_pubdate(self, item):
        return item.created

class DiscussFeed(Feed):
    title = 'Rhizome Discuss RSS'
    link = '/feeds/discuss/'
    description = 'Rhizome\'s Community Discussions'
    
    def items(self):
        return ThreadedComment.objects.filter(is_public=True).exclude(object_pk='')[:50]
        
    def item_title(self, item):
        return item.title

    def item_author_name(self,item):
        return item.user.get_profile()

    def item_description(self, item):
        try:
            description = bbcode_to_html(item.comment)
        except:
            description = strip_bbcode(item.comment)
        return description
    
    def item_pubdate(self, item):
        return item.submit_date
        
class ArtBaseFeed(Feed):
    title = 'Rhizome ArtBase RSS'
    link = '/feeds/artbase/'
    description = 'Additions to Rhizome\'s ArtBase'
    
    def items(self):
        return latest_additions(50)

    def item_author_name(self,item):
        return item.user.get_profile()
        
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        try:
            description = item.description
        except:
            pass
        return description
    
    def item_pubdate(self, item):
        return item.approved_date
