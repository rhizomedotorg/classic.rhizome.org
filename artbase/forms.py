import os
import datetime
import simplejson as json
from ast import literal_eval

from django import forms
from django.forms import ModelForm
from django.conf import settings
from django.contrib.admin import widgets  
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.forms.formsets import formset_factory
from django.contrib.contenttypes.models import ContentType

import tagging

from artbase.models import MemberExhibition, ArtworkStub,Artwork,Technology,Video,Audio,AboutArtbase    
from tagging.models import Tag, TaggedItem
from utils.document_form import *
from utils.multi_form import *



###
#HELPER FUNCTIONS
###
def check_for_empty_values(fields_and_values):
    """
    returns list of fields with empty values, perhaps could be abstracted to a general matching function and put in utils...
    """
    empties = []
    for item in fields_and_values:
        if item[1] == "" or item[1] == None:
            empties.append(item)
    return empties


####CUSTOM WIDGETS
class ImageWidget(forms.FileInput):
    """
    A file upload widget that allows viewing/removing images, could prolly be put in utils, but only used here...
    """
    def __init__(self, attrs={}):
        super(ImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('<img src = "'+settings.MEDIA_URL+'%s" />' % value )
            if "rhizome_art_default" not in value.url:
                if "rhizome_exhibition_default" not in value.url:
                    output.append('<div class="delete-checkbox"><input type="checkbox" name="delete_%s" id="id_delete_%s" /><label>Delete this image?</label></div>' %(name,name))
            output.append('<div><label>Change this image?</label></div>')
        output.append(super(ImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))      

###FORM CLASSES

class AboutArtbaseForm(ModelForm):
    mission = forms.CharField()
    archival_process = forms.CharField()
    philosophy = forms.CharField()
    selection_criteria = forms.CharField()
    current_projects = forms.CharField()
    access_membership = forms.CharField()

    class Meta:
        model = AboutArtbase
        
    def __init__(self, *args, **kwargs):
        super(AboutArtbaseForm, self).__init__(*args, **kwargs)


class BaseArtworkForm(ModelForm):
    """
    Form for submitting artworks and adding base artwork information.
    """

    class Meta:
        model = ArtworkStub
        fields = ("title", "url", "summary", "statement", "description", "created_date", "byline")
        exclude=("user","needs_repair","completion_percentage")

    def __init__(self, *args, **kwargs):
        super(BaseArtworkForm, self).__init__(*args, **kwargs)
        self.fields['created_date'].widget = widgets.AdminSplitDateTime()        

    def save(self, commit=True):
        artworkstub = super(self.__class__, self).save(commit=False)
        if commit:
            artworkstub.save()
        return artworkstub

class ArtworkMediaForm(ModelForm):
    #video = forms.FileField(required=False, label=_("Artwork video"))
    video_url = forms.URLField(
                  required=False,
                  max_length=255,
                  label=_("Artwork video url (if remote)")
                  )
    audio = forms.FileField(required=False, label=_("Artwork audio"))
    audio_url = forms.URLField(
                   required=False,
                   max_length=255,
                   label=_("Artwork audio url (if remote)")
                   )
                   
    image_large = forms.ImageField(required=False, label=_("Large Image"),widget=ImageWidget)
    image_medium = forms.ImageField(required=False, label=_("Medium Image"),widget=ImageWidget)
    image_small = forms.ImageField(required=False, label=_("Icon Image"),widget=ImageWidget)
    image_featured = forms.ImageField(required=False, label=_("Featured Image"),widget=ImageWidget)
    delete_image_large = forms.BooleanField(required=False)
    delete_image_medium = forms.BooleanField(required=False)
    delete_image_small = forms.BooleanField(required=False)
    delete_image_featured = forms.BooleanField(required=False)

    class Meta:
        model = ArtworkStub
        fields = ("image_featured", "image_small", "image_medium", "image_large",)
        exclude=("user",)

    def save(self, commit=True):
        artwork = super(self.__class__, self).save(commit=False)
        
        ##replacement of prev uploaded images handled in artworkstub model's upload_to functions
        
        if self.cleaned_data.get('video_url'):
            new_video = Video(url = self.cleaned_data.get('video_url'), work=artwork)
            new_video.save() 
            vid_dict = {"url":"%s" % new_video.url, "video_id": "%s" % new_video.id}
            work_document = artwork.get_document() 
            work_document.videos.append(vid_dict)
            work_document.save()
        
        if self.cleaned_data.get('audio_url'):
            new_audio = Audio(url = self.cleaned_data.get('audio_url'), work=artwork)
            new_audio.save() 
            audio_dict = {"url":"%s" % new_audio.url, "audio_id": "%s" % new_audio.id}
            work_document = artwork.get_document() 
            work_document.audio.append(audio_dict)
            work_document.save()
            
        if self.cleaned_data.get('audio'):
            new_audio = Audio(work=artwork, file_path = self.cleaned_data.get('audio'))
            filename = "%s" % self.cleaned_data.get('audio')
            extension = filename.split('.')[-1]
            new_audio.file_name = filename
            new_audio.encod_type = extension
            new_audio.save() 
            audio_url = "%s%s" %(settings.MEDIA_URL, new_audio.file_path)
            audio_dict = {"file_path":"%s" % new_audio.file_path, "url": audio_url, "audio_id": "%s" % new_audio.id}
            work_document = artwork.get_document() 
            work_document.audio.append(audio_dict)
            work_document.save()
            
        if self.cleaned_data.get('delete_image_large'):
            if os.path.exists(artwork.image_large.path) and "rhizome_art_default.png" not in artwork.image_large.path:
                os.remove(artwork.image_large.path)
            artwork.image_large = 'artbase/images/rhizome_art_default.png'
        
        if self.cleaned_data.get('delete_image_medium'):
            if os.path.exists(artwork.image_medium.path) and "rhizome_art_default.png" not in artwork.image_medium.path:
                os.remove(artwork.image_medium.path)
            artwork.image_medium = 'artbase/images/rhizome_art_default.png'
        
        if self.cleaned_data.get('delete_image_small'):
            if os.path.exists(artwork.image_small.path) and "rhizome_art_default.png" not in artwork.image_small.path:
                os.remove(artwork.image_small.path)
            artwork.image_small = 'artbase/images/rhizome_art_default.png'

        if self.cleaned_data.get('delete_image_featured'):
            if os.path.exists(artwork.image_featured.path) and "rhizome_art_default.png" not in artwork.image_featured.path:
                os.remove(artwork.image_featured.path)
            artwork.image_featured = 'artbase/images/rhizome_art_default.png'

        if commit:
            artwork.save()
            
        return artwork

class MemberExhibitionForm(ModelForm):
    """
    Form for member exhibitions. 
    """
    artworks = forms.CharField(required=False, widget=forms.HiddenInput)
    image = forms.ImageField(required=False, label=_("Invitation Image"),widget=ImageWidget)
    delete_image = forms.BooleanField(required=False)
    
    class Meta:
        model = MemberExhibition
        fields = ("title", "subtitle", "statement", "image", "tags")
        
    def save(self, commit=True):
        exhibition = super(self.__class__, self).save(commit=False)    
        if self.cleaned_data.get('delete_image'):
            if os.path.exists(exhibition.image.path):
                if "rhizome_exhibition_default.png" not in exhibition.image:
                    os.remove(exhibition.image.path)
                    exhibition.image = 'artbase/exhibition_images/rhizome_exhibition_default.png'
                    exhibition.save()

        if commit:
            exhibition.save()
            
        return exhibition
        
class ArtworkLicenseAgreementForm(ModelForm):
    license_slug = forms.CharField(required=False, max_length=255)
    agree_to_agreement = forms.BooleanField(required=False)
    
    class Meta:
        model = ArtworkStub
        fields = ("agree_to_agreement",)
        exclude=("user",)

class ApproveTagsForm(forms.Form):
    """
    This form is only used by logged in admins. It's not the cleanest and 
    adds a good bit of work and writing to the dbs, but it creates a simple 
    interface for staff to approve and promote tags on the artwork details page
    """

    artist_tags = forms.MultipleChoiceField(label='Artist Tags', 
            widget=forms.CheckboxSelectMultiple(attrs={'class':'artist_tag'}),required=False, choices=())
    approved_tags = forms.MultipleChoiceField(label='Approved Tags', 
            widget=forms.CheckboxSelectMultiple(attrs={'class':'rhizome_tag'}),required=False, choices=())

    def __init__(self, artwork_stub, *args, **kwargs):
        super(ApproveTagsForm, self).__init__(*args, **kwargs)
        from artbase.views import artbase_approved_tags
        all_approved_tags = artbase_approved_tags()
        work_approved_tags = artwork_stub.get_approved_tags()
        self.fields['artist_tags'].choices = [(tag.id, tag) for tag in artwork_stub.get_artist_tags()]    
        self.fields['approved_tags'].choices = [(tag.id, tag) for tag in all_approved_tags]    
        self.fields['approved_tags'].initial = ["%s" % tag.id for tag in work_approved_tags]
                     
    def save(self, artwork_stub,  commit=True, *args, **kwargs):
        """
        This is pretty intense, but it manages to keep everything in tact 
        and in order and still have that useful frontend for staff.
        """
        
        # combine the promoted artist tags and approved rhizome tags into one list of approved tags
        promoted_ids = self.cleaned_data.get('artist_tags')
        promoted_artist_tag_objects = list(Tag.objects.filter(id__in = promoted_ids))
        
        approved_ids= self.cleaned_data.get('approved_tags')
        approved_tag_objects = list(Tag.objects.filter(id__in = approved_ids))
        
        combined_list_of_approved_tags = promoted_artist_tag_objects + [i for i in approved_tag_objects if i not in promoted_artist_tag_objects]
        
        # Mark all in combined_list_of_approved_tags as approved
        ctype = ContentType.objects.get_for_model(artwork_stub)
        for tag in combined_list_of_approved_tags:
            tagged_item, created = TaggedItem.objects.get_or_create(tag = tag, content_type = ctype, object_id=artwork_stub.id)
            tagged_item.approved = 1
            tagged_item.save()

        # combine the artist tags and approved tags into one list of work tags
        artist_tags = [tag for tag in artwork_stub.get_artist_tags()]
        combined_list_of_work_tags = artist_tags + [i for i in combined_list_of_approved_tags if i not in artist_tags]

        # turn master list into a string, so to update the work's tags via the tagging field when saved 
        # update method, which will create the relationships if necessary      
        combined_tags_string = ', '.join([('%s' % tag) for tag in combined_list_of_work_tags])         
                
        #Tag.objects.update_tags(work, combined_tags_string)
        artwork_stub.tags = combined_tags_string

        doc = artwork_stub.get_document()
        doc.tags = combined_list_of_work_tags
        doc.rhiz_tags = combined_list_of_approved_tags
        
        if commit:
            doc.save()
            artwork_stub.save()   

        return artwork_stub, doc
                  
# ==============================================================================
# Artwork Document Forms
# ==============================================================================

from artbase.models import Artwork

# NOTE: the following is kind of boiler-plate-y, but making it more generic
# might be too "magical" - David

class ArtworkCreatorForm(DocumentForm):
    class Meta:
        document = Artwork
        path = ("creators",)
ArtworkCreatorsFormSet = formset_factory(ArtworkCreatorForm,
                                         formset=DocumentFormSet,
                                         can_delete=True,
                                         extra=0)


class ArtworkExhibitionForm(DocumentForm):
    class Meta:
        document = Artwork
        path = ('exhibitions',)
ArtworkExhibitionsFormSet = formset_factory(ArtworkExhibitionForm,
                                            formset=DocumentFormSet,
                                            can_delete=True,
                                            extra=0)


class ArtworkSupportForm(DocumentForm):
    class Meta:
        document = Artwork
        path = ('support',)
ArtworkSupportFormSet = formset_factory(ArtworkSupportForm,
                                        formset=DocumentFormSet,
                                        can_delete=True,
                                        extra=0)


class ArtworkFootnoteForm(DocumentForm):
    class Meta:
        document = Artwork
        path = ('footnotes',)
ArtworkFootnotesFormSet = formset_factory(ArtworkFootnoteForm,
                                          formset=DocumentFormSet,
                                          can_delete=True,
                                          extra=0)


class ArtworkArticleForm(DocumentForm):
    class Meta:
        document = Artwork
        path = ('articles',)
ArtworkArticlesFormSet = formset_factory(ArtworkArticleForm,
                                         formset=DocumentFormSet,
                                         can_delete=True,
                                         extra=0)


class TechnologyField(forms.CharField):
    def clean(self, value):
        value = super(TechnologyField, self).clean(value)
        if value:
            value = [int(x) for x in literal_eval(value)]
        else:
            value = []
        r = []
        for object_id in value:
            r.append(Technology.objects.get(pk=int(object_id)))
        return r


class ArtworkStubForm(ModelForm):
    technologies = TechnologyField(required=False, widget=forms.MultipleHiddenInput)
    tags = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = ArtworkStub
        fields = (
                  "readme",
                  "tags",
                  "worked_with",
                  "support",
                  "notices",
                  "format",
                  "state_ed",
                  "collective",
                  "exhibitions",
                  "tech_details",
                  "technologies",
                  "allow_comments"
                )
        exclude=("location", "user", "exhibitions", "support", "other_artists")

    def save(self, commit=True, **kwargs):
        artwork_stub = super(ArtworkStubForm, self).save(commit=False, **kwargs)
        current = artwork_stub.technologies.all()
        new = self.cleaned_data["technologies"]
        
        for t in current:
            artwork_stub.technologies.remove(t)
        for t in new:
            artwork_stub.technologies.add(t)
                
        artwork_stub.save()
        return artwork_stub
 
 
def sync_document_and_stub(document=None, stub=None, multi_form_instance_proxy_object=None):
                    
        '''   
        + ensure couchdb sync'd.
        + most of this data created by the ArtworkStubForm in the Multiform 
        + have to be careful where saved due to couchdb conflict errors.
        + creates one place to get nasty specific if need be
        + can be a document and stub or multi_form_instance_proxy_object
        '''
        
        if not document and not stub and not multi_form_instance_proxy_object:
            raise Exception('Missing Arguments. Please proved either a document and stub or a MultiFormProxy object')
                    
        if multi_form_instance_proxy_object:
            document = multi_form_instance_proxy_object.document
            stub = multi_form_instance_proxy_object.model
            
        document.statement = stub.statement
        document.location = stub.location
        document.readme = stub.readme
        document.created = stub.created_date        
        document.summary = stub.summary
        document.location_type = stub.location_type
        document.format = stub.format
        document.notices = stub.notices
        document.collective = {
             "display_string":stub.collective,
             "name_authority":"Rhizome",
             "name_authority_id":None,
            }
        
        techs = stub.get_technologies()
        if techs:
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
        
        if multi_form_instance_proxy_object:
            return multi_form_instance_proxy_object
        else:
            return document, stub
 
# This takes all the forms and creates a crazy uber form - David
ArtworkDetailsForm = multiple_form_factory({
        'artworkstub': ArtworkStubForm,
        'creator': ArtworkCreatorsFormSet,
        'exhibition': ArtworkExhibitionsFormSet,
        'support': ArtworkSupportFormSet,
        'footnote': ArtworkFootnotesFormSet,
        'article': ArtworkArticlesFormSet,
}, ['artworkstub', 'creator', 'exhibition', 'support', 'footnote', 'article',])


