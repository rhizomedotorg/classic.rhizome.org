from django.forms.widgets import Textarea
from django.template.loader import render_to_string

class BBCodeTextarea(Textarea):
    def render(self, name, value, attrs=None):
        return render_to_string('comments/basic_bbcode.html') + super(BBCodeTextarea, self).render(name, value, attrs)