import re

from django import template
from django.conf import settings
from django.db import models
from utils.helpers import strip_bbcode
from announce.models import get_announcements_by_deadline, get_latest_announcements, get_random_jobs, get_events_and_opportunities

register = template.Library()

class UpcomingDeadline(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
        
    def render(self, context):
        announcements = get_announcements_by_deadline(int(self.limit))
        if announcements and (int(self.limit) == 1):
            context[self.var_name] = announcements[0]
        else:
            context[self.var_name] = announcements
        return ''

@register.tag
def get_upcoming_deadlines(parser, token):
    """
    Gets upcoming deadlines them in a variable with an optional limit

    Syntax::

        {% get_upcoming_deadlines [limit] as [var_name] %}

    Example usage::

        {% get_upcoming_deadlines 10 as deadlines %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return UpcomingDeadline(format_string, var_name)
    
    
class RecentlyPosted(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        announcements = get_latest_announcements(self.limit) 
        if announcements and (int(self.limit) == 1):
            context[self.var_name] = announcements[0]
        else:
            context[self.var_name] = announcements
        return ''

@register.tag
def get_recently_posted(parser, token):
    """
    Gets recent announcements and puts them in a variable with an optional limit

    Syntax::

        {% get_recently_posted [limit] as [var_name] %}

    Example usage::

        {% get_recently_posted 10 as recent %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return RecentlyPosted(format_string, var_name)
    
class JobsBoard(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        jobs = get_random_jobs(self.limit) 
        if jobs and (int(self.limit) == 1):
            context[self.var_name] = jobs[0]
        else:
            context[self.var_name] = jobs
        return ''

@register.tag
def get_jobs_board(parser, token):
    """
    Gets jobs and puts them in a variable with an optional limit

    Syntax::

        {% get_jobs_board [limit] as [var_name] %}

    Example usage::

        {% get_jobs_board 10 as jobs %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return JobsBoard(format_string, var_name)
    

class EventsAndOpps(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        events_and_opps = get_events_and_opportunities(self.limit) 
        if events_and_opps and (int(self.limit) == 1):
            context[self.var_name] = events_and_opps[0]
        else:
            context[self.var_name] = events_and_opps
        return ''

@register.tag
def get_events_and_opps(parser, token):
    """
    Gets jobs and puts them in a variable with an optional limit

    Syntax::

        {% get_events_and_opps [limit] as [var_name] %}

    Example usage::

        {% get_events_and_opps 10 as events_and_opps %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return EventsAndOpps(format_string, var_name)