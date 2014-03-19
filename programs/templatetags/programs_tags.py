import re

from django import template
from django.conf import settings
from django.db import models
from programs.models import *
from itertools import chain
from operator import attrgetter, itemgetter

register = template.Library()

class UpcomingPrograms(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
        
    def render(self, context):
        events = get_upcoming_events()
        exhibitions = get_upcoming_exhibitions()    
        context[self.var_name] = sorted(chain(events, exhibitions),key=attrgetter('start_date'),reverse=True)
        return ''

@register.tag
def get_upcoming_programs(parser, token):
    """
    Gets upcoming deadlines them in a variable with an optional limit

    Syntax::

        {% get_upcoming_programs as [var_name] %}

    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    var_name = "%s" % m.groups()
    return UpcomingPrograms(var_name)