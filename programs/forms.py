from django.forms import ModelForm

from programs.models import RhizEvent, Exhibition

class RhizEventForm(ModelForm):
    class Meta:
        model = RhizEvent
    
    def __init__(self, *args, **kwargs):
        super(RhizEventForm, self).__init__(*args, **kwargs)

class ExhibitionForm(ModelForm):
    class Meta:
        model = Exhibition
    
    def __init__(self, *args, **kwargs):
        super(ExhibitionForm, self).__init__(*args, **kwargs)
