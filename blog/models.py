import os
import datetime
import urllib2
import HTMLParser

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save 
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags


import tagging
from tagging.models import Tag, TaggedItem
from tagging.fields import TagField

from blog.managers import PublicManager
from utils.helpers import clean_html
from artbase.models import License


class Post(models.Model):
    DRAFT = 1 
    PUBLIC = 2 
    PRIVATE = 3 
    STATUS_CHOICES = (
        (DRAFT, 'draft'),
        (PUBLIC, 'public'),
        (PRIVATE, 'private'),
    )

    title = models.CharField('title', max_length=200)
    subtitle = models.TextField('subtitle', blank=True)
    slug = models.SlugField(unique_for_date='publish', db_index=True)
    authors = models.ManyToManyField(User,null=True, blank=True)
    byline = models.CharField(max_length=200, null=True, blank=True)
    post_item_link = models.URLField('item link', null=True, blank=True)
    body = models.TextField('body')
    tease = models.TextField('tease', blank=True)
    fp_news_excerpt = models.TextField('excerpt', blank=True, null=True) 
    staff_blog = models.BooleanField('staff blog only', default=False,blank=True, db_index=True)
    fp_and_staff_blog = models.BooleanField('front page + staff blog', default=False,blank=True, db_index=True)
    featured_article = models.BooleanField('featured', default=False,blank=True, db_index=True)
    artist_profile = models.BooleanField(default=False,blank=True, db_index=True)
    sponsored = models.BooleanField(default=False,blank=True)
    artbase_essay = models.BooleanField(default=False,blank=True, db_index=True)
    allow_comments = models.BooleanField('allow comments', default=True)
    is_live = models.BooleanField('auto-refresh (for live blogging)', default=False, blank=True)
    is_micro = models.BooleanField(default=False, blank=True)
    status = models.IntegerField('status', choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    publish = models.DateTimeField('publish date', default=datetime.datetime.now, db_index=True)
    created = models.DateTimeField('created', auto_now_add=True)
    modified = models.DateTimeField('modified', auto_now=True)
    objects = PublicManager()
    tags = TagField(max_length=1024, null=True, blank=True)

    class Meta:
        db_table  = 'blog_posts'
        ordering  = ('-publish',)
        get_latest_by = 'publish'
        
    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.old_status = self.status
        
    def save(self, *args, **kwargs):
        ''' On save, clean HTML '''
        self.body = clean_html(self.body)
        if not self.id:
            self.created = datetime.datetime.now()
    
        if self.id:            
            if not self.byline or self.byline == "" and self.authors:
                self.byline = self.get_authors_as_text()
                
        if not self.byline:
            self.byline = "Rhizome"
        super(Post, self).save(*args, **kwargs)

    def can_view(self, user):
        if user.is_staff:
            return True

        if self.status == self.PUBLIC and self.publish <= datetime.datetime.now():
            return True
        return False
        
    def get_authors(self):
        return self.authors.all()
    
    def get_authors_as_text(self):
        if self.byline and self.byline != "":
            return self.byline
        else:
            if len(self.authors.all()) > 1:
                return ''.join([("%s " % author.get_profile()) for author in self.authors.all()])
            else:
                return ''.join([("%s" % author.get_profile()) for author in self.authors.all()])                   

    def get_authors_admin(self):
        return ''.join([("<a href='?authors__id__exact=%s'>%s</a> " % (author.id,author.get_profile())) for author in self.authors.all()])
        
    get_authors.short_description = 'Author/User'
    get_authors_admin.allow_tags = True
    get_authors_admin.short_description = 'Author/User'

    def __unicode__(self):
        return u'%s' % self.title
    
    def content_type(self):
        ct = ContentType.objects.get_for_model(self)
        return ct
    
    def content_type_id(self):
        ct = ContentType.objects.get_for_model(self)
        return ct.id
    
    def get_tags(self):
        """
        To get at the actual list of tags and not just the comma or
        or space separated string
        """
        return Tag.objects.get_for_object(self)

    def is_reblog(self):
        """
        checks to see if post is a reblogpost
        """        
        try:
            return ReblogPost.objects.get(post_ptr = self.id)
        except:
            return False

    def has_images(self):
        has_images = False
        if self.get_images():
            return True
        if self.get_first_image_from_body():
            return True
            
    def get_images(self):
        """
        Get all images related to post
        """
        return PostImage.objects.filter(post=self)

    def get_first_image(self):
        first_image = None
        images = PostImage.objects.filter(post=self)[:1]
        if images:
            return images[0].image
        return first_image

    def get_first_image_from_body(self):
        """
        returns thumbnail of first image for post
        """
        working_url = None
        try:
            from BeautifulSoup import BeautifulSoup as Soup
        except ImportError:
            Soup = None
        
        if Soup:
            soup = Soup(self.body)
            images = soup.findAll('img')
            if images:
                first_image = images[0]
                first_image_url = first_image['src']
                try:
                    urllib2.urlopen(first_image_url, timeout = 1)
                    working_url = first_image_url
                    return working_url
                except:
                    pass
        return working_url

    def get_all_images_from_body(self):
        """
        returns all image urls for post
        """
        urls = []

        try:
            from BeautifulSoup import BeautifulSoup as Soup
        except ImportError:
            Soup = None
        
        if Soup:
            soup = Soup(self.body)
            images = soup.findAll('img')
            if images:
                for img in images:
                    urls.append(img['src'])
        return urls

    def get_working_images_from_body(self):
        """
        returns all image urls for post
        """
        working_urls = []

        try:
            from BeautifulSoup import BeautifulSoup as Soup
        except ImportError:
            Soup = None
        
        if Soup:
            soup = Soup(self.body)
            images = soup.findAll('img')
            if images:
                for img in images:
                    img_url = img['src']
                    try:
                        urllib2.urlopen(img_url, timeout = 1)
                        working_urls.append(img_url) 
                    except urllib2.URLError, e:
                        print e
        return working_urls

    def get_broken_images_from_body(self):
        """
        returns all broken image urls for post
        """
        broken_urls = []

        try:
            from BeautifulSoup import BeautifulSoup as Soup
        except ImportError:
            Soup = None
        
        if Soup:
            soup = Soup(self.body)
            images = soup.findAll('img')
            if images:
                for img in images:
                    img_url = img['src']
                    try:
                        urllib2.urlopen(img_url, timeout = 1)
                        pass
                    except urllib2.URLError, e:
                        print e
                        broken_urls.append(img_url)
        return broken_urls

    def get_audio(self):
        """
        To get at the actual list of tags and not just the comma or
        or space separated string
        """
        return PostAudio.objects.filter(post=self) 

    def get_files(self):
        """
        To get at the actual list of tags and not just the comma or
        or space separated string
        """
        return PostFile.objects.filter(post=self) 
        
    def get_videos(self):
        """
        To get at the actual list of tags and not just the comma or
        or space separated string
        """
        return PostVideo.objects.filter(post=self)       
    
#     @permalink
#     def get_absolute_url(self):
#         return ('blog_detail', None, {
#             'year': self.publish.year,
#             'month': self.publish.strftime('%b').lower(),
#             'day': self.publish.day,
#             'slug': self.slug
#         })
    
    def get_absolute_url(self):
        '''
        the above screwed with the url conf so had to get explicit
        '''
        if self.staff_blog or self.fp_and_staff_blog:
            return "/staffblog/%s/%s/%s/%s" % (self.publish.year, self.publish.strftime('%b').lower(), self.publish.day, self.slug)
        else:
            return "/editorial/%s/%s/%s/%s" % (self.publish.year, self.publish.strftime('%b').lower(), self.publish.day, self.slug)
        
    def get_previous_post(self):
        if self.staff_blog:
            return self.get_previous_by_publish(status__gte=2,staff_blog=True)
        else:
            return self.get_previous_by_publish(status__gte=2)

    def get_next_post(self):
        if self.staff_blog:
            return self.get_next_by_publish(status__gte=2,staff_blog=True)
        else:
            return self.get_next_by_publish(status__gte=2)

    def get_similar_posts(self):
        """
        gets posts that are similar via author, title, tags
        """  
        author_posts = []
        if self.get_authors():
            for author in self.get_authors():
                for post in author.get_profile().get_blog_posts(6):
                    if post != self and post.has_images():
                        author_posts.append(post)
        
        for post in Post.objects.filter(byline = self.byline).exclude(id = self.id).order_by('?')[:6]:
            if post.has_images():
                author_posts.append(post)

        tag_posts = []        
        for tag in self.get_tags():
            posts_with_tag = TaggedItem.objects.get_by_model(Post, tag) \
                .filter(status=2) \
                .filter(publish__lte=datetime.datetime.now()) \
                .exclude(id = self.id) \
                .order_by('?')[:6]
            tag_posts.append(posts_with_tag)
        flat_tag_posts = [item for sublist in tag_posts for item in sublist if item.has_images()]

        similar_posts = author_posts + flat_tag_posts
        return similar_posts

    def create_description(self):
        '''
        use this if no tease is supplied
        '''
        if not self.tease:
            stripped_body = strip_tags(self.body)
            graphs = [graph for graph in stripped_body.split("\n")]
            for graph in  graphs:
                words = [word for word in graph.split(" ")]
                if len(words) > 20:
                    return graph
        else:
            return self.tease

    def get_formatted_news_excerpt(self):
        excerpt = self.fp_news_excerpt
        
        try:
            from BeautifulSoup import BeautifulSoup as Soup
        except ImportError:
            Soup = None
        
        if Soup:
            soup = Soup(excerpt)
            iframes = soup.findAll('iframe')
            embeds = soup.findAll('embed')
            objects = soup.findAll('object')
            images = soup.findAll('img')

            for iframe in iframes:
                excerpt = excerpt.replace("%s" % iframe,"") 
            for embed in embeds:
                excerpt = excerpt.replace("%s" % embed,"") 
            for obj in objects:
                excerpt = excerpt.replace("%s" % obj,"") 
            for img in images:
                orig = "%s" % img
                if 'width' in img:
                    if img["width"] > 440:
                        img["width"] = 440
                        img["height"] = ""
                        excerpt = excerpt.replace('%s' % orig, '%s' % img,) 
                    
        excerpt = excerpt.replace('<p class="more span-15"><a href="%s">READ ON &raquo;</a></p>' % self.get_absolute_url(),'')
        return excerpt
        
try:
    tagging.register(Post,tag_descriptor_attr="post")
except tagging.AlreadyRegistered:
    # http://code.google.com/p/django-tagging/issues/detail?id=128 
    # Not sure the right way to register a model for tagging b/c it
    # raises this error if registered more than once. We end up registering
    # the first time during "manage.py syncdb" and then a second time when
    # actually attempting to run the site.
    pass

def on_post_save(sender, **kwargs):
    instance = kwargs['instance']
    if instance.status == 2:
        for a in instance.get_authors():
            a.get_profile().add_points_for_object(instance)
        
post_save.connect(on_post_save, sender=Post)



'''
Reblog Posts were migrated from rhizome's old reblog system
'''

class ReblogPost(Post):
    reblog_post_id = models.IntegerField(max_length=11,null=False,blank=False, db_index=True)
    post_author = models.ForeignKey(User, null=True, blank=True)
    rhiz_author = models.ForeignKey(User,null=True,blank=True,limit_choices_to = {'is_staff':True},related_name="rhiz_author")
    comment = models.TextField(_('comment'), blank=True)
    itemselect_link = models.URLField(blank=True)
    item_link = models.URLField(blank=True)
    item_body = models.TextField(_('item body'), blank=True)
    feed_url = models.URLField(blank=True)
    feed_title = models.CharField(_('feed title'), max_length=200,blank=True)
    feed_link = models.URLField(blank=True)
    feed_description = models.TextField(_('feed description'),blank=True )
    objects = PublicManager()

'''
Blogroll
'''
        
class BlogRoll(models.Model):
    """Other blogs you follow."""
    name = models.CharField(max_length=100)
    url = models.URLField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('sort_order', 'name',)
        verbose_name = 'blog roll'
        verbose_name_plural = 'blog roll'

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return self.url

'''
PostMeta
'''

class PostMeta(models.Model):
    """Rhizome Post Metadata."""
    post = models.ForeignKey(Post)
    meta_key = models.CharField(max_length=200, db_index=True)
    meta_value = models.TextField(max_length=200)
    
    def __unicode__(self):
        return "%s: %s => %s" % (self.post.id, self.key, self.value)
        
'''
Blog Image (ripped off basic.models.photo
'''

def blog_media_upload(instance, filename):
    extension = filename.split('.')[-1]
    return 'blog/%s/%s.%s' % (instance.post.id, instance.title.replace(" ", "-"), extension)

class PostImage(models.Model):
    post = models.ForeignKey(Post)
    title = models.CharField(max_length=255)
    image = models.FileField(upload_to=blog_media_upload,db_index=True)
    taken_by = models.CharField(max_length=100, blank=True)
    license = models.ForeignKey(License, blank=True, null = True)
    description = models.TextField(blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_postimage'
        verbose_name = 'image'
        ordering = ['-uploaded']

    def __unicode__(self):
        return '%s / %s' % (self.title, self.post.title)

    @property
    def url(self):
        return '%s%s' % (settings.MEDIA_URL, self.image)

    def get_absolute_url(self):
        return "/%s" % self.image

    # for displaying thumbnail in change list
    def admin_thumbnail(self):
        return '<img src="' + self.image.url + '" width="100" />'
    admin_thumbnail.short_description = 'thumbnail'
    admin_thumbnail.allow_tags = True

'''
Blog Video (ripped off basic.models)
'''

class PostVideo(models.Model):
    """PostVideo model"""
    post = models.ForeignKey(Post)
    title = models.CharField(max_length=255)
    still = models.FileField(upload_to=blog_media_upload, blank=True)
    video = models.FileField(upload_to=blog_media_upload, db_index=True)
    description = models.TextField(blank=True)
    uploaded = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)
    license = models.ForeignKey(License, blank=True, null = True)
    created_by = models.CharField(max_length=100, blank=True)

    def embed_url(self):
        return '%s/%s' % (settings.MEDIA_URL , self.video)

    class Meta:
        db_table = 'blog_postvideo'
        verbose_name = 'video'
        ordering = ['-uploaded']

    def __unicode__(self):
        return '%s / %s' % (self.title, self.post.title)

    def get_absolute_url(self):
        return "/%s" % self.video

'''
Blog Audio (ripped off basic.models
'''
      
class PostAudio(models.Model):
    """PostAudio model"""
    post = models.ForeignKey(Post)
    title = models.CharField(max_length=255)
    still = models.FileField('thumb', upload_to=blog_media_upload, blank=True)
    audio = models.FileField(upload_to=blog_media_upload,db_index=True)
    description = models.TextField(blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    license = models.ForeignKey(License, blank=True, null = True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'blog_postaudio'
        verbose_name_plural = 'audio'
        ordering = ['-uploaded']

    def __unicode__(self):
        return '%s / %s' % (self.title, self.post.title)
        
    def embed_url(self):
        return '%s/%s' % (settings.MEDIA_URL , self.audio)
      
    def get_absolute_url(self):
        return "/%s" % self.audio


class PostFile(models.Model):
    """PostAudio model"""
    post = models.ForeignKey(Post)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=blog_media_upload,db_index=True)
    description = models.TextField(blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    license = models.ForeignKey(License, blank=True, null = True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'blog_postfile'
        verbose_name = 'file'
        ordering = ['-uploaded']

    def __unicode__(self):
        return '%s / %s' % (self.title, self.post.title)
    
    def get_absolute_url(self):
        return "/%s" % self.file

      
      
######

def get_featured_articles(limit):
    '''
    method to return all posts designated featured articles, used in rhizome news, etc
    '''
    return Post.objects.filter(featured_article = 1).filter(status = 2).order_by('-publish')[:limit]

