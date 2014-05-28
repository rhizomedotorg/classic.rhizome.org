from django import forms
from django.forms import ModelForm
from models import *
from django.conf import settings
from django.contrib.admin import widgets  
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.forms.util import ErrorList


class CommissionsImageWidget(forms.FileInput):
    """
    A file upload widget that shows the current announcement's image
    """
    def __init__(self, attrs={}):
        super(CommissionsImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('<img width="230" src = "'+settings.MEDIA_URL+'%s" />' % value )
            output.append('<div class= "delete-image"><input type="checkbox" name="delete_image" id="id_delete_image" /><label class = "light-gray">Delete this image?</label></div>')

        output.append(super(CommissionsImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
        
class ProposalForm(ModelForm): 
    image = forms.ImageField(required=False,widget=CommissionsImageWidget)      
    save_as_bio = forms.BooleanField(required=False)
    other_artists_users = forms.CharField(max_length = 125, required=False)
    other_artists = forms.CharField(max_length = 125, required=False)
    summary = forms.CharField(max_length=150)
    delete_image = forms.BooleanField(required=False)
    external_url = forms.URLField(required=False)
    rhizome_hosted = forms.BooleanField(initial=1,required=False)
    first_name = forms.CharField(max_length = 125, required=True)

    class Meta:
        model = Proposal
        exclude = ('author','artists','username','legacy_state','legacy_country','created','view_rank','finalist','cycle','submitted','rank_vote_finalist', 'deleted')
        
    def clean_other_artists_users(self): # make sure other artist/users exist           
        if self.cleaned_data['other_artists_users']:
            verfied_artists = []
            for artist in self.cleaned_data['other_artists_users'].split(','):
                artist = artist.strip()
                try:
                    user = User.objects.get(email=artist)
                    verfied_artists.append(user)
                except:
                    raise forms.ValidationError(_("There isn't a Rhizome account matching this email address: %s" % artist))
            return verfied_artists
    
    def clean(self):
        cleaned_data = self.cleaned_data
        external_url = cleaned_data.get('external_url')
        rhizome_hosted = cleaned_data.get('rhizome_hosted')
        
        if not external_url and not rhizome_hosted:
           self._errors["external_url"] = ErrorList([u"If your proposal will not be Rhizome hosted, please provide a URL to your proposal website in the space provided"])
        return cleaned_data
                
    def __init__(self, *args, **kwargs):
        super(ProposalForm, self).__init__(*args, **kwargs)
               
    def save(self, commit=True):
        proposal = super(self.__class__, self).save(commit=False)
        proposal.other_artists = self.cleaned_data["other_artists"]

        if self.cleaned_data.get('delete_image'):
            import os
            if os.path.exists(proposal.image.path):
                os.remove(proposal.image.path)
                proposal.image = ''
                proposal.thumbnail = ''
        if commit==True:
            proposal.save()
        return proposal
        
class ApprovalVoteForm(ModelForm): 
    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())
    proposal = forms.ModelChoiceField(queryset=Proposal.objects.all(), widget=forms.HiddenInput())
    approved = forms.TypedChoiceField(coerce=bool,choices=((True, 'YES'),(False, 'NO')), widget=forms.RadioSelect)
    
    class Meta:
        model = ApprovalVote
        exclude = ('created',)

    def __init__(self, *args, **kwargs):
        super(ApprovalVoteForm, self).__init__(*args, **kwargs)

class RankVoteForm(forms.Form): 
    rankings = forms.CharField(required=True, widget=forms.HiddenInput,error_messages={'required': 'In order to vote, you must reorder the proposals into a ranking hierarchy of your choosing.'})

    def __init__(self, *args, **kwargs):
        super(RankVoteForm, self).__init__(*args, **kwargs)

### new stuff

class GrantProposalForm(forms.Form):
    def __init__(self, *args, **kwargs):
        grant = kwargs.pop('grant')
        super(GrantProposalForm, self).__init__(*args, **kwargs)

        for f in grant.fields.all():
            self.fields[f.name] = f.form_field()
