from django import template
from django.conf import settings
from django.db import models

SidebarItems = models.get_model('frontpage', 'sidebaritem')

register = template.Library()

class CurrentFPSidebarItems(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        items = SidebarItems.objects.filter(is_active=True)
        if items:
            context[self.var_name] = items
        return ''

@register.tag
def get_current_fp_sidebar_items(parser, token):
    """
    Gets the current sidebar items and stores them in a variable

    Syntax::

        {% get_current_fp_sidebar_items as [var_name] %}

    Example usage::

        {% get_current_fp_sidebar_items as items %}
    """
    try:
        tag_name = token.split_contents()[-1]
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    var_name = tag_name
    return CurrentFPSidebarItems(var_name)