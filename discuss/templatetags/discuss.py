import re

from django import template
from django.conf import settings
from django.db import models
from utils.helpers import strip_bbcode

from django.core.urlresolvers import reverse

DiscussionThread = models.get_model('discuss', 'discussionthread')
ThreadedComment = models.get_model('threadedcomments', 'ThreadedComment')

register = template.Library()

class ActiveThreads(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        threads = DiscussionThread.objects.filter(is_public=True)[:int(self.limit)]
        if threads and (int(self.limit) == 1):
            context[self.var_name] = threads[0]
        else:
            context[self.var_name] = threads
        return ''

@register.tag
def get_active_threads(parser, token):
    """
    Gets the latest threads and stores them in a variable with an optional limit

    Syntax::

        {% get_latest_threads [limit] as [var_name] %}

    Example usage::

        {% get_latest_comments 10 as threads %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return ActiveThreads(format_string, var_name)

class ActiveThreads(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        comments = DiscussionThread.objects.filter(is_public=True)[:int(self.limit)]
        if comments and (int(self.limit) == 1):
            context[self.var_name] = comments[0]
        else:
            context[self.var_name] = comments
        return ''
        
        
class LatestComments(template.Node):
    def __init__(self, limit, var_name):
        self.limit = limit
        self.var_name = var_name
    
    def render(self, context):
        comments = ThreadedComment.objects.filter(is_public=True).order_by('-submit_date')[:int(self.limit)]
        cleaned_comments =  []
        for comment in comments:
            comment.comment = strip_bbcode(comment.comment)
            cleaned_comments.append(comment)
                
        if cleaned_comments and (int(self.limit) == 1):
            context[self.var_name] = cleaned_comments[0]
        else:
            context[self.var_name] = cleaned_comments
        return ''

@register.tag
def get_latest_comments(parser, token):
    """
    Gets the latest comments and stores them in a variable with an optional limit

    Syntax::

        {% get_latest_comments [limit] as [var_name] %}

    Example usage::

        {% get_latest_comments 10 as comments %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return LatestComments(format_string, var_name)

# yanked from django-hitcounts app
class GetHitCountJavascript(template.Node):

    def handle_token(cls, parser, token):
        args = token.contents.split()
        
        if len(args) == 3 and args[1] == 'for':
            return cls(object_expr = parser.compile_filter(args[2]))

        else:
            raise TemplateSyntaxError, \
                    "'get_hit_count' requires " + \
                    "'for [object] in [timeframe] as [variable]' " + \
                    "(got %r)" % args

    handle_token = classmethod(handle_token)


    def __init__(self, object_expr):
        self.object_expr = object_expr


    def render(self, context):
        ctype, object_pk = get_target_ctype_pk(context, self.object_expr)
        
        obj = None
        
        try:
            obj, created = HitCount.objects.get_or_create(content_type=ctype, 
                        object_pk=object_pk)
        except:
            hitcounts = HitCount.objects.filter(content_type=ctype, 
                        object_pk=object_pk).order_by('-modified')[:1]
            
            for h in hitcounts:
                obj = h

# jquery code
#         js =    "$.post( '" + reverse('hitcount_update_ajax') + "',"   + \
#                 "\n\t{ hitcount_pk : '" + str(obj.pk) + "' },\n"         + \
#                 "\tfunction(data, status) {\n"                         + \
#                 "\t\tif (data.status == 'error') {\n"                  + \
#                 "\t\t\t// do something for error?\n"                   + \
#                 "\t\t}\n\t},\n\t'json');"
        
####### EDITED TO WORK WITH MOOTOOLS - NH
        
        js =    "new Request({method: 'post',url: '" + \
                reverse('hitcount_update_ajax') + "', \
                    data:  {hitcount_pk : '" + str(obj.pk) + "' }, \
                    onError: function(rtxt) {}, \
                    onSuccess: function(rtxt,rxml) {}}).send();" 

        return js

        
        
def get_hit_count_javascript_mootools(parser, token):
    '''
    Return javascript for an object (goes in the document's onload function)
    and requires jQuery.  NOTE: only works on a single object, not an object
    list.

    For example:

    <script src="/media/js/jquery-latest.js" type="text/javascript"></script>
    <script type="text/javascript"><!--
    $(document).ready(function() {
        {% get_hit_count_javascript for [object] %}
    });
    --></script> 
    '''
    return GetHitCountJavascript.handle_token(parser, token)

register.tag('get_hit_count_javascript_mootools', get_hit_count_javascript_mootools)
