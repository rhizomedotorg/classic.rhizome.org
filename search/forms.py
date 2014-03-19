from django import forms
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
import haystack
from haystack.forms import SearchForm, model_choices
from haystack.query import SearchQuerySet
from utils.helpers import split_by
from django.forms.widgets import SelectMultiple,CheckboxInput,CheckboxSelectMultiple
from django.utils.encoding import StrAndUnicode, force_unicode
from itertools import chain
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe

'''
The only reason i created any of this was to control the output of checkbox select multiple, as I needed to add some <br/>'s into the output, so I created a new version of CheckboxSelectMultiple (SearchCheckboxSelectMultiple). otherwise, it's basically the same as stuff as found in haystack forms. Seems like overkill, I know...
'''

class SearchCheckboxSelectMultiple(SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''
            if i > 0 and i % 8 == 0: # if the current iteration is diviible by 7, add a <br />
                 output.append(u'<br />')
            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)

        
class RhizomeModelSearchForm(SearchForm):
    def __init__(self, *args, **kwargs):
        super(RhizomeModelSearchForm, self).__init__(*args, **kwargs)
        self.fields['models'] = forms.MultipleChoiceField(choices=model_choices(), required=False, label=_('Search In'), widget=SearchCheckboxSelectMultiple)

    def get_models(self):
        """Return an alphabetical list of model classes in the index."""
        search_models = []
        
        for model in self.cleaned_data['models']:
            search_models.append(models.get_model(*model.split('.')))
        
        return search_models
        #return list(split_by(search_models, 4))
        
        
    def search(self):
        sqs = super(RhizomeModelSearchForm, self).search()
        return sqs.models(*self.get_models())


class RhizomeHighlightedModelSearchForm(RhizomeModelSearchForm):
    def search(self):
        return super(RhizomeHighlightedModelSearchForm, self).search().highlight()
