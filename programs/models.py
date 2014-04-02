import os
from itertools import chain
from operator import attrgetter
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError

from countries.models import Country, UsState
from blog.models import Post


#this naming of dirs via the title is a BAD idea, and needs to be fixed. big mess on server.

def get_event_image_upload_to(self, filename):
    image_title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    return 'programs/rhizevent/%s/%s.%s' % (self.title.replace(" ", "-"),image_title.replace(" ", "-"),extension)

def get_exhibition_image_upload_to(self, filename):
    image_title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    return 'programs/exhibition/%s/%s.%s' % (self.title.replace(" ", "-"),image_title.replace(" ", "-"),extension)

def thumbnail_upload(instance, filename):
    image_title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    return '%s_thumbnail.%s' % (image_title.replace(" ", "-"), extension)

def get_exhibition_medium_upload(instance, filename):
    image_title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    return 'programs/exhibition/%s/%s_250x250.%s' % (instance.title.replace(" ", "-"), image_title.replace(" ", "-"), extension)

def get_event_medium_upload(instance, filename):
    image_title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    return 'programs/rhizevent/%s/%s_250x250.%s' % (instance.title.replace(" ", "-"), image_title.replace(" ", "-"), extension)



class RhizEvent(models.Model):
    #created_by = models.ForeignKey(User, null=False,editable=False)
    title = models.CharField(null=False, max_length=255)
    slug = models.SlugField(db_index=True, unique=True)    
    url = models.URLField(null=True, blank=True)
    media_link = models.URLField(help_text="For linking to external images, etc", null=True, blank=True)    
    tickets_link = models.URLField(null=True, blank=True)    
    summary = models.TextField(null=False,help_text="Can be description exercpt")
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to = get_event_image_upload_to, null=True, blank=True)
    thumbnail =  models.FileField(upload_to = thumbnail_upload,
                                        help_text = "100w x 100h (CREATED AUTOMATICALLY)",
                                        null=True,
                                        blank=True,
                                        )
    medium_image =  models.ImageField(upload_to = get_event_medium_upload,
                                        help_text = "250w x 250h",
                                        null=True,
                                        blank=True,
                                        )
    is_new_silent = models.BooleanField(_('Is this part of the New Silent Series?'), default=False,db_index = True)
    at_new_museum = models.BooleanField(_('Is this event at the New Museum?'), default=False,db_index = True)
    is_online = models.BooleanField(_('Does this event exist online?'), default=False,db_index = True)
    location_title = models.CharField(null=False, blank=True, max_length=255)
    location_street1= models.CharField(null=False, blank=True, max_length=255)
    location_street2= models.CharField(null=False, blank=True, max_length=255)
    location_city = models.CharField(null=False, blank=True, max_length=255)
    location_locality_province = models.CharField(_('Location Locality or Province (if applicable)'), 
            null=True,blank=True, max_length=255)
    zip_postal_code = models.IntegerField(null=True, blank=True, max_length=11)
    location_state = models.ForeignKey(UsState,to_field='name',null=True, blank=True)
    location_country = models.ForeignKey(Country,null=True,blank=True,)    
    location_url =  models.URLField(null=True, blank=True)
    start_date = models.DateTimeField(null=False)
    end_date =  models.DateTimeField(null=True,blank=True)
    created = models.DateTimeField(null=False, editable=False)   
    modified = models.DateTimeField(null=False, editable=False, auto_now=True)
    allow_comments = models.BooleanField(_('allow comments?'), default=True)
    curator = models.ManyToManyField(User, null=True, blank=True, related_name="event-curator")
    curator_other = models.TextField(_('Other Curator'), max_length=200, null=True, blank=True, 
            help_text=_('If no rhizome user or cannot create user account, like for an organization.'))
    curator_other_link = models.URLField(null=True, blank=True) 

    class Meta:
        verbose_name = _('Rhizome Event')
        verbose_name_plural = _('Rhizome Events')

    def __unicode__(self):
        return '%s on %s' % (self.title, self.start_date)
    
    def save(self, *args, **kwargs):
        ''' On save, strip html and update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        if self.at_new_museum == True:
            self.location_title = "the New Museum"
            self.location_street1 = "235 Bowery"
            self.location_city = "New York"
            self.zip_postal_code = "10002"
            self.location_url = "http://www.newmuseum.org/"
        super(RhizEvent, self).save(*args, **kwargs)

    def curators(self):
        return self.curator.all()

    def get_curators(self):
        return self.curator.all()
    
    curator.short_description = 'Curator(s)'
    
    def get_absolute_url(self):
        return '/events/%s/' % self.slug
    
    def video(self):
        video = Video.objects.get(related_event = self)
        if video:
            return video
        else:
            return None

def on_rhizevent_save(sender, **kwargs):
    instance = kwargs['instance']
    if instance.image and not instance.thumbnail:
        if os.path.exists(instance.image.path):
            from easy_thumbnails.files import get_thumbnailer
            thumbnail_options = dict(size=(100, 0))
            instance.thumbnail = get_thumbnailer(instance.image).get_thumbnail(thumbnail_options).file
            instance.save()
post_save.connect(on_rhizevent_save, sender=RhizEvent)
        
class Exhibition(models.Model):
    #created_by = models.ForeignKey(User, null=False,editable=False)
    title = models.CharField(null=False, max_length=255)
    slug = models.SlugField(_('slug'), unique_for_date='start_date', db_index=True,
            max_length=75, unique=True)
    url = models.URLField(null=True)
    description = models.TextField(null=False)
    image = models.ImageField(help_text="MUST SAVE BEFORE ADDING IMAGE!!!",
            upload_to = get_exhibition_image_upload_to, null=True, blank=True,max_length=200)
    artists = models.ManyToManyField(User,null=True,blank=True,related_name="exhibition-artists")
    artists_other = models.TextField(null=True,blank=True, help_text=_('If artist has no rhizome user acct.'))
    at_new_museum = models.BooleanField(_('Is this exhbition at the New Museum?'), default=True,db_index = True)
    is_online = models.BooleanField(_('Does this exhibition exist online?'), default=True,db_index = True)
    location_title = models.CharField(null=False, blank=True, max_length=255)
    location_street1= models.CharField(null=False, blank=True, max_length=255)
    location_street2= models.CharField(null=False, blank=True, max_length=255)
    location_city = models.CharField(null=False, blank=True, max_length=255)
    location_locality_province = models.CharField(_('Location Locality or Province (if applicable)'),
            null=True, blank=True, max_length=255)
    location_state = models.ForeignKey(UsState,to_field='name',null=True, blank=True)
    location_country = models.ForeignKey(Country,null=True,blank=True,)
    location_url =  models.URLField(null=True, blank=True)
    zip_postal_code = models.IntegerField(null=True, blank=True, max_length=11)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date =  models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=False, editable=False)   
    modified = models.DateTimeField(null=False, editable=False, auto_now=True)
    allow_comments = models.BooleanField(_('allow comments?'), default=True)
    curator = models.ManyToManyField(User,null=True,blank=True,related_name="exhibition-curator")
    media_link = models.URLField(help_text="For linking to external images, etc",null=True, blank=True)
    curator_other = models.CharField(_('Other Curator'), null=True, max_length=200, blank=True, 
            help_text=_('If no rhizome user or cannot create user account, like for an organization.'))
    curator_other_link = models.URLField(null=True, blank=True) 
    thumbnail =  models.FileField(upload_to = thumbnail_upload,
                                        help_text = "100w x 100h (CREATED AUTOMATICALLY)",
                                        null=True,
                                        blank=True,
                                        )
    medium_image =  models.ImageField(upload_to = get_exhibition_medium_upload,
                                        help_text = "250w x 250h (CREATED AUTOMATICALLY)",
                                        null=True,
                                        blank=True,
                                        )

    def __unicode__(self):
        return '%s on %s' % (self.title, self.start_date)

    def save(self, *args, **kwargs):
        ''' On save, strip html and update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        if self.at_new_museum == True:
            self.location_title = "the New Museum"
            self.location_address = "235 Bowery"
            self.location_city = "New York"
            self.location_url = "http://www.newmuseum.org/"
        super(Exhibition, self).save(*args, **kwargs)
    
    def curators(self):
        return self.curator.all()

    def get_curators(self):
        return self.curator.all()

    def get_absolute_url(self):
        return '/exhibitions/%s/' % self.slug
    
    def get_artists(self):
        return self.artists.all().iterator()
    
    class Meta:
        verbose_name = _('Rhizome Exhibition')
        verbose_name_plural = _('Rhizome Exhibitions')
    
    def video(self):
        video =  Video.object.get(related_exhibition = self)
        if video:
            return video
        else:
            return None
                    
    curator.short_description = 'Curator(s)'


def on_exhibition_save(sender, **kwargs):
    instance = kwargs['instance']
    if instance.image and not instance.thumbnail:
        if os.path.exists(instance.image.path):
            from easy_thumbnails.files import get_thumbnailer
            thumbnail_options = dict(size=(100, 0))
            instance.thumbnail = get_thumbnailer(instance.image).get_thumbnail(thumbnail_options).file
            instance.save()
post_save.connect(on_exhibition_save, sender=Exhibition)
        
class Video(models.Model):
    #created_by = models.ForeignKey(User, null=False,editable=False)
    title = models.CharField(null=False, max_length=255)
    related_event = models.ForeignKey(RhizEvent, null=True,blank=True)
    related_exhibition = models.ForeignKey(Exhibition,null=True,blank=True)
    related_post =  models.ForeignKey(Post,null=True,blank=True)
    url = models.URLField(_('URL for site related to video or video collection, not the url of the embed'),
            null=True, blank=True)
    image = models.ImageField(upload_to = 'programs/video/', null=True, blank=True)
    description = models.TextField(null=False)
    lead_video = models.TextField(_('EMBED CODE for the 1st or main video'),null=False)
    other_videos = models.TextField(_('EMBED CODE for ALL other videos here'),null=True, blank=True,
            help_text=_("Surround each video's embed code with HTML paragraph elements for spacing."))
    video_date = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=False, editable=False)   
    modified = models.DateTimeField(null=False, editable=False, auto_now=True)
    allow_comments = models.BooleanField(_('allow comments?'), default=True)
    
    class Meta:
        verbose_name = _('Rhizome Video')
        verbose_name_plural = _('Rhizome Videos')

    def __unicode__(self):
        return '%s' % (self.title)

    def save(self, *args, **kwargs):
        ''' On save, strip html and update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()                   
        super(Video, self).save(*args, **kwargs)

#the download
def get_download_image_upload_to(self, filename):
    extension = filename.split('.')[-1]
    return 'programs/the_download/%s/images/%s.%s' % (self.id, self.title.replace(" ","-").lower(), extension)

def get_download_artist_image_upload_to(self, filename):
    extension = filename.split('.')[-1]
    return 'programs/the_download/%s/images/%s.%s' % (self.id, self.artist_name.replace(" ","-").lower(), extension)

class DownloadOfTheMonth(models.Model):
    title = models.CharField(max_length=255) 
    artist_user_account = models.ForeignKey(User, null=True, blank=True, verbose_name='account')
    artist_name = models.CharField(max_length=255) 
    file_description_and_size = models.CharField('medium', max_length=255)
    about_artist = models.TextField()
    artist_url = models.URLField()
    work_description = models.TextField('description')
    work_instructions = models.TextField('instructions')
    is_active = models.BooleanField(db_index=True)
    premier_date = models.DateField()
    created = models.DateTimeField('created', null=False, editable=False)
    image = models.ImageField('main image', upload_to=get_download_image_upload_to, null=True, blank=True)
    artist_image = models.ImageField(upload_to=get_download_artist_image_upload_to, help_text='156x178', null=True, blank=True)

    class Meta:
        verbose_name = 'download'
        verbose_name_plural = 'The Download'
        ordering = ['-premier_date']

    def get_absolute_url(self):
        return "/the-download/%s/%s/" % (self.premier_date.year, self.premier_date.strftime('%b').lower())

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        self.title = self.title.strip()
        self.artist_name = self.artist_name.strip()
        super(DownloadOfTheMonth, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s: %s/%s" % (self.artist_name, self.premier_date.month, self.premier_date.year)

def download_file_file_upload_to(self, filename):
    filename = filename.replace(' ','-')
    return 'programs/the_download/%s/files/%s' % (self.download.id, filename)

class DownloadFile(models.Model):
    download = models.ForeignKey(DownloadOfTheMonth)
    file = models.FileField(upload_to=download_file_file_upload_to)
    title = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return '(~_~;)'

        
##########
# General query functions (this should probably be managers)
##########
def get_recent_events(limit = None):
    if limit:
        events = RhizEvent.objects.filter(start_date__lt = datetime.datetime.now()).exclude(image = None).exclude(image = '').order_by('-start_date')[:limit]
    else:
        events = RhizEvent.objects.filter(start_date__lt = datetime.datetime.now()).exclude(image = None).exclude(image = '').order_by('-start_date')
    return events

def get_upcoming_events(limit = None):
    if limit:
        events = RhizEvent.objects.filter(start_date__gte = datetime.datetime.now()).exclude(image = None).exclude(image = '').order_by('-start_date')[:limit]
    else:
        events = hizEvent.objects.filter(start_date__gte = datetime.datetime.now()).exclude(image = None).exclude(image = '').order_by('-start_date')
    return events

def get_recent_exhibitions(limit = None):
    if limit:
        exhibitions = Exhibition.objects.filter(start_date__lte = datetime.datetime.now()).order_by('-start_date')[:limit]
    else:
        exhibitions = Exhibition.objects.filter(start_date__lte = datetime.datetime.now()).order_by('-start_date')
    return exhibitions

def get_upcoming_events():
    return [event for event in RhizEvent.objects.all().order_by('-start_date') if event.start_date > datetime.datetime.now()]
    
def get_past_events():
    return [event for event in RhizEvent.objects.all().order_by('-start_date') if event.start_date < datetime.datetime.now()]    

def get_upcoming_exhibitions():
    return [exhibition for exhibition in Exhibition.objects.all().order_by('-start_date') if exhibition.start_date > datetime.datetime.now()]
    
def get_past_exhibitions():
    return [exhibition for exhibition in Exhibition.objects.all().order_by('-start_date') if exhibition.start_date < datetime.datetime.now()]    

def get_upcoming_programs():
    events = get_upcoming_events()
    exhibitions = get_upcoming_exhibitions()
    return sorted(chain(events, exhibitions),key=attrgetter('start_date'),reverse=True)
    

    
    
