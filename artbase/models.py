from __future__ import division

import datetime
import os 
from operator import attrgetter

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist

import tagging
import logging

#couchdb
from couchdb.client import *
from couchdb.mapping import *

from easy_thumbnails.fields import ThumbnailerImageField
from utils.helpers import clean_html
from utils.model_document import ModelDocument
from tagging.models import Tag, TaggedItem
from tagging.fields import TagField
from django.conf import settings

logger = logging.getLogger('django')

#couchdb connection
server = Server(settings.COUCH_SERVER)
try:
    db = server['artbase']
except Exception:
    try:
        db = server.create('artbase')
    except Exception:
        logger.error('Could not access or create artbase CouchDB database')

LICENSE_TYPES = (
    ('software','software'),
    ('creative_commons','creative_commons'),
    ('all_rights_reserved','all_rights_reserved'),
    ('public_domain','public_domain') 
)

def artbase_document_upload(instance, filename):
    extension = filename.split('.')[-1]
    return 'artbase/documents/%s.%s' % (instance.title.replace(' ', '-'), extension)

class License(models.Model):
    slug =  models.CharField(max_length=255, default = "arr")
    title = models.CharField(max_length=255,  default = "All Rights Reserved")
    url = models.URLField()
    image = models.URLField(blank=True, null=True)
    type = models.CharField(_('Type of License'),
                            max_length=50,
                            choices=LICENSE_TYPES,
                            null=True,
                            blank=True,
                            db_index = True)
    
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.slug)

class ArtbaseDocument(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    file = models.FileField(upload_to=artbase_document_upload)
    cover_image = models.ImageField(upload_to='artbase/documents/cover_images/')
    uploaded = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    published = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'ArtBase Documents'
        ordering = ['-published']

    def __unicode__(self):
        return '%s by %s' % (self.title, self.author)

class AboutArtbase(models.Model):
    mission = models.TextField()
    archival_process = models.TextField()
    philosophy = models.TextField()
    selection_criteria = models.TextField()
    current_projects = models.TextField()
    access_membership = models.TextField()

    def get_absolute_url(self):
        return "/artbase/about/"

    def get_documents(self):
        return self.documents.all().order_by('-published')
    
    
    def save(self, *args, **kwargs):
        ''' On save, clean HTML '''
        self.mission = clean_html(self.mission)
        self.archival_process = clean_html(self.archival_process)
        self.access_membership = clean_html(self.access_membership)
        self.philosophy = clean_html(self.philosophy)
        self.selection_criteria = clean_html(self.selection_criteria)
        self.current_projects = clean_html(self.current_projects)
        super(AboutArtbase, self).save(*args, **kwargs)

    def __unicode__(self):
        return 'About the Rhizome Artbase'
    
    class Meta:
        verbose_name = "About"
        verbose_name_plural = "About"
    
# =================
# = ArtBase Model =
# =================

class ArtBaseModel(models.Model):
    """
    Abstract base model for all artbase models. Provides the created
    and modified field and related behaviors as well as the updates
    on model save. Django abstract base models just remove the boilerplate.
    It's important to declare it as abstract otherwise you'll run into
    lots of problems. - David
    """
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False, blank=True)

    class Meta:
        abstract = True
    
    def save(self):
        if not self.id:
            self.created = datetime.datetime.now()
        if not self.created:
            self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        super(ArtBaseModel, self).save()
        

class ExternalCollection(ArtBaseModel):
    name = models.CharField(max_length=1024)
    description = models.TextField()
    relationship = models.TextField()
    url = models.URLField()
    
    def __unicode__(self):
        return "%s" % self.name


class ExternalCollectionWork(ArtBaseModel):
    work = models.ForeignKey("ArtworkStub")
    collection = models.ForeignKey(ExternalCollection)
    date_submitted = models.DateTimeField(blank=True, null=True)
    submitted = models.BooleanField()

    def __unicode__(self):
        return "%s -> %s" % (self.work.title, self.collection.name)

class Title(ArtBaseModel):
    display_string = models.CharField(max_length=1024)


class Name(ArtBaseModel):
    display_string = models.CharField(max_length=1024)
    

class Material(ArtBaseModel):
    display_string = models.CharField(max_length=1024)
    category = models.CharField(max_length=1024)
    type = models.CharField(max_length=1024)
    version = models.CharField(max_length=1024)


class Technique(ArtBaseModel):
    display_string = models.CharField(max_length=1024)

class Technology(ArtBaseModel):
    '''
    Rhizome's controlled vocabulary for technologies
    '''
    display_string = models.CharField(max_length=1024)
    category = models.CharField(max_length=1024)
    type = models.CharField(max_length=1024)
    version = models.CharField(max_length=1024)

    class Meta:
        verbose_name = _('ArtBase Technology')
        verbose_name_plural = _('ArtBase Technologies')

    def __unicode__(self):
        return "%s" % self.display_string

class WorkType(ArtBaseModel):
    '''
    Rhizome's controlled vocabulary for work_types
    '''
    work_type = models.CharField(max_length=1024)

    class Meta:
        verbose_name = _('Work Type')
        verbose_name_plural = _('Work Types')

    def __unicode__(self):
        return "%s" % self.work_type


class Concept(ArtBaseModel):
    display_string = models.CharField(max_length=1024)

class Subject(ArtBaseModel):
    display_string = models.CharField(max_length=1024)

class Role(ArtBaseModel):
    display_string = models.CharField(max_length=1024)
    
# =========
# = Works =
# =========

WORK_IMAGE_SIZES = {
    "old_thumb_small": "_thumbnail40x51.gif",
    "old_thumb_med": "_thumbnail50x63.gif",
    "old_thumb_large": "_thumbnail62x85.gif",
    "old_med": ".gif",
    }

STATUS_CHOICES = (
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('awaiting', 'Awaiting'),
    ('unsubmitted', 'Unsubmitted'),
    ('deleted', 'Deleted'),
    ('to_consider', 'To Consider'),
)

LOCATION_TYPE_CHOICES = (
    ('linked', 'Linked'),
    ('cloned', 'Cloned')
    )

def featured_upload_to(self, filename):
    current = ArtworkStub.objects.get(id=self.id)
    if current.image_featured != self.image_featured:
        if os.path.exists(current.image_featured.path) and "rhizome_art_default.png" not in current.image_featured.path:
            os.remove(current.image_featured.path)  
    extension = filename.split('.')[-1]
    return 'artbase/images/%s_image_featured.%s' % (self.id,extension)
    

def large_upload_to(self, filename):
    current = ArtworkStub.objects.get(id=self.id)
    if current.image_large != self.image_large:
        if os.path.exists(current.image_large.path) and "rhizome_art_default.png" not in current.image_large.path:
            os.remove(current.image_large.path)  
    extension = filename.split('.')[-1]
    return 'artbase/images/%s_image_large.%s' % (self.id,extension)
    

def medium_upload_to(self, filename):
    current = ArtworkStub.objects.get(id=self.id)
    if current.image_medium != self.image_medium:
        if os.path.exists(current.image_medium.path) and "rhizome_art_default.png" not in current.image_medium.path:
            os.remove(current.image_medium.path)  
    extension = filename.split('.')[-1]
    return 'artbase/images/%s_image_medium.%s' % (self.id,extension)
    

def small_upload_to(self, filename):
    current = ArtworkStub.objects.get(id=self.id)
    if current.image_small != self.image_small:
        if os.path.exists(current.image_small.path) and "rhizome_art_default.png" not in current.image_small.path:
            os.remove(current.image_small.path)  
    extension = filename.split('.')[-1]
    return 'artbase/images/%s_image_small.%s' % (self.id,extension)    

def get_arr():
    return License.objects.get(slug = "arr")
    
    
    
# TODO: need to think of reconciling the document and the ArtworkStub - David
class ArtworkStub(ArtBaseModel):

    """
    The artwork MySQL stub. This model should be considered read only.
    """
    from django.contrib.auth.models import User
    user = models.ForeignKey(User, related_name="artworks")

    title = models.CharField(max_length=1024, blank=True, null=True)
    byline = models.CharField(max_length=200, blank=True, null=True)

    technologies = models.ManyToManyField(Technology, null=True, blank=True)
    work_type    = models.ForeignKey(WorkType, null=True, blank=True)

    summary = models.TextField(blank=True, null=True, max_length=400)
    statement = models.TextField(blank=True, null=True)
    readme = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    image_featured = ThumbnailerImageField(upload_to = featured_upload_to,
                                           blank     = True,
                                           default   = "artbase/images/rhizome_art_default.png",
                                           resize_source=dict(size=(950, 375), crop='smart', quality=99),
                                           help_text = "Wide Featured Image: 950w x 375h px")
    
    image_large= ThumbnailerImageField(upload_to =  large_upload_to,
                                       blank     = True,
                                       resize_source=dict(size=(1024, 768), crop='smart', quality=99),
                                       default   = "artbase/images/rhizome_art_default.png",
                                       help_text = "Full Screen Image: 1024w x 768h px")

    image_medium = ThumbnailerImageField(upload_to = medium_upload_to,
                                         blank     = True,
                                         default   = "artbase/images/rhizome_art_default.png",
                                         resize_source=dict(size=(470, 355), crop='smart', quality=99),
                                         help_text = "Main Image: 470w x 355h px")

    image_small = ThumbnailerImageField(upload_to = small_upload_to,
                                        blank     = True,
                                        default   = "artbase/images/rhizome_art_default.png",
                                        resize_source=dict(size=(135, 170), crop='smart', quality=99),
                                        help_text = "Thumbnail: 135w x 170h px")
    
    license       = models.ForeignKey(License, null=True, blank=True, default = get_arr)
    url           = models.URLField(blank=True, null=True, max_length = 300)
    location      = models.URLField(blank=True,  max_length = 300, null=True)
    location_type = models.CharField(max_length=16, choices=LOCATION_TYPE_CHOICES, blank=True, null=True)

    agree_to_agreement = models.NullBooleanField(default=False)

    allow_comments = models.BooleanField(_('allow comments'), default=True,blank=True)
    needs_repair   = models.BooleanField(_('needs repair'), default=False,blank=True)


    approved_date  = models.DateTimeField(null=True, blank=True)
    submitted_date = models.DateTimeField(null=True, blank=True)
    

    status = models.CharField(max_length = 300,
                              choices    = STATUS_CHOICES,
                              blank      = True,
                              default    = "unsubmitted",
                              db_index   = True)
    
    external_collections = models.ManyToManyField(ExternalCollection, null=True, blank=True,through='ExternalCollectionWork')

    tags = TagField(max_length=1024, null=True, blank=True)

    worked_with   = models.CharField(max_length=1024, null=True, blank=True)
    created_date  = models.DateTimeField(null=True, blank=True) #date the work was actually created by the artist
    notices       = models.CharField(max_length=1024, null=True, blank=True)
    format        = models.CharField(max_length=1024, null=True, blank=True)
    state_ed      = models.CharField(max_length=1024, null=True, blank=True)
    collective    = models.CharField(max_length=1024, null=True, blank=True)
    other_artists = models.CharField(max_length=1024, null=True, blank=True)
    tech_details  = models.TextField(null=True, blank=True)
    completion_percentage = models.FloatField(null=True,blank=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('Artwork')
        verbose_name_plural = _('Artworks')

    def __unicode__(self):
        return self.title
        
    def tally_completion_percentage(self):
        #####
        # Eventually this should be turned into something comprehensive, but this will do for now. 
        #####
        completed_fields = 0
        total_fields = 0
        for attr, value in self.__dict__.iteritems():
            if attr == "notices" or attr == "collective" or attr == "readme" \
            or attr == "worked_with" or attr == "allow_comments" or attr == "other_artists" \
            or attr == "tech_details":
                pass
            else:
                total_fields += 1
                if value:
                    completed_fields += 1
                if "image" in attr:
                    if "rhizome_art_default.png" in "%s" % value:
                        completed_fields -= 1
                if not value or value == "":
                    completed_fields -= 1            
        percent_complete = round((completed_fields / total_fields), 2) * 100
        return percent_complete
        
    def is_halfway_complete(self):
        if float(self.completion_percentage) >= 50.0:
            return True
        else:
            return False
        
    def save(self, **kwargs):
        if not self.byline:
            self.byline = self.user.get_profile()
        self.completion_percentage = self.tally_completion_percentage()
        if not self.created_date:
            self.created_date = self.created
        if not self.license:
            self.license = get_arr()
            license = dict(
                title = "%s" % self.license.title,
                slug = "%s" % self.license.slug,
                url = "%s" % self.license.url,
                image = "%s" % self.license.image
            )    
            
        new = not self.id 
        doc = self.get_document()
        super(ArtworkStub, self).save(**kwargs)
        if new or not doc:
            self.create_document()

    def remove(self, **kwargs):
        self.status = "deleted"
        self.save()

    def artist(self):
        # TODO: update to return byline
        try:
            return self.user
        except:
            return None
        
    def get_status(self):
        return "%s" % self.status
    
    def get_document(self):
        #return Artwork.load(db, str(self.id))
        return Artwork.objects.get(pk=str(self.id))#use django like syntax established in utils/model_document.py
        
    def create_document(self):
        '''
        creates a couchdb document for the relevant artwork stub
        '''
        new_doc_d = { "titles" : [{"display_string": self.title}],
                      "url": self.url,
                      "summary": self.summary,
                      "created": self.created_date,
                      "description": self.description,
                      "creators" : [{"name": {"display_string": self.user.__unicode__(),
                                              "name_authority": "Rhizome"},
                                     "user_id": self.user.id,
                                     "roles": "primary creator"}],
                      "license" : [{"title": "%s" % self.license.title,
                                    "slug" : "%s" % self.license.slug,
                                    "url" : "%s" % self.license.url,
                                    "image" : "%s" % self.license.image,
                                    }]
                    }
        new_doc = Artwork(**new_doc_d)
        new_doc.id = str(self.id)
        new_doc.save()
        return new_doc

    def sync_document(self):
        '''
        syncs a stub and it's couchdb document
        '''
        document = self.get_document()
        if document:
            if not document.agree_to_agreement or document.agree_to_agreement == "null" \
            or document.agree_to_agreement != self.agree_to_agreement and self.agree_to_agreement:
                document.agree_to_agreement = self.agree_to_agreement

            if not document.dates.start or document.dates.start == "null" \
            or document.dates.start != self.created_date and self.created_date:
                document.dates.start = self.created_date

            if not document.publish_date or document.publish_date == "null" \
            or document.publish_date != self.submitted_date and self.submitted_date:
                document.publish_date = self.submitted_date
            
            if not document.approved_date or document.approved_date == "null" \
            or document.approved_date != self.approved_date and self.approved_date:
                document.approved_date = self.approved_date
            
            if not document.byline or document.byline == "null" \
            or document.byline != self.byline and self.byline:
                document.byline = self.byline

            if not document.created or document.created == "null" \
            or document.created != self.created and self.created:
                document.created = self.created
            
            if not document.description or document.description == "null" \
            or document.description != self.description and self.description:
                document.description = self.description            
            
            if not document.format or document.format == "null" \
            or document.format != self.format and self.format:
                document.format = self.format  
             
            if not document.summary or document.summary == "null" \
            or document.summary != self.summary and self.summary:
                document.summary = self.summary  

            if not document.statement or document.statement == "null" \
            or document.statement != self.statement and self.statement:
                document.statement = self.statement  
           
            if not document.image_featured or document.image_featured == "null" \
            or document.image_featured != self.image_featured and self.image_featured:
                document.image_featured = self.image_featured  

            if not document.image_large or document.image_large == "null" \
            or document.image_large != self.image_large and self.image_large:
                document.image_large = self.image_large  

            if not document.image_medium or document.image_medium == "null" \
            or document.image_medium != self.image_medium and self.image_medium:
                document.image_medium = self.image_medium  

            if not document.image_small or document.image_small == "null" \
            or document.image_small != self.image_small and self.image_small:
                document.image_small = self.image_small  

            if not document.location or document.location == "null" \
            or document.location != self.location and self.location:
                document.location = self.location  

            if not document.location_type or document.location_type == "null" \
            or document.location_type != self.location_type and self.location_type:
                document.location_type = self.location_type  

            if not document.user_id or document.user_id == "null" \
            or document.user_id != self.user_id and self.user_id:
                document.user_id = self.user_id

            if not document.mat_techs or document.mat_techs == "null" \
            or document.mat_techs != self.get_technologies() and self.get_technologies():
                techs = self.get_technologies()
                tech_list = []
                for tech in techs:
                    d = {
                        "display_string": "%s" % tech.display_string,
                        "concept_authority":"Rhizome",
                        "concept_authority_id": "1",
                        "type": "%s" % tech.type,
                    }
                    tech_list.append(d)
                document.mat_techs = tech_list
            
            if not document.license or document.user_id == "null" \
            or document.user_id != self.license and self.license:
                document.license = self.license.title         
            
            if not document.readme or document.readme == "null" \
            or document.readme != self.readme and self.readme:
                document.readme = self.readme  

            if not document.status or document.status == "null" \
            or document.status != self.status and self.status:
                document.status = self.status  

            if not document.url or document.url == "null" \
            or document.url != self.url and self.url:
                document.url = self.url  
            
            if self.work_type:
                if not document.work_types or document.work_types == "null":
                    document.work_types = []
                    work_dict = {
                        "concept_authority":      "Rhizome",
                        "concept_authority_id":   1,
                        "display_string":         "%s" % self.work_type.work_type,
                        "eff_date":               datetime.datetime.now(),
                        "type":                   "%s" % self.work_type.work_type,
                        "preferred":              True
                    }

                    document.work_types.append(work_dict) 


                for item in document.work_types:
                    if item and item["concept_authority"] == "Rhizome":
                        if item["type"] != self.work_type.work_type:
                            item["type"] = "%s" % self.work_type.work_type
                            item["display_string"] = "%s" % self.work_type.work_type
                            item["eff_date"] = datetime.datetime.now()
                    #document.save()

    def view_url(self):
        if self.status == "approved":
            return "/artbase/artwork/%s/" % self.id
        else:
            return "/portfolios/artwork/%s/" % self.id
                    
    def get_absolute_url(self):
        return "/artbase/artwork/%s" % self.id
    
    def edit_url(self):
        return "/artbase/artwork/%s/edit/" % self.id

    def get_location_admin(self):
        return '<a href="%s" target="_blank">%s</a>' % (self.location,self.location)
        
    get_location_admin.short_description = 'Location'
    get_location_admin.allow_tags = True


    #TAGS
    def get_tags(self):
        """
        To get at the actual list of tags and not just the comma or
        or space separated string
        """
        return Tag.objects.get_for_object(self)
    
    def get_approved_tags(self):
        """
        returns list of approved tag objects for artwork
        """
        ctype = ContentType.objects.get_for_model(self)
        approved =[]
        for tag in TaggedItem.objects.filter(content_type__pk=ctype.id, object_id=self.id, approved=True):
            try:
                approved.append(tag.tag)
            except:
                pass
        return approved
                
    def get_approved_tags_relationships(self):
        """
        returns list of approved tag relationships (taggeditems) for artwork
        """
        ctype = ContentType.objects.get_for_model(self)
        approved_rels =[]
        for tag in TaggedItem.objects.filter(content_type__pk=ctype.id, object_id=self.id, approved=True):
            try:
                approved_rels.append(tag.tag)
            except:
                pass
        return approved_rels

    def get_artist_tags(self):
        """
        returns list of user (not approved) tag objects for artwork
        """
        ctype = ContentType.objects.get_for_model(self)
        artist_tags =[]
        for tag in TaggedItem.objects.filter(content_type__pk=ctype.id, object_id=self.id, approved=False):
            try:
                artist_tags.append(tag.tag)
            except:
                pass
        return artist_tags
                                    
    def get_artist_tags_relationships(self):
        """
        returns list of user (not approved) tag relationships (taggeditems) for artwork
        """
        ctype = ContentType.objects.get_for_model(self)
        artist_tags_rels =[]
        for tag in TaggedItem.objects.filter(content_type__pk=ctype.id, object_id=self.id, approved=False):
            try:
                artist_tags_rels.append(tag.tag)
            except:
                pass
        return artist_tags_rels
   
    def get_related_works(self, limit=None):
        related_works_list = []
        related_works_list_append = related_works_list.append
        if limit:
            related_works = TaggedItem.objects.get_related(self, self.__class__, limit+5)
            for work in related_works:
                if work.image_medium != "artbase/images/rhizome_art_default.png" \
                and work.status != "accepted" and work.status != "deleted":
                    related_works_list_append(work)
                    if len(related_works_list) == limit:
                        return related_works_list
        else:
            related_works = TaggedItem.objects.get_related(self, self.__class__, 100)
            for work in related_works:
                if work.image_medium != "artbase/images/rhizome_art_default.png" \
                and work.status != "unsubmitted" and work.status != "deleted":
                    related_works_list_append(work)
                    if len(related_works_list) == 5:
                        return related_works_list
            
    def content_type(self):
        ct = ContentType.objects.get_for_model(self)
        return ct
    
    def content_type_id(self):
        ct = ContentType.objects.get_for_model(self)
        return ct.id
        
    def get_artist(self):
        if self.byline:
            return self.byline
        return self.user.get_profile()

    def get_audio(self):
        """
        To get at the audio media associated with the artwork
        """
        return Audio.objects.filter(work = self)

    def get_video(self):
        """
        To get the video media associated with the artwork
        """
        return Video.objects.filter(work = self)
        
    def get_technologies(self):
        return self.technologies.all()

    def get_saved_by(self):
        from accounts.models import RhizomeUser
        return RhizomeUser.objects \
            .filter(saved_artworks__id = self.id) \
            .filter(is_active = True) \
            .filter(visible=True)
        
    def get_collection_fragment_url(self):
        return "/artbase/collections/artwork/%s/fragment.html" % self.id
                    
try:
    tagging.register(ArtworkStub,tag_descriptor_attr="artwork_stub")
except tagging.AlreadyRegistered:
    # http://code.google.com/p/django-tagging/issues/detail?id=128 
    # Not sure the right way to register a model for tagging b/c it
    # raises this error if registered more than once. We end up registering
    # the first time during "manage.py syncdb" and then a second time when
    # actually attempting to run the site.
    pass

def on_stub_save(sender, **kwargs):
    #
    # happens whenever someone saves, this could be refined to work with status changes instead
    #
    instance = kwargs['instance']
    if instance.status != "unsubmitted" or instance.status != "deleted":
        instance.user.get_profile().add_points_for_object(instance)
        instance.sync_document()
post_save.connect(on_stub_save, sender=ArtworkStub)

# TODO: return a wrapped object
class ArtworkManager():
    """
    A helper so that we have the basic bits of the Django
    API when interacting with CouchDB.
    """
    def get(self, **args):
        pk = args.get("pk")
        if pk:
            return db[str(pk)]
        return None



class Artwork(ModelDocument):
    class Meta:
        model = ArtworkStub
        try:
            db = db
        except Exception:
            logger.error('Could not access or create artbase CouchDB database')

    # ==================================================
    # Views

    by_tag = ViewField("artworks", """function(doc) {
      for(var i = 0, len = doc.tags.length; i < len; i++) {
        emit(doc.tags[i], doc._id);
      }
    }""")

    # ==================================================
    # Fields

    created  = DateTimeField()
    modified = DateTimeField()

    # Ward Fields

    titles = ListField(DictField(Mapping.build(
                display_string = TextField(),
                type           = TextField(),
                source         = DictField(Mapping.build(
                                     source_authority = TextField(),
                                     range            = TextField()
                                     ))
                )))
    work_types = ListField(DictField(Mapping.build(
                     concept_authority    = TextField(),
                     concept_authority_id = IntegerField(),
                     display_string       = TextField(),
                     eff_date             = DateTimeField(),
                     type                 = TextField(),
                     preferred            = BooleanField()
                     )))

    creators = ListField(DictField(Mapping.build(
                   name    = DictField(Mapping.build(
                                 name_authority    = TextField(),
                                 name_authority_id = IntegerField(),
                                 display_string    = TextField()
                                 )),
                   email = TextField(),
                   user_id = IntegerField(),
                   roles   = TextField(),
                   attrs   = TextField(),
                   xts     = TextField(),
                   )))

    collective = DictField(Mapping.build(
                     name_authority   = TextField(),
                     name_athority_id = IntegerField(),
                     display_string   = TextField()
                     ))
    mat_techs = ListField(DictField(Mapping.build(
                    display_string       = TextField(),
                    concept_authority    = TextField(),
                    concept_authority_id = IntegerField(),
                    type                 = TextField(),
                    color                = TextField(),
                    xt                   = TextField(),
                    source               = DictField(Mapping.build(
                                               source_authority = TextField(),
                                               range            = TextField(),
                                               ))
                    )))
    state_ed = DictField(Mapping.build(
                   type      = TextField(),
                   qualifier = TextField(),
                   number    = TextField(),
                   total     = TextField(),
                   name      = TextField(),
                   source    = DictField(Mapping.build(
                                   source_authority = TextField(),
                                   range            = TextField(),
                                   ))
                   ))
    
    styles    = TextField()
    
    subjects  = ListField(DictField(Mapping.build(
                             concept_authority    = TextField(),
                             concept_authority_id = IntegerField(),
                             display_string       = TextField(),
                             xt                   = TextField(),
                             type                 = TextField(),
                             )))

    # Rhizome Fields

    user_id = IntegerField()
    other_artists =  ListField(DictField(Mapping.build(
                                   index               = IntegerField(),
                                   name                = TextField(),
                                   role                = TextField(),
                                   email               = TextField(),
                                   rhizome_user_id     = IntegerField(),
                                   rhizome_profile_url = TextField(),
                                   )))
    
    image_featured = TextField()
    image_small    = TextField()
    image_medium   = TextField()
    image_large    = TextField()

    last_edit_by = IntegerField()
    byline       = TextField()
    summary      = TextField()
    description  = TextField()
    statement    = TextField()
    articles = ListField(DictField(Mapping.build(
                             title       = TextField(),
                             author      = TextField(),
                             date        = DateField(),
                             publication = TextField(),
                             link        = TextField(),
                             )))

    support =  ListField(DictField(Mapping.build(
                             title      = TextField(),
                             benefactor = TextField(),
                             amount     = TextField(),
                             date       = DateField(),
                             )))

    license = TextField()
    notices = TextField()
    readme  = TextField()
    format  = TextField()
    media   = ListField(IntegerField())
    footnotes =  ListField(DictField(Mapping.build(
                               title = TextField(),
                               link  = TextField()
                               )))

    dates = DictField(Mapping.build(
                start = DateTimeField(),
                end   = DateTimeField()
                ))
    agree_to_agreement = BooleanField();
    tags               = ListField(TextField())
    rhiz_tags          = ListField(TextField())
    exhibitions = ListField(DictField(Mapping.build(
                                title    = TextField(),
                                location = TextField(),
                                date     = DateField(),
                                curator  = TextField(),
                                link     = TextField()
                                )))
    audio = ListField(DictField(Mapping.build(
                          audio_id  = IntegerField(),
                          url       = TextField(),
                          file_path = TextField(),
                          )))
        
    videos = ListField(DictField(Mapping.build(
                           video_id = IntegerField(),
                           url      = TextField(),
                           )))

    submitted_date = DateTimeField()
    approved_date  = DateTimeField()
    publish_date   = DateTimeField()
    published      = BooleanField()

    url           = TextField()
    location      = TextField()
    location_type = TextField()

    # TODO : move this out into a class we inherit from - David
    def save(self):
        return self.store(self.get_db())

    def get_db(self):
        return db

    def get_stub(self):
        try:
            return ArtworkStub.objects.get(pk = self.id)
        except:
            return None

    def title(self):
        for title in self.titles:
            if title.type == "preferred":
                return title

    def get_title(self):
        for title in self.titles:
            if title.type == "preferred":
                return title

    def status(self):
        return self.model.status

    def view_url(self):
        return "/artbase/artwork/%s" % self.id()

    def edit_url(self):
        return "/artbase/artwork/%s/edit/" % self.id()

class FeaturedSet(ArtBaseModel):
    """
    Model for generating a set of featured artworks.
    Can set the image, the background color and the
    list of artworks that belong to the set.
    """
    title = models.CharField(max_length=255)
    publish_date = models.DateTimeField()
    background_color = models.CharField(max_length=6, default="FFFFFF")
    current = models.BooleanField()
    artworks = models.ManyToManyField(ArtworkStub, blank=True)

    def get_artwork(self):
        return [w for w in self.artworks.all()]

    def __unicode__(self):
        return self.title
        
    def publish(self):
        """
        Publish this featured set of artworks.
        Implicitly sets all other FeatureSets
        current to False
        """
        self.publish_date = datetime.now()
        currentSets = FeaturedSet.objects(current=True)
        for aSet in currentSets:
            aSet.current = False
            aSet.save()
        self.current = True
        self.save()


def artbase_set_current_set(sender, *args, **kwargs):
    instance = kwargs["instance"]
    if instance.current:
        FeaturedSet.objects.exclude(id=instance.id).update(current=False)
post_save.connect(artbase_set_current_set, sender=FeaturedSet)


def get_exhibitions_upload_to(self, filename):
    if self.id:
        current = MemberExhibition.objects.get(id=self.id)
        if current.image != self.image:
            if os.path.exists(current.image.path):
                if current.image != "artbase/exhibition_images/rhizome_exhibition_default.png":
                    os.remove(current.image.path)
        extension = filename.split('.')[-1]
        return 'artbase/exhibition_images/%s.%s' % (self.id, extension) 
    else:
        return 'artbase/exhibition_images/tmp/%s' % filename

class MemberExhibition(ArtBaseModel):
    """
    Model for member exhibitions. Was called ArtBase Collection
    before.
    """
    from django.contrib.auth.models import User
    live = models.BooleanField(default=False, db_index=True)
    user = models.ForeignKey(User, related_name = "exhibitions")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    statement = models.TextField(blank=True)
    image = ThumbnailerImageField(upload_to=get_exhibitions_upload_to,
                                  blank=True,
                                  resize_source=dict(size=(290, 200), crop='smart'),
                                  default="artbase/exhibition_images/rhizome_exhibition_default.png")
    time_opened = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)

    tags = TagField(max_length=1024, null=True, blank=True)

    def approved_tags(self):
        ctype = ContentType.objects.get_for_model(self)
        return [x.tag for x in
                TaggedItem.objects.filter(content_type__pk=ctype.id,
                                          object_id=self.id,
                                          approved=True)]

    def rhiz_tags(self):
        """
        Only return the Rhizome applied tags.
        """
        tags = self.tags.all()
        return [tag for tag in tags if tag.concept.authority_id == 1]
    
    def get_tags(self):
        """
        Return all tags
        """
        return Tag.objects.get_for_object(self)
    
    def content_type(self):
        ct = ContentType.objects.get_for_model(self)
        return ct
    
    def content_type_id(self):
        ct = ContentType.objects.get_for_model(self)
        return ct.id
    
    def works(self):
        return [x.artwork for x in self.memberexhibitionartwork_set.exclude(artwork__status="deleted").order_by('position')]

    def has_work(self, artwork):
        return artwork in self.works()

    def remove(self, artwork):
        exhibition_artwork = self.memberexhibitionartwork_set.get(artwork=artwork)
        try:
            exhibition_artwork.delete()
        except ObjectDoesNotExist:
            pass
        
    def artists(self):
        """
        Returns the list of artists in this exhibition
        """
        return [x.artwork.artist() for x in self.memberexhibitionartwork_set.all()]

    def updateOrder(self, artworks):
        # TODO : this is not done
        for i in range(len(artworks)):
            artwork = artworks[i]
            artwork.position = i
            artwork.save()

    def __unicode__(self):
        return self.title

    def url(self):
        return "/artbase/exhibitions/view/%s" % self.id

    def edit_url(self):
        return "/artbase/exhibitions/edit/%s" % self.id
     
    def get_absolute_url(self):
        return "/artbase/exhibitions/view/%s" % self.id
        
try:
    tagging.register(MemberExhibition,tag_descriptor_attr='member_exhibition_tags')
except tagging.AlreadyRegistered:
    # http://code.google.com/p/django-tagging/issues/detail?id=128 
    # Not sure the right way to register a model for tagging b/c it
    # raises this error if registered more than once. We end up registering
    # the first time during "manage.py syncdb" and then a second time when
    # actually attempting to run the site.
    pass

class MemberExhibitionArtwork(ArtBaseModel):
    artwork = models.ForeignKey(ArtworkStub)
    exhibition = models.ForeignKey(MemberExhibition)
    note = models.TextField()
    position = models.IntegerField()


####
# COLLECTIONS
#####

class CollectionCurator(ArtBaseModel):
    '''
    A table for storing users who can curate collections.
    '''
    from django.contrib.auth.models import User
    user = models.OneToOneField(User, blank=True, null=True)
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    collections_allowed = models.IntegerField()

    def __unicode__(self):
        return "%s" % self.user
    
class Collection(ArtBaseModel):
    """
    Collections are curated and authored introductions to
    a specific field, style, or type of art. These are not open to general users, 
    and their organizer must be designated. 
    """
    from django.contrib.auth.models import User
    live = models.BooleanField(default=False, db_index=True)
    curator = models.ForeignKey(CollectionCurator, related_name = "collector")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    statement = models.TextField(blank=True, \
                help_text = "Accepts basic HTML(links, bold, italic, etc). \
                Unfortunately, link breaks won't show up to due pagination.")
    summary = models.TextField(blank=True, null=True, max_length=400, \
                help_text = "This will display in Rhizome ArtBae Home Page" )
    time_opened = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    artworks = models.ManyToManyField(ArtworkStub)

    def get_artworks(self):
        return sorted(self.artworks.all(), key=attrgetter('created_date'))  
        #return self.artworks.all()

    def get_artworks_for_fp(self):
        return self.artworks.all()[:6]

    def get_absolute_url(self):
        return "/artbase/collections/%s" % self.id

    def __unicode__(self):
        return "%s: %s by %s" % (self.id, self.title, self.curator)
    
class Video(ArtBaseModel):
    work = models.ForeignKey(ArtworkStub)
    provider = models.CharField(max_length=255, blank=True)
    provider_video_id = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    position = models.IntegerField(blank=True,null=True)
    
    def __unicode__(self):
        return '%s' % self.id
    
def audio_upload_to(instance, filename):
    filename=filename.replace(' ','-')
    return 'artbase/audio/%s/%s' % (instance.work.id, filename)
        
class Audio(ArtBaseModel):
    work = models.ForeignKey(ArtworkStub)
    file_path = models.FileField(upload_to=audio_upload_to,blank=True,null=True)
    file_name = models.CharField(max_length = 255, blank=True,null=True)
    url = models.URLField(blank=True)
    position = models.IntegerField()    
    encod_type = models.CharField(max_length = 255, blank=True,null=True)
    
    def __unicode__(self):
        return '%s' % self.id

class CollectionManagementPolicy(models.Model):
    policy = models.TextField()
    
    class Meta:
        verbose_name = _('Collection Management Policy')
        verbose_name_plural = _('Collection Management Policy')

    def __unicode__(self):
        return '%s' % self.id
        
class ArtistAgreement(models.Model):
    policy = models.TextField()
    
    class Meta:
        verbose_name = _('ArtBase Artist Agreement')
        verbose_name_plural = _('ArtBase Artist Agreement')

    def __unicode__(self):
        return 'Artist Agreement Policy'
