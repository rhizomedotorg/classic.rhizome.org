import datetime
import time
import re
from itertools import groupby
from operator import attrgetter

from django.conf import settings
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext

from django.http import Http404
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import cache_page

from blog.models import *

from tagging.models import Tag, TaggedItem
from utils.template import RhizomePaginator
from utils.helpers import split_by

from django.template.defaultfilters import truncatewords_html


##UTILITIES
def get_blog_archive_breakdown():
    '''
    this is also a template tag, it feeds the blog archive sidebar monthly breakdown. Might could be rewritten.
    '''
    blog_archive_years = Post.objects.dates('publish', 'year', order='DESC')
    blog_archive_months = Post.objects.dates('publish', 'month', order='DESC')
    block_archive_months_split = []
    for year_date in blog_archive_years:
        matching_dates = [month_date for month_date in blog_archive_months if month_date.year == year_date.year]
        block_archive_months_split.append(matching_dates)
    block_archive_breakdown = zip(blog_archive_years,block_archive_months_split)
    return block_archive_breakdown


##VIEWS

def index(request):
    posts = Post.objects.published().exclude(staff_blog=1).exclude(fp_and_staff_blog=True)
    post_paginator = RhizomePaginator(posts, per_page=8, url=request.get_full_path())
    post_paginator.set_current_page(request.GET.get('page'))
    d = {  
        'post_paginator': post_paginator,
        'current_page_str': str(post_paginator.current_page),
    }
    return render(request, 'blog/post_list.html', d)

def post_archive_year(request, year=None):
    breadcrumb = (("Editorial","/editorial"),("Archives",None))

    context = RequestContext(request)
    if year:
        posts = Post.objects.published().filter(publish__year=year).order_by('-publish')
    else:
        latest_blog_date = blog_archive_years = Post.objects.dates('publish', 'year', order='DESC')[:1]
        for dates in latest_blog_date:
            year = dates.year
        posts = Post.objects.published().filter(publish__year=year).order_by('-publish')
    
    post_paginator = RhizomePaginator(posts, per_page=10,url=request.get_full_path())
    post_paginator.set_current_page(request.GET.get("page"))
    
    d = {  
        "post_paginator":post_paginator,
        "year":year,
        "breadcrumb":breadcrumb
        }
    
    return render_to_response("blog/archive.html", d, context)

def post_archive_month(request, year, month, **kwargs):
    breadcrumb = (("Editorial","/editorial"),("Archives",None))
    context = RequestContext(request)
    tt = time.strptime("%s-%s" % (year, month), '%s-%s' % ('%Y', '%b'))
    date = datetime.date(*tt[:3])
    posts = Post.objects.published().filter(publish__year=year).filter(publish__month=date.month).order_by('publish')
    post_paginator = RhizomePaginator(posts, per_page=10,url=request.get_full_path())
    post_paginator.set_current_page(request.GET.get("page"))
    d = {  
        "post_paginator":post_paginator,
        "date":date,
        "month":date.month,
        "year":year,
        "breadcrumb":breadcrumb
        }
    return render_to_response("blog/archive.html", d, context)

def post_archive_day(request, year, month, day, **kwargs):
    breadcrumb = (("Editorial","/editorial"),("Archives",None))
    context = RequestContext(request)
    tt = time.strptime('%s-%s-%s' % (year, month, day),'%s-%s-%s' % ('%Y', '%b', '%d'))
    date = datetime.date(*tt[:3])
    posts = Post.objects.published().filter(publish__year=year).filter(publish__month = date.month).filter(publish__day = date.day).order_by('publish')        
    if not posts:
        return HttpResponseRedirect('/editorial/archive/%s/%s' % (year, month)) 
    post_paginator = RhizomePaginator(posts, per_page=10,url=request.get_full_path())
    post_paginator.set_current_page(request.GET.get("page"))
    d = {  
        "post_paginator":post_paginator,
        "year":year,
        "date":date,
        "month":date.month,
        "day":date.day,
        "breadcrumb":breadcrumb
        }
    return render_to_response("blog/archive.html", d, context)

def forward(request):
    context = RequestContext(request)
    return HttpResponseRedirect('/editorial/')

# AJAX view for live blogging
def post_body(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404

    return HttpResponse(post.body)

# AJAX view for live blogging
def post_tease(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404

    arrow = '<p class="more span-15"><a href="%s">READ ON &raquo;</a></p>' % post.get_absolute_url()

    if not post.tease:
        return HttpResponse(truncatewords_html(post.body, 300) + arrow)

    return HttpResponse(post.tease + arrow)

def post_detail(request, slug, year, month, day, **kwargs):
    tt = time.strptime('%s-%s-%s' % (year, month, day),'%s-%s-%s' % ('%Y', '%b', '%d'))
    date = datetime.date(*tt[:3])
    post = None
    
    # incredibly, this sometimes returns multiple posts
    posts = Post.objects.filter(publish__year=date.year, publish__month=date.month, publish__day=date.day, slug=slug)
    for post in posts:
        if not post.is_reblog():
            post = post

    if not post:
        raise Http404
     
    breadcrumb = (('Editorial', '/editorial/'),)

    d = {  
        'post': post,
        'reblog_post': post.is_reblog(),
    }
    
    if post.can_view(request.user):
        if post.iframe_src:
            return render(request, 'blog/iframe_post_shell.html', {'post': post})
        elif post.is_reblog():
            return render_to_response('blog/reblog_post_detail.html', d, RequestContext(request))
        return render_to_response('blog/blog_post_detail.html', d, RequestContext(request))
    raise Http404


def post_detail_forward(request,post_id):
    try:
        post = Post.objects.get(id = post_id)
    except:
        post = None
    
    if post:
        return HttpResponseRedirect('%s' % (post.get_absolute_url()))
    else:
        return HttpResponseRedirect("/editorial/")
        

def old_post_forward(request):
    forwarded_id = request.GET.get('article')
    
    if forwarded_id:
        return HttpResponseRedirect("/editorial/%s" % forwarded_id)
    else:
        return HttpResponseRedirect("/editorial/")

def old_news_forward(request):
    '''
    forwarding for old site's tag urls
    '''
    timestamp = request.GET.get("timestamp")

    if timestamp:
        # clean up old malformed links to here
        timestamp = timestamp.replace(' ','')
        timestamp = timestamp.replace('\"','')
        timestamp = timestamp.replace('\'','')
        if len(timestamp) > 8:
            timestamp = timestamp[:8]
        dt = datetime.datetime.strptime(timestamp,'%Y%m%d')
        month = datetime.datetime.strftime(dt,"%b")
        return HttpResponseRedirect("/editorial/archive/%s/%s/%s/" % (dt.year, month, dt.day) )
    else:
        return HttpResponseRedirect("/editorial/archive/")

def old_month_forward(request):
    '''
    forwarding for old site's tag urls
    '''
    timestamp = request.GET.get("month")
    
    if timestamp:
        try:
            dt = datetime.datetime.strptime(timestamp,'%Y%m')
        except TypeError:
            return HttpResponse(status=404)

        month = datetime.datetime.strftime(dt,"%b")
        return HttpResponseRedirect("/editorial/archive/%s/%s/" % (dt.year, month) )
    else:
        return HttpResponseRedirect("/editorial/archive/")


def reblog_forward(request,reblog_id=None):
    
    if reblog_id:    
        try:
            post = ReblogPost.objects.get(reblog_post_id = reblog_id)
        except:        
            post = None
    else:
        reblog_id = request.GET.get("id")
        try:
            post = ReblogPost.objects.get(reblog_post_id = reblog_id)
        except:
            post = None
    
    
    if post == None:
        return HttpResponseRedirect("/editorial/")
    else:
        return HttpResponseRedirect('%s' % (post.get_absolute_url()))
    
def staff_blog(request):
    return HttpResponseRedirect("/editorial/")

def artist_profiles(request):    
    context = RequestContext(request)
    breadcrumb = (("Editorial","/editorial"),("Artist Profiles",None))
    posts = Post.objects.published().filter(artist_profile=True)
    
    image = None
    post_for_image = Post.objects.published().filter(artist_profile=True)[:1]
    for p in post_for_image:
        image = p.get_first_image()
    
    #give posts attributes for sorting
    for p in posts:
        p.artist_last = p.title.split()[-1]
        p.artist_title = p.title.replace("Artist Profile:", "")
        p.artist_last_letter = p.artist_last.split()[0][0]

    alpha = sorted(posts, key=attrgetter('artist_last_letter'))
    grouped = groupby(alpha, lambda x: x.artist_last_letter)

    # http://stackoverflow.com/questions/6906593/itertools-groupby-with-a-django-queryset
    grouped_profiles = [(letter, list(posts)) for letter, posts in grouped]    
        
    d = {  
        "section_title": "Artist Profiles",
        "grouped_profiles":grouped_profiles,
        "image": image,
        }
    return render_to_response("blog/artist_profiles.html", d, context)

def tag_list(request, template_name = 'blog/tag_list.html', **kwargs):
    """
    Category list

    Template: ``blog/category_list.html``
    Context:
        object_list
            List of categories.
    """
    context = RequestContext(request)
    object_list = Tag.objects.filter(type="editorial")
    tag_list_split = list(split_by(object_list, len(object_list)/2))
    tag_list_left = tag_list_split[0]
    tag_list_right= tag_list_split[1]
    breadcrumb = (("Editorial","/editorial"),("Tags", None))
    
    d = {  
    "tag_list_left":tag_list_left,
    "tag_list_right":tag_list_right,
    "breadcrumb":breadcrumb,
    }
    return render_to_response(template_name, d, context)


def tag_detail(request, slug, template_name = 'blog/tag_detail.html', **kwargs):
    """
    Tag detail

    Template: ``blog/tag_detail.html``
    Context:
        object_list
            List of posts specific to the given tag.
        tag
            Given tag.
    """
    
    # gotta add in some exception handling in case of duplicate tags
    tag = None
    
    try:
        tag = get_object_or_404(Tag, slug=slug, type="editorial")
    except:
        tags = Tag.objects.filter(slug=slug, type="editorial")[:1]
        for t in tags:
            tag = t
        
    if tag:
        queryset = TaggedItem.objects.get_by_model(Post, tag).filter(status=2).filter(publish__lte=datetime.datetime.now())
        if queryset:
            context = RequestContext(request)
            post_paginator = RhizomePaginator(queryset, per_page=10, url=request.get_full_path())
            page = request.GET.get("page")
            post_paginator.set_current_page(request.GET.get("page"))
            breadcrumb =  (("Editorial","/editorial"),("Tags", "/editorial/tags"),(tag.name,None))
        else:
            return HttpResponseRedirect("/editorial/")
    else:
        raise Http404
    
    d = {  
        "tag":tag,
        "post_paginator":post_paginator,
        "breadcrumb":breadcrumb,
        }
    return render_to_response(template_name, d, context)


def old_tag_forward(request):
    '''
    forwarding for old site's tag urls
    '''
    tag = request.GET.get("tag")
    
    if tag:
        return HttpResponseRedirect("/editorial/tag/%s/" % tag)
    else:
        return HttpResponseRedirect("/editorial/")

# Stop Words courtesy of http://www.dcs.gla.ac.uk/idom/ir_resources/linguistic_utils/stop_words
STOP_WORDS = r"""\b(a|about|above|across|after|afterwards|again|against|all|almost|alone|along|already|also|
although|always|am|among|amongst|amoungst|amount|an|and|another|any|anyhow|anyone|anything|anyway|anywhere|are|
around|as|at|back|be|became|because|become|becomes|becoming|been|before|beforehand|behind|being|below|beside|
besides|between|beyond|bill|both|bottom|but|by|call|can|cannot|cant|co|computer|con|could|couldnt|cry|de|describe|
detail|do|done|down|due|during|each|eg|eight|either|eleven|else|elsewhere|empty|enough|etc|even|ever|every|everyone|
everything|everywhere|except|few|fifteen|fify|fill|find|fire|first|five|for|former|formerly|forty|found|four|from|
front|full|further|get|give|go|had|has|hasnt|have|he|hence|her|here|hereafter|hereby|herein|hereupon|hers|herself|
him|himself|his|how|however|hundred|i|ie|if|in|inc|indeed|interest|into|is|it|its|itself|keep|last|latter|latterly|
least|less|ltd|made|many|may|me|meanwhile|might|mill|mine|more|moreover|most|mostly|move|much|must|my|myself|name|
namely|neither|never|nevertheless|next|nine|no|nobody|none|noone|nor|not|nothing|now|nowhere|of|off|often|on|once|
one|only|onto|or|other|others|otherwise|our|ours|ourselves|out|over|own|part|per|perhaps|please|put|rather|re|same|
see|seem|seemed|seeming|seems|serious|several|she|should|show|side|since|sincere|six|sixty|so|some|somehow|someone|
something|sometime|sometimes|somewhere|still|such|system|take|ten|than|that|the|their|them|themselves|then|thence|
there|thereafter|thereby|therefore|therein|thereupon|these|they|thick|thin|third|this|those|though|three|through|
throughout|thru|thus|to|together|too|top|toward|towards|twelve|twenty|two|un|under|until|up|upon|us|very|via|was|
we|well|were|what|whatever|when|whence|whenever|where|whereafter|whereas|whereby|wherein|whereupon|wherever|whether|
which|while|whither|who|whoever|whole|whom|whose|why|will|with|within|without|would|yet|you|your|yours|yourself|
yourselves)\b"""


def search(request, template_name='editorial/post_search.html'):
    """
    Search for blog posts.

    This template will allow you to setup a simple search form that will try to return results based on
    given search strings. The queries will be put through a stop words filter to remove words like
    'the', 'a', or 'have' to help imporve the result set.

    Template: ``blog/post_search.html``
    Context:
        object_list
            List of blog posts that match given search term(s).
        search_term
            Given search term.
    """
    context = {}
    if request.GET:
        stop_word_list = re.compile(STOP_WORDS, re.IGNORECASE)
        search_term = '%s' % request.GET['q']
        cleaned_search_term = stop_word_list.sub('', search_term)
        cleaned_search_term = cleaned_search_term.strip()
        if len(cleaned_search_term) != 0:
            post_list = Post.objects.published().filter(Q(body__icontains=cleaned_search_term) | Q(tags__icontains=cleaned_search_term) | Q(categories__title__icontains=cleaned_search_term))
            context = {'object_list': post_list, 'search_term':search_term}
        else:
            message = 'Search term was too vague. Please try again.'
            context = {'message':message}
    return render_to_response(template_name, context, context_instance=RequestContext(request))
