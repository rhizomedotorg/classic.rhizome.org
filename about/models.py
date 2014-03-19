import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags

from countries.models import Country, UsState
from utils.helpers import clean_html

class StaffMember(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    position = models.CharField(max_length = 100)
    bio = models.TextField()
    email = models.EmailField()
    url =  models.URLField(max_length = 255,null=True,blank=True)
    
    def __unicode__(self):
        return '%s' % (self.email)


    def save(self, *args, **kwargs):
        ''' On save, clean HTML '''
        self.bio = clean_html(self.bio)
        super(StaffMember, self).save(*args, **kwargs)
    
def press_upload_to(self, filename):
    title = filename.split('.')[0]
    extension = filename.split('.')[-1]
    #add check extension logic
    self.image = 'about/press/%s.%s' % (title,extension)
    return 'about/press/%s.%s' % (title,extension)

class Press(models.Model):
    publication = models.CharField(max_length = 255)
    article_title =  models.CharField(max_length = 255)
    article_url = models.URLField(max_length = 255)
    publication_date = models.DateField()
    excerpt = models.TextField()
    article_full_text = models.TextField(null=True, blank=True)
    document = models.FileField(null=True, blank=True,upload_to = press_upload_to)
    
    def __unicode__(self):
        return '%s on %s' % (self.publication, self.publication_date)
    
    class Meta:
        verbose_name = "Press Clipping"
        verbose_name_plural = "Press Clippings"
        
    def save(self, *args, **kwargs):
        ''' On save, clean HTML '''
        self.excerpt = clean_html(self.excerpt)
        self.article_full_text = clean_html(self.article_full_text)
        super(Press, self).save(*args, **kwargs)
