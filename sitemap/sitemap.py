from django.contrib.sitemaps import Sitemap

from news_sitemaps import register, NewsSitemap

from accounts.models import RhizomeUser
from announce.models import Event, Job, Opportunity
from artbase.models import ArtworkStub, MemberExhibition
from blog.models import Post
from discuss.models import DiscussionThread
from programs.models import Exhibition, RhizEvent


class RhizomeSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

class NewsSitemap(NewsSitemap):
    limit = 1000
    def items(self):
        return Post.objects.published().exclude(staff_blog=True)

    def lastmod(self, obj):
        return obj.publish

    def genres(self, obj):
        return 'Blog'

    def publication_date(self, obj):
        return obj.publish
        
    def title(self, obj):
        return obj.title

register(blog=NewsSitemap)

class BlogSitemap(RhizomeSitemap):
    def items(self):
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.modified

class DiscussSitemap(RhizomeSitemap):
    def items(self):
        threads = DiscussionThread.objects.filter(is_public=True).exclude(pk=1)
        return [thread for thread in threads if thread.is_discuss_thread()]

    def lastmod(self, obj):
        return obj.last_comment.submit_date
        
class EventSitemap(RhizomeSitemap):
    def items(self):
        return Event.objects.filter(status=True)

    def lastmod(self, obj):
        return obj.created
        
class OpportunitySitemap(RhizomeSitemap):
    def items(self):
        return Opportunity.objects.filter(status=True)

    def lastmod(self, obj):
        return obj.modified

class JobSitemap(RhizomeSitemap):
    def items(self):
        return Job.objects.filter(status=True)

    def lastmod(self, obj):
        return obj.modified
        
class RhizEventSitemap(RhizomeSitemap):
    def items(self):
        return RhizEvent.objects.all()

class RhizExhibitionsSitemap(RhizomeSitemap):
    def items(self):
        return Exhibition.objects.all()

class ExhibitionSitemap(RhizomeSitemap):
    def items(self):
        return MemberExhibition.objects.filter(live=True)
    
class ArtWorkSitemap(RhizomeSitemap):
    def items(self):
        return ArtworkStub.objects.exclude(status='deleted').exclude(status='unsubmitted')
        
class ProfilesSitemap(RhizomeSitemap):
    def items(self):
        return RhizomeUser.objects.filter(is_active=True).filter(visible=True)
