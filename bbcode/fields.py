from django.db import models
from django import forms
validate = __import__('bbcode').validate

class BBCodeTextField(models.TextField):
    """
    BBCodeField for a database which basically is a TextField but uses the 
    BBCodeFormField form field to validate bbcode input (eg. in admin)
    """
    def formfield(self, **kwargs):
        return models.TextField.formfield(self, form_class=BBCodeFormField, **kwargs)

class BBCodeCharField(models.CharField):
    """
    BBCodeField for a database which basically is a CharField but uses the 
    BBCodeFormField form field to validate bbcode input (eg. in admin)
    """
    def formfield(self, **kwargs):
        return models.CharField.formfield(self, form_class=BBCodeFormField, **kwargs)
    
    
class BBCodeFormField(forms.CharField):
    """
    A form field validating BBCode Input (it does NOT parse it)
    """
    def clean(self, content):
        preclean = forms.CharField.clean(self, content)
        errors = validate(preclean, auto_discover=True)
        if errors:
            raise forms.ValidationError('\n'.join(map(lambda x: 'Line: %s: %s' % (x.lineno, x.message), errors)))
        return content