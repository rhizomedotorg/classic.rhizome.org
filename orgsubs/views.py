from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import *
from django.contrib.auth.models import User 
from django.core.paginator import Paginator, InvalidPage, EmptyPage 
from django.http import HttpResponse, HttpResponseRedirect
from django.template.context import RequestContext
from django.shortcuts import render_to_response
import datetime
from models import *
from utils.template import RhizomePaginator
from django.core.exceptions import ObjectDoesNotExist

def index(request):
    organizations = Organization.objects.all()
    context = RequestContext(request)    
    orgsub_paginator = RhizomePaginator(organizations, per_page=20, url=request.get_full_path())
    page = request.GET.get("page")
    #ip = request.META['HTTP_X_FORWARDED_FOR'] # for remote server with load balancing proxy 
    ip = request.META['REMOTE_ADDR']# for production server
    ip_access = is_ip_org_sub(ip)
    #organizations.set_current_page(request.GET.get("page"))
        
    d = {"include_section_header": True,
         "section_title": "Organizations ",
         "organizations":organizations,
         "include_section_header":True,
         "ip_access":ip_access,
         "ip":ip
         }
    
    return render_to_response("orgsubs/index.html",d,context)