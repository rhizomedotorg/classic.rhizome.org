from itertools import chain
from operator import attrgetter, itemgetter
import datetime
import time
from dateutil.relativedelta import relativedelta
from itertools import chain

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import *
from django.core.paginator import Paginator, InvalidPage, EmptyPage 
from django.http import HttpResponse, HttpResponseRedirect
from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User, UserManager
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME, login as django_login
from django.contrib.auth import login as auth_login
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page

from programs.models import *
from accounts.models import RhizomeMembership 
from utils.template import RhizomePaginator
from utils.helpers import month_range
from accounts.decorators import membership_required


def index(request):
    context = RequestContext(request)     

    breadcrumb = (('Programs', '/programs/'),)
        
    return render_to_response(
        "programs/index.html", 
        {
        "section_title": "Rhizome Programs",
        "include_section_header":True,    
        'breadcrumb': breadcrumb,
         },
        context
    )

def events_list(request):
    context = RequestContext(request)    
    events = RhizEvent.objects.all().order_by("-start_date")
    upcoming_events = get_upcoming_events()
    past_events = get_past_events()
    past_events_paginator = RhizomePaginator(past_events, per_page=7, url=request.get_full_path())
    past_events_paginator.set_current_page(request.GET.get("page"))

    breadcrumb = (('Programs', '/programs/'), ('Events', None))

    return render_to_response(
        "programs/events_list.html", {
            "upcoming_events":upcoming_events,
            "past_events_paginator":past_events_paginator,
            'breadcrumb': breadcrumb
        },
        context
    )

def event_details(request,slug):
    context = RequestContext(request)    
    event = get_object_or_404(RhizEvent, slug = slug)
    
    return render_to_response(
            "programs/event_detail.html", 
            {"event":event,
             },
            context
        )

def exhibitions_list(request):
    context = RequestContext(request)    
    upcoming_exhibitions = get_upcoming_exhibitions()
    past_exhibitions = get_past_exhibitions()    
    past_exhibitions_paginator = RhizomePaginator(past_exhibitions, per_page=7, url=request.get_full_path())
    past_exhibitions_paginator.set_current_page(request.GET.get("page"))

    breadcrumb = (('Programs', '/programs/'), ('Exhibition', None))

    return render_to_response(
        "programs/exhibitions_list.html", {
            "past_exhibitions_paginator":past_exhibitions_paginator,
            "upcoming_exhibitions":upcoming_exhibitions,
            'breadcrumb': breadcrumb
        },
        context
    )

def exhibition_details(request,slug):
    context = RequestContext(request)    
    exhibition = get_object_or_404(Exhibition,slug = slug)

    return render_to_response(
            "programs/exhibition_detail.html", 
            {"exhibition":exhibition,},
            context
        )

def video_index(request):
    context = RequestContext(request)    
    videos = Video.objects.all().order_by("-video_date")
            
    #create the pages    
    paginator = Paginator(videos, 25)
           
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        videos_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        videos_page = paginator.page(paginator.num_pages)
    
    try:
        is_member = request.user.is_rhizomemember()
    except:
        is_member = False
    
    return render_to_response(
        "programs/videos_index.html", 
        {"videos_page":videos_page,
         "is_member":is_member},
        context
    )
    
def video_details(request,id):
    context = RequestContext(request)    
    video = Video.objects.get(pk = id)
    
    try:
        is_member = request.user.is_rhizomemember()
    except:
        is_member = False


    return render_to_response(
            "programs/videos_detail.html", 
            {"video":video,
             "is_member":is_member},
            context
        )

def downloadofthemonth(request):
    context = RequestContext(request)
    downloads = DownloadOfTheMonth.objects.filter(is_active=True).order_by('-premier_date')
       
    d = {
        "current_download":downloads[0],
        "archive_listings":downloads,
        "section_title": 'The Download',
        "include_section_header":True,  
    }
    
    return render_to_response(
        "programs/thedownload/the-download.html", d, context 
    )

def downloadofthemonth_detail(request, year, month):
    context = RequestContext(request)
    breadcrumb = (("Programs","/programs/"),("The Download", None))  
    
    tt = time.strptime('%s-%s' % (year, month,),'%s-%s' % ('%Y', '%b'))    
    requested_date = datetime.date(*tt[:3])

    try:
        current_download = DownloadOfTheMonth.objects.get(
                premier_date__year = requested_date.year, 
                premier_date__month = requested_date.month
            )
        if current_download.is_active or request.user.is_staff:        
            all_downloads =  DownloadOfTheMonth.objects.exclude(is_active=False)
           
            d = {
                "current_download":current_download,
                "archive_listings":all_downloads,
                "breadcrumb":breadcrumb,
                "section_title": "The Download",
                "include_section_header":True,  
                }
            
            return render_to_response(
                "programs/thedownload/the-download.html", d, context 
            )
        else:
            return HttpResponseRedirect("/the-download/")
    except ObjectDoesNotExist:
        return HttpResponseRedirect("/the-download/")
