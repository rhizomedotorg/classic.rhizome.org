from django import template
from django.conf import settings
from django.db import models

OrgSubs = models.get_model('orgsubs', 'organization')

register = template.Library()

####ORGSUB NAMES

class CurrentOrganizationSubscriber(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        orgsubs = OrgSubs.objects.exclude(cancelled=True).filter(active = True).values("id","name")[:40]
        if orgsubs:
            context[self.var_name] = orgsubs
        return ''

@register.tag
def get_current_orgsubs(parser, token):
    """
    Gets the names of current orgsubs and stores them in a variable

    Syntax::

        {% get_current_orgsubs as [var_name] %}

    Example usage::

        {% get_current_orgsubs as orgsubs %}
    """
    try:
        tag_name = token.split_contents()[-1]
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    var_name = tag_name
    return CurrentOrganizationSubscriber(var_name)
