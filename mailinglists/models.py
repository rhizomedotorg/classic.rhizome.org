import datetime

import django.db.models.options as options
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from mailinglists.signals import *
from blog.models import Post
from artbase.models import MemberExhibition
from utils.helpers import clean_html

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('news_actions', 'member_newsletter_actions',)

class Newsletter(models.Model):
    post = models.ForeignKey(Post, db_index = True, limit_choices_to = {'featured_article':1})
    created = models.DateTimeField(null=False, editable=False)
    sent = models.DateTimeField(null=True, editable=False)
#    banner_image = models.ImageField(upload_to = 'editorial/newsletter/banner_images/',null=True,blank=True)
#    banner_artwork =  models.ForeignKey(ArtworkStub,null=False,db_index = True,null=True,blank=True)
    
    class Meta:
        ordering = ('-post',)
 
    def __unicode__(self):
        return u'%s created on %s and sent on %s' % (self.post, self.created, self. sent)
        
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        super(Newsletter, self).save(*args, **kwargs)
        
    def article(self):
        article =  Post.objects.get(pk = self.post_id)
        return article 
        
class List(models.Model):
    listowner = models.CharField(null=False, max_length=255,db_index = True)
    listemail = models.CharField(null=False, max_length=255,db_index = True)
    title = models.CharField(null=True, max_length=255)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_object = generic.GenericForeignKey()  
    description = models.CharField(max_length=255)
    display = models.BooleanField()
    
    def __unicode__(self):
        return '%s: %s' % (self.id, self.title)  

class Member(models.Model):
    '''
    this model is based off Rhizome's old email system, which didn't always match users to listserv members, and thus some of these instances aren't tied to Users. Ideally, this would be a manytomany field connected to Users. 
    '''
    user = models.ForeignKey(User, null=True,blank=True)
    listid = models.IntegerField(max_length = 11,db_index = True)
    email = models.CharField(null=False, max_length=255,db_index = True)
    created = models.DateTimeField(null=False, editable=False)
    confirmed = models.BooleanField()
    approved = models.BooleanField()
    deleted= models.BooleanField()
    delete_date = models.DateTimeField(null=True,blank=True)
    IP = models.CharField(null=True, max_length=31,blank=True)
    RH = models.CharField(null=True, max_length=255, blank=True)

    def get_list(self):
        mlist = List.objects.get(id = self.listid)
        return mlist

    def __unicode__(self):
        return '%s / %s' % (self.email, self.get_list())
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        super(Member, self).save(*args, **kwargs)  

class MLMessage(models.Model):
    '''
    this is to record messages sent to the various list and prevent accidental resending of messages
    '''
    user = models.ForeignKey(User, null=False)
    mllist = models.ForeignKey(List, null=False)
    content_type = models.ForeignKey(ContentType)  
    object_pk = models.IntegerField(max_length = 11,db_index = True)
    created = models.DateTimeField(null=False, editable=False)
    sent = models.BooleanField()
       
    def __unicode__(self):
        return 'From %s on %s and sent is %s' % (self.user, self.created, self.sent)   
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        super(MLMessage, self).save(*args, **kwargs) 

def member_newsletter_image(self, filename):
	return 'mailinglists/member_newsletter/%s/%s' % (self.id, filename.replace(" ", "-"))

class MemberNewsletter(models.Model):
    body = models.TextField()
    body_image = models.ImageField(upload_to = member_newsletter_image, null=True, blank=True)
    month =  models.DateField(null=False)
    created = models.DateTimeField(null=False, editable=False)
    sent = models.DateTimeField(null=True, editable=False)
    featured_exhibition = models.ForeignKey(MemberExhibition, null=True, blank=True)        

    class Meta:
        ordering = ('-created',)
     
    def __unicode__(self):
        return '%s' % self.month
        
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.body = clean_html(self.body)
        if not self.id:
            self.created = datetime.datetime.now()
        super(MemberNewsletter, self).save(*args, **kwargs)    
