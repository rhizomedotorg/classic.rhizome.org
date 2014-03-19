from django import forms
from threadedcomments.models import ThreadedComment

from bbcode.fields import BBCodeFormField
from discuss.widgets import BBCodeTextarea


class EditDiscussForm(forms.ModelForm):
    title = forms.CharField()
    comment = BBCodeFormField(widget=BBCodeTextarea)
    
    class Meta:
        model = ThreadedComment
        fields = ('title', 'comment')
            
    def __init__(self, *args, **kwargs):
        super(EditDiscussForm, self).__init__(*args, **kwargs)
