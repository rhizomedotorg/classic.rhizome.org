from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import datetime
from django.utils.translation import ugettext_lazy as _
import simplejson as json
from paintstore.fields import ColorPickerField
from django.conf import settings

featured_object_choices = {'model__in':('post','rhizomeuser','artworkstub','rhizevent','exhibition','tag')}

def get_sidebar_upload_to(self, filename):
    title = self.title.replace(' ','-')
    extension = filename.split('.')[-1]
    #add check extension logic
    return 'frontpage/sidebar/images/%s.%s' % (title,extension)

class SidebarItem(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(help_text=('310 pixels width'),upload_to = get_sidebar_upload_to, null=True, blank=True)
    text = models.TextField(help_text = "Optional",blank=True,null=True)
    link = models.URLField()
    created = models.DateTimeField(null=False, editable=False)
    is_active =models.BooleanField(db_index=True)
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        super(SidebarItem, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.title

class FeaturedSet(models.Model):
    """
    Model for generating the featured content set on the front page / frontpage.html
    """    
    
    title = models.CharField(max_length=255)
    created = models.DateTimeField(null=True, editable=False)
    current = models.BooleanField(db_index = True)
        
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.now()
        super(FeaturedSet, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return u'%s: "%s" created on %s' % (self.id,self.title,self.created)

class FeaturedObject(models.Model):
    """
    Model for generating featured objects for the featured set
    """
    featured_set = models.ForeignKey(FeaturedSet)
    content_type = models.ForeignKey(ContentType, limit_choices_to=featured_object_choices, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    content_object = generic.GenericForeignKey('content_type','object_id')
    image = models.ImageField(upload_to='frontpage/images/', null=True, blank=True, help_text='300px high')
    title = models.CharField(max_length=40, blank=True, null=True) 
    description = models.CharField(max_length=225, blank=True, null=True) 
    byline = models.CharField(max_length=60, blank=True, null=True) 
    url = models.URLField(blank=True, null=True)

    title_color = ColorPickerField(max_length=40, blank=True, null='')
    text_color = ColorPickerField(max_length=40, blank=True, null='')
    byline_color = ColorPickerField(max_length=40, blank=True, null='')

    def __unicode__(self):
        return self.get_title()

    def get_title(self):
        if self.title:
            return self.title
        if hasattr(self.content_object, 'subtitle'):
            if self.content_object.subtitle:
                return self.content_object.subtitle
        return self.content_object.title

    def get_byline(self):
        if self.byline:
            return ('#', self.byline)

        if self.ct == 'artworkstub':
            return (self.content_object.user.get_profile().get_absolute_url(), self.content_object.get_artist())

        if self.ct == 'post':
            authors = self.content_object.get_authors()
            if authors:
                return (authors[0].get_profile().get_absolute_url(), authors[0].get_profile()) 
            return ('', self.content_object.byline)

        if self.ct in ['rhizevent', 'exhibition']:
            curators = self.content_object.curator.all()
            if curators:
                return (curators[0].get_profile().get_absolute_url(), curators[0].get_profile())
            return (self.content_object.curator_other_link, self.content_object.curator_other)
            

    def get_description(self):
        if self.description:
            return self.description

        if self.ct == 'artworkstub':
            if self.content_object.summary:
                return self.content_object.summary
            return self.content_object.description

        if self.ct == 'rhizomeuser':
            return self.content_object.description

        if self.ct == 'post':
            return self.content_object.tease

        if self.ct == 'exhibition':
            return self.content_object.description

        if self.ct == 'rhizevent':
            return self.content_object.summary

"""
methods for getting featured objects
"""
def get_featured_objects():
    featured_set = None
    featured_sets = FeaturedSet.objects.filter(current=True).order_by('created')
    if featured_sets:
        featured_set = featured_sets[0]
    return FeaturedObject.objects.filter(featured_set=featured_set).order_by('id')
    
def get_featured_objects_list():
    '''
    returns featured objects as a list for frontpage
    '''
    featured_objects = get_featured_objects()       
    featured_objects_list = []
    
    for obj in featured_objects:
        try: 
            if obj.content_type_id:
                #has object foreign key, configure item in list based on object type
                ct = ContentType.objects.get_for_id(obj.content_type_id)
                object_data = ct.model_class()._default_manager.get(pk=obj.object_id) 
                
                if ct.name == 'rhizome user':
                    if not obj.icon: 
                        if object_data.image:
                            image = "%s%s" % (settings.MEDIA_URL, object_data.image)
                        else:
                            image = '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL)
                    else:
                        image = "%s%s" % (settings.MEDIA_URL,obj.icon)
                     
                    obj.pk = object_data.id
                    obj.ct = "rhizomeuser" #call it this to avoid spaces
                    obj.image = image
                    obj.url = object_data.get_absolute_url()
                        
                elif ct.name == 'artwork stub':
                    if not obj.image: 
                        if object_data.image_medium:
                            image = "%s%s" % (settings.MEDIA_URL, object_data.image_medium)
                        else:
                            image = '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL) 
                    else:
                        image = "%s%s" % (settings.MEDIA_URL,obj.image)
                        
                    obj.pk = object_data.id
                    obj.ct = 'artworkstub' #call it this to avoid spaces
                    obj.image =  image
                    obj.url = object_data.view_url()
        
                elif ct.name == "post":
                    if obj.image:
                        image = "%s%s" % (settings.MEDIA_URL, obj.image)
                    else:
                        image =  '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL)
                    
                    obj.pk = object_data.id,
                    obj.ct = "post"
                    obj.image = image
                    obj.url = object_data.get_absolute_url()
                
                elif ct.name == "rhiz event":
                    if not obj.image: 
                        if object_data.image:
                            image = "%s%s" % (settings.MEDIA_URL, object_data.image)
                        else:
                            image =  '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL)
                    else:
                        image = "%s%s" % (settings.MEDIA_URL,obj.image)
                    
                    obj.pk = object_data.id,
                    obj.ct = "rhizevent"
                    obj.image = image
                    obj.url = object_data.get_absolute_url()
                
                elif ct.name == 'exhibition':
                    from programs.models import Exhibition
                    
                    if not obj.image: 
                        if object_data.image:
                            image = "%s%s" % (settings.MEDIA_URL, object_data.image)
                        else:
                            image = '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL)
                    else:
                        image = "%s%s" % (settings.MEDIA_URL, obj.image)
                    
                    obj.image = image
                    obj.ct = ct.name
                    obj.url = object_data.get_absolute_url()
        
                else:
                    if not obj.image: 
                        if object_data.image:
                            image = "%s%s" % (settings.MEDIA_URL, object_data.image)
                        else:
                            image = '%sartbase/images/rhizome_art_default.png' % (settings.MEDIA_URL)
                    else:
                        image = "%s%s" % (settings.MEDIA_URL,obj.image)
        
                    obj.pk = object_data.id
                    obj.ct = ct.name
                    obj.image = image
                    obj.url = object_data.get_absolute_url()
            else:
                #no foriegn key
                obj.image = '%s%s' % (settings.MEDIA_URL, obj.image)
            
            featured_objects_list.append(obj)
        except:
            pass
            
    return featured_objects_list