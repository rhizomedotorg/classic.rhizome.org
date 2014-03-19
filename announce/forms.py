from django import forms
from django.forms import ModelForm
from django.conf import settings
from django.contrib.admin import widgets  
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from announce.models import *

from support.fields import CreditCardField, CreditCardExpiryField, CreditCardCVV2Field
from support.models import ccType

####
## WIDGETS
####
class AnnounceImageWidget(forms.FileInput):
    """
    A file upload widget that shows the current announcement's image
    """
    def __init__(self, attrs={}):
        super(AnnounceImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('<img  width="230" src = "'+settings.MEDIA_URL+'%s" />' % value )
            output.append('<div class= "delete-image"><input type="checkbox" name="delete_image" id="id_delete_image" /><label class = "light-gray">Delete this image?</label></div>')

        output.append(super(AnnounceImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
        
class EventForm(ModelForm): 
    image = forms.ImageField(required=False,widget=AnnounceImageWidget)      
    delete_image = forms.BooleanField(required=False)

    class Meta:
        model = Event
        exclude = ('user','username','status','ip_address','is_spam')

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget = widgets.AdminSplitDateTime()
        self.fields['end_date'].widget = widgets.AdminSplitDateTime()        
        
    def save(self, commit=True):
        Event = super(self.__class__, self).save(commit=False)
        if self.cleaned_data.get('delete_image'):
            import os
            if os.path.exists(Event.image.path):
                os.remove(Event.image.path)
                Event.image = ''
                Event.thumbnail = ''
        if commit:
            Event.save()
        return Event

        
class OpportunityForm(ModelForm):
    image = forms.ImageField(required=False,widget=AnnounceImageWidget) 
    delete_image = forms.BooleanField(required=False)

    class Meta:
        model = Opportunity
        exclude = ('user','username','status','ip_address','is_spam')

    def __init__(self, *args, **kwargs):
        super(OpportunityForm, self).__init__(*args, **kwargs)
        self.fields['deadline'].widget = widgets.AdminSplitDateTime()
    
    def save(self, commit=True):
        Opportunity = super(self.__class__, self).save(commit=False)
        if self.cleaned_data.get('delete_image'):
            import os
            if os.path.exists(Opportunity.image.path):
                os.remove(Opportunity.image.path)
                Opportunity.image = ''
                Opportunity.thumbnail = ''
        if commit:
            Opportunity.save()
        return Opportunity

                  
class JobForm(ModelForm):    
    image = forms.ImageField(required=False,widget=AnnounceImageWidget) 
    delete_image = forms.BooleanField(required=False)

    class Meta:
        model = Job
        exclude = ('user','username','status','ip_address','is_spam')

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        self.fields['deadline'].widget = widgets.AdminSplitDateTime()

    def save(self, commit=True):
        Job = super(self.__class__, self).save(commit=False)
        if self.cleaned_data.get('delete_image'):
            import os
            if os.path.exists(Job.image.path):
                os.remove(Job.image.path)
                Job.image = ''
                Job.thumbnail = ''
        if commit:
            Job.save()
        return Job

class JobPaymentForm(ModelForm):
    cc_type = forms.CharField(widget=forms.Select(choices=ccType))
    cc_number = CreditCardField(label="Credit Card Number")
    cc_exp_date = CreditCardExpiryField(label="Expiration Date")
    cc_card_code = CreditCardCVV2Field(label="Card Security Code")
    first_name = forms.CharField(max_length=20)
    last_name = forms.CharField(max_length=20)
    amount = forms.DecimalField(max_digits=15, decimal_places=2, widget=forms.HiddenInput)    
    
    class Meta:
        model = JobPostingPayment
        exclude = ('user','job')

    def __init__(self, *args, **kwargs):
        super(JobPaymentForm, self).__init__(*args, **kwargs)
        
    def save(self, user, job, commit=True, *args, **kwargs):
        payment = super(self.__class__, self).save(commit=False)
        payment.user = user
        payment.job = job        

        if commit:
            job.status = True
            job.save()
            payment.save()
            
        return payment
        
        
        
        