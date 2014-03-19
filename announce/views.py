from urllib import urlencode
import urllib2
from time import time
import datetime
from itertools import chain
import time
import decimal

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import *
from django.contrib.auth.models import User 
from django.core.paginator import Paginator, InvalidPage, EmptyPage 
from django.http import HttpResponse, HttpResponseRedirect,Http404
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.html import strip_tags
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page

from mailinglists.signals import send_to_announce_mailing_list
from utils.template import RhizomePaginator
from utils.helpers import split_by
from announce.models import *
from announce.forms import *
from utils.imaging import create_thumbnail
from accounts.models import RhizomeMembership 
from utils.payments import call_authorizedotnet, call_authorizedotnet_capture
from accounts.forms import UserBillingAddressForm


###
## VIEWS
###

def index(request):
    context = RequestContext(request)    
    announcements = get_latest_announcements()
    announce_paginator = RhizomePaginator(announcements, per_page=15, url=request.get_full_path())
    page = request.GET.get("page")
    announce_paginator.set_current_page(request.GET.get("page"))

    breadcrumb = (('Community', '/community/'), ('Announce', None))
        
    d = {"include_section_header": True,
         "section_title": "Rhizome Announce",
         "section_action": "submit",     
         "announce_paginator":announce_paginator,
         "include_section_header":True,
         'breadcrumb': breadcrumb
         }
    
    return render_to_response("announce/index.html",d,context)

def deadlines(request):
    context = RequestContext(request)    
    deadlines = get_announcements_by_deadline()
    announce_paginator = RhizomePaginator(deadlines, per_page=15, url=request.get_full_path())
    page = request.GET.get("page")
    announce_paginator.set_current_page(request.GET.get("page"))
        
    d = {"include_section_header": True,
         "section_title": "Rhizome Announce: Upcoming Deadlines",
         "section_action": "../events/submit",     
         "announce_paginator":announce_paginator,
         "include_section_header":True
         }
    
    return render_to_response("announce/deadlines.html",d,context)

def events(request):
    from models import EVENT_SUB_TYPES
    sub_types = EVENT_SUB_TYPES
    context = RequestContext(request)    
    auto_checks=[]
    sub_types_grouped = list(split_by(sub_types, 3))
    today = datetime.date.today()
    interval =  today + datetime.timedelta(days=365)
        
    if request.GET:
        #check to see if there are multiple filter values or one single filter value
        if len(request.GET) > 1 or request.GET.get("page") == None and not request.GET.get("refresh"):
            filtered_objects = []
            filtered_append = filtered_objects.append
            for get in request.GET:
                if get != "page" and get != "refresh":
                    '''
                    filter objects via get variables
                    '''
                    get_objects = Event.objects.filter(status=1) \
                        .filter(start_date__lte = interval) \
                        .filter(start_date__gte = today) \
                        .filter(subtype = get).filter(status=1) \
                        .order_by("start_date")
                    for object in get_objects:
                        filtered_append(object)
                    auto_checks.append(get)
                                                           
            sorted_objects = sorted(filtered_objects,key=attrgetter('start_date'),reverse=False)   
            events_count = len(sorted_objects)
            events_paginator = RhizomePaginator(sorted_objects, per_page=20, url=request.get_full_path())
                   
        else:
            '''
            just asking for pages, load unfiltered page
            '''
            events = Event.objects \
                .filter(status=1) \
                .filter(start_date__lte = interval) \
                .filter(start_date__gte = today) \
                .order_by("start_date")
            events_count = len(events)
            events_paginator = RhizomePaginator(events, per_page=20, url=request.get_full_path())
            
    else:
        '''
        load normal page
        '''
        events = Event.objects \
            .filter(status=1) \
            .filter(start_date__lte = interval) \
            .filter(start_date__gte = today) \
            .order_by("start_date")
        events_count = len(events)
        events_paginator = RhizomePaginator(events, per_page=20, url=request.get_full_path())
          
    events_paginator.set_current_page(request.GET.get("page"))
    
    d = {
         "include_section_header": True,
         "section_title": "Rhizome Events",
         "section_action": "submit",     
         "announce_paginator":events_paginator,
         "include_section_header":True,
         "events_count":events_count,
         "auto_checks":auto_checks,
         "sub_types_grouped":sub_types_grouped,
         }    
    return render_to_response("announce/events.html",d,context)

def opportunities(request):
    from models import OPPORTUNITY_SUB_TYPES
    context = RequestContext(request)    
    sub_types = OPPORTUNITY_SUB_TYPES
    auto_checks=[]
    sub_types_grouped = list(split_by(sub_types, 4))
    now = datetime.datetime.now()

    if request.GET:
        #check to see if there are multiple filter values or one single filter value
        if len(request.GET) > 1 or request.GET.get("page") == None and not request.GET.get("refresh"): 
            filtered_objects = []
            filtered_append = filtered_objects.append
            for get in request.GET:
                if get != "page":
                    get_objects = Opportunity.objects \
                        .filter(subtype = get) \
                        .filter(status = 1) \
                        .filter(deadline__gte = now) \
                        .order_by("deadline")
                    for object in get_objects:
                        filtered_append(object)
                    auto_checks.append(get)
                                                       
            sorted_objects = sorted(filtered_objects,key=attrgetter('deadline'))   
            opportunities_count = len(sorted_objects)
            opportunites_paginator = RhizomePaginator(sorted_objects, per_page=20, url=request.get_full_path())

        else:
            opportunites = Opportunity.objects \
                .filter(status=1) \
                .filter(deadline__gte = now) \
                .order_by("deadline") 
            opportunities_count = len(opportunites)
            opportunites_paginator = RhizomePaginator(opportunites, per_page=20, url=request.get_full_path())
                   
    else:
        opportunites = Opportunity.objects \
            .filter(status=1) \
            .filter(deadline__gte = now) \
            .order_by("deadline") 
        opportunities_count = len(opportunites)
        opportunites_paginator = RhizomePaginator(opportunites, per_page=20, url=request.get_full_path())
  
    opportunites_paginator.set_current_page(request.GET.get("page"))
        
    d = {
         "include_section_header": True,
         "section_title": "Rhizome Opportunities",
         "section_action": "submit",     
         "announce_paginator":opportunites_paginator,
         "include_section_header":True,
         "opportunities_count":opportunities_count,
         "auto_checks":auto_checks,
         "sub_types_grouped":sub_types_grouped,
         }
    
    return render_to_response("announce/opportunities.html",d,context)

def jobs_forward(request):
    return HttpResponseRedirect("/announce/jobs/")

def jobs(request):
    if request.GET.get("gclid"):
        return HttpResponseRedirect("/announce/jobs/")
        
    from models import JOB_SUB_TYPES
    sub_types = JOB_SUB_TYPES
    context = RequestContext(request) 
    auto_checks=[]
    now = datetime.datetime.now()

    breadcrumb = (('Community', '/community/'), ('Jobs Board', None))
    
    if request.GET:
        if len(request.GET) > 1 or request.GET.get("page") == None and not request.GET.get("refresh"):
            filtered_objects = []
            filtered_append = filtered_objects.append
            for get in request.GET:
                if get != "page":
                    get_objects = Job.objects \
                        .filter(subtype = get) \
                        .filter(status=1) \
                        .filter(deadline__gte = now) \
                        .order_by("deadline")
                    for object in get_objects:
                        filtered_append(object)
                    auto_checks.append(get)
                                                       
            sorted_objects = sorted(filtered_objects,key=attrgetter('deadline'),reverse=True)   
            jobs_count = len(sorted_objects)
            jobs_paginator = RhizomePaginator(sorted_objects, per_page=20, url=request.get_full_path())
        else:
            jobs = Job.objects \
                .filter(status=1) \
                .filter(deadline__gte = now) \
                .order_by("deadline")
            jobs_count = len(jobs)
            jobs_paginator = RhizomePaginator(jobs, per_page=20, url=request.get_full_path())
                   
    else:
        jobs = Job.objects \
            .filter(status=1) \
            .filter(deadline__gte = now) \
            .order_by("deadline")
        jobs_count = len(jobs)
        jobs_paginator = RhizomePaginator(jobs, per_page=20, url=request.get_full_path())
    
    jobs_paginator.set_current_page(request.GET.get("page"))
        
    d = {"include_section_header": True,
         "section_title": "Rhizome Jobs Board",
         "section_action": "submit",     
         "announce_paginator":jobs_paginator,
         "include_section_header":True,
         "jobs_count":jobs_count,
         "sub_types":sub_types,
         "auto_checks":auto_checks,
         'breadcrumb': breadcrumb
         }
    
    return render_to_response("announce/jobs.html",d,context)
    
def legacy_view_forward(request, id):
    '''
    handles viewing of announcements via old site's urls. 
    can produce the wrong match since now opps, events, and jobs 
    are separate tables and thus could have duplicate ids
    '''
    try:
        announcement = Opportunity.objects.get(pk=id)
    except ObjectDoesNotExist:
        try:
            announcement = Event.objects.get(pk=id)
        except ObjectDoesNotExist:
            try:
                announcement = Job.objects.get(pk=id)                
            except:
                raise Http404

    if not announcement:
        raise Http404
    else:
        if announcement.type == "opportunity":
            return HttpResponseRedirect(reverse(post_detail,kwargs={'type':'opportunities','id':announcement.id}))
 
        if announcement.type == "event":
            return HttpResponseRedirect(reverse(post_detail,kwargs={'type':'events','id':announcement.id}))

        if announcement.type == "job":
            #return HttpResponseRedirect('/announce/jobs/%s/view/' % (announcement.id)) 
            return HttpResponseRedirect(reverse(post_detail,kwargs={'type':'jobs','id':announcement.id}))
 
            
            
def post_detail(request, type, id):
    context = RequestContext(request)   
        
    if type == 'opportunities':
        announcement = get_object_or_404(Opportunity, id=id, is_spam=False)
    elif type == 'jobs':
        announcement = get_object_or_404(Job, id=id, is_spam=False)
    elif type == 'events':
        announcement = get_object_or_404(Event, id=id, is_spam=False)
    elif type == None:
        raise Http404
    else:
        raise Http404
    
    if announcement.status: #check to make sure it's live
        return render_to_response(
            "announce/post_detail.html",
            {
            "announcement": announcement,
            "type": type
            },
            context
            )    
    elif announcement.user == request.user:
        return HttpResponseRedirect(reverse(preview,kwargs={'type':type,'id':announcement.id}))                    
    else:
        raise Http404

def email(request, type, id):
    context = RequestContext(request)   
        
    if type == 'opportunities':
        announcement = get_object_or_404(Opportunity, id=id)
    elif type == 'jobs':
        announcement = get_object_or_404(Job, id=id)
    elif type == 'events':
        announcement = get_object_or_404(Event, id=id)
    elif type == None:
        raise Http404
    else:
        raise Http404
    
    return render_to_response(
        "announce/email_templates/announcement.html",
        {
        "announcement": announcement,
        "type": type
        },
        context
        )    

def preview(request, type, id):
    context = RequestContext(request)   
    
    if type == 'opportunities':
        announcement = get_object_or_404(Opportunity, id=id, is_spam=False)
    elif type == 'jobs':
        announcement = get_object_or_404(Job, id=id, is_spam=False)
    elif type == 'events':
        announcement = get_object_or_404(Event, id=id, is_spam=False)
    elif type == None:
        raise Http404
    else:
        raise Http404

    #check to make sure it's not live and user owns it
    if announcement.user == request.user:
        return render_to_response(
            "announce/post_detail.html",
            {"announcement": announcement,
            "type": type
            },
            context
            )    
    else:
        return HttpResponseRedirect(reverse(post_detail,kwargs={'type':'opportunities','id':announcement.id}))
        
@login_required  
def submit(request, type = None):
    context = RequestContext(request)
    
    if type == 'opportunities':   
        announcement_form = OpportunityForm()
    if type == 'jobs':   
        announcement_form = JobForm()
    if type == 'events':   
        announcement_form = EventForm()
    if type == None:
        type = "opportunities"
        announcement_form = OpportunityForm()

    if request.method == 'POST':
        if request.POST.get("form-type") == "opportunity-form":
            announcement_form = OpportunityForm(request.POST, request.FILES or None)
            
        if request.POST.get("form-type") == "job-form":
            announcement_form = JobForm(request.POST, request.FILES or None)
            
        if request.POST.get("form-type") == "event-form":  
            announcement_form = EventForm(request.POST, request.FILES or None)
                        
        if announcement_form.is_valid():
            announcement = announcement_form.save(commit=False)
            announcement.user_id = request.user.id
            announcement.username = strip_tags(request.user.get_profile())
            announcement.title = strip_tags(announcement.title)
            announcement.url = strip_tags(announcement.url)
            announcement.description = strip_tags(announcement.description)
            announcement.subtype = strip_tags(announcement.subtype)
            announcement.ip_address = request.META["REMOTE_ADDR"]
            announcement.status = False
            
            #save now so can create thumbanail with id in title
            announcement.save()             
            
            if announcement.image:
                #create_thumbnails uses saved image
                announcement.thumbnail = create_thumbnail(announcement.image)
                announcement.save()#save again after creating thumbnail                       

            if request.POST.get("status") == "preview":
                #return HttpResponseRedirect('/announce/%s/%s/preview/' % (type, announcement.id))
                return HttpResponseRedirect(reverse(preview,kwargs={'type':type,'id':announcement.id}))
            
            elif request.POST.get("status") == "publish":
                if type == 'jobs' and not announcement.is_paid() and not request.user.get_profile().is_member():
                    return HttpResponseRedirect(reverse(job_payment))
                
                if not moderator.process(announcement, request):
                    announcement.status = True
                    announcement.save()
                    send_to_announce_mailing_list(announcement.__class__, announcement, created=True)
                
                return HttpResponseRedirect(reverse(thanks, kwargs={'type':type,'id':announcement.id}))
                    
                
    return render_to_response(
        "announce/submit.html",
        {"announcement_form":announcement_form, "type":type},
        context
        )

@login_required  
def edit(request, type, id):
    context = RequestContext(request)
    username = request.user.get_profile()       
        
    #CHECK THE TYPE, GRAB OBJECT OR CATCH MISSING INFO
    if type == 'opportunities':
        announcement = get_object_or_404(Opportunity, id=id, is_spam=False)
        announcement_form = OpportunityForm(
                                request.POST or None, 
                                request.FILES or None, 
                                instance=announcement, 
                                initial={'username':username}
                            )
    elif type == 'jobs':
        announcement = get_object_or_404(Job, id=id, is_spam=False)
        announcement_form = JobForm(
                                request.POST or None, 
                                request.FILES or None, 
                                instance=announcement,  
                                initial={'username':username}
                                )
    elif type == 'events':
        announcement = get_object_or_404(Event, id=id, is_spam=False)
        announcement_form = EventForm(
                                request.POST or None, 
                                request.FILES or None, 
                                instance=announcement, 
                                initial={'username':username}
                            )
    else:
        raise Http404
    
    if not announcement.can_edit():
        # can only edit if announcement less than 2 wks old...    
        return HttpResponseRedirect(reverse('announce_index'))  
    else:
        # MAKE SURE THE USER OWNS THE ANNOUNCEMENT
        if request.user != announcement.user:
            return HttpResponseRedirect(reverse('announce_index'))  
        else:
            # HANDLE THE POST
            if request.method == 'POST':
            
                if request.POST.get("form-type") == "opportunity-form":
                    announcement_form = OpportunityForm(
                                            request.POST, 
                                            request.FILES or None, 
                                            instance=announcement, 
                                            initial={'username':username}
                                        )
                if request.POST.get("form-type") == "job-form":
                    announcement_form = JobForm(
                                            request.POST, 
                                            request.FILES or None, 
                                            instance=announcement, 
                                            initial={'username':username}
                                        )
                if request.POST.get("form-type") == "event-form":  
                    announcement_form = EventForm(
                                            request.POST, 
                                            request.FILES or None, 
                                            instance=announcement, 
                                            initial={'username':username}
                                            )
           
                if announcement_form.is_valid():
                    announcement = announcement_form.save(commit=False)
                    announcement.user_id = request.user.id
                    announcement.ip_address = request.META["REMOTE_ADDR"]
                    
                    if request.POST.get("delete_image"):
                        if announcement.image:
                            import os
                            if os.path.exists(announcement.image.path):
                                os.remove(announcement.image.path)
                        announcement.image = None
                    
                    #save now so can create thumbanail with id in title
                    announcement.save() 
                    
                    if announcement.image and not announcement.thumbnail:
                        announcement.thumbnail = create_thumbnail(announcement.image)
                        announcement.save()           
                    
                    ####
                    # if announcement is not yet published
                    ####
                    if request.POST.get("status") == "preview":
                        announcement.status = False
                        announcement.save()
                        return HttpResponseRedirect(reverse(preview, kwargs={'type':type, 'id':announcement.id}))                    
                        
                    if request.POST.get("status") == "publish":

                        if type == 'jobs' and not announcement.is_paid() and not request.user.get_profile().is_member():
                            return HttpResponseRedirect(reverse(job_payment))

                        if not moderator.process(announcement, request):
                            announcement.status = True
                            announcement.save()
                            send_to_announce_mailing_list(announcement.__class__, announcement, created=True)
 
                        return HttpResponseRedirect(reverse(thanks, kwargs={'type':type,'id':announcement.id}))

                    
                    ####
                    # if announcement is published
                    ####
                    if request.POST.get("status") == "unpublish":
                        announcement.status = False
                        announcement.save()
                        #return HttpResponseRedirect('/announce/%s/%s/preview/' % (type, announcement.id))
                        return HttpResponseRedirect(reverse(edit,kwargs={'type':type,'id':announcement.id}))

                    if request.POST.get("status") == "update":
                        moderator.process(announcement, request)
                            
                        #return HttpResponseRedirect('/announce/%s/%s/preview/' % (type, announcement.id))
                        return HttpResponseRedirect(reverse(thanks,kwargs={'type':type,'id':announcement.id}))
                
                    else:
                        if type == 'opportunities':   
                            announcement_form = OpportunityForm(request.POST)
                        if type == 'jobs':   
                            announcement_form = JobForm(request.POST)
                        if type == 'events':   
                            announcement_form = EventForm(request.POST)       
        
        return render_to_response(
            "announce/submit.html",
            {"announcement_form":announcement_form,
            "type": type  
            }, 
            context
            )

@login_required  
def thanks(request, type, id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/announce/')
    
    context = RequestContext(request) 
    user_id = request.user.id
    
    if type == 'opportunities':
        announcement = get_object_or_404(Opportunity, id=id, is_spam=False)
    elif type == 'jobs':
        announcement = get_object_or_404(Job, id=id, is_spam=False)
    elif type == 'events':
        announcement = get_object_or_404(Event, id=id, is_spam=False)
    elif type == None:
        raise Http404
    else:
        raise Http404
    
    if request.user == announcement.user:
        return render_to_response("announce/post_detail.html", {"announcement":announcement,"type": type,"thanks":True  }, context )    
    else:
        return HttpResponseRedirect(reverse(index))

##CALENDAR LISTINGS
@csrf_exempt
def calendar_listing(request, ref_type, year, month, day):
    context = RequestContext(request)
    
    tt = time.strptime('%s-%s-%s' % (year, month, day),'%s-%s-%s' % ('%Y', '%m', '%d'))
    formatted_date = datetime.date(*tt[:3])
    
    if ref_type == "fp":  
        try:
            date_listings = Event.objects.filter(
                                start_date__year = formatted_date.year, 
                                start_date__day = formatted_date.day, 
                                start_date__month = formatted_date.month, 
                                status=True
                            )

        except:
            date_listings = None
        
        return render_to_response("announce/fp_listing.html", 
            {
            "date_listings":date_listings,
            "date":formatted_date,
            }
            ,context)
            
    if ref_type == "widget":  
        try:
            events = Event.objects.filter(
                        start_date__year = formatted_date.year, 
                        start_date__day = formatted_date.day, 
                        start_date__month = formatted_date.month, 
                        status=True
                    )
        except:
            events = []
        
        try:
            jobs = Job.objects.filter(
                        deadline__year = formatted_date.year, 
                        deadline__day = formatted_date.day, 
                        deadline__month = formatted_date.month, 
                        status=True
                    )
        except:
            jobs = []
        
        try:
            opportunities = Opportunity.objects.filter(
                                deadline__year = formatted_date.year, 
                                deadline__day = formatted_date.day, 
                                deadline__month = formatted_date.month, 
                                status=True
                            )

        except:
            opportunities = []
        
        date_listings = sorted(chain(events, opportunities, jobs))
        # except:
#             date_listings = None

        return render_to_response("announce/widget_listing.html", 
            {
            "date_listings":date_listings,
            "date":formatted_date,
            },
            context)

@login_required  
def job_payment(request):
    context = RequestContext(request)
    user = request.user
    notice = ''
    try:
        job = Job.objects.filter(user=user).latest('created')
    except:
        HttpResponseRedirect("/announce/")
            
    breadcrumb = (("Announce","/announce"),("Job Posting",""))
    job_amount = 25.00

    job_payment_form = JobPaymentForm(initial= {"first_name":user.first_name, 
                                                "last_name":user.last_name, 
                                                "amount":job_amount})
    
    billing_address_form = UserBillingAddressForm(initial= {"user":user,
                                                            "address_type":'billing'},
                                                            prefix="billing")
        
    if request.method == 'POST':
        job_payment_form = JobPaymentForm(request.POST,initial= {"amount":job_amount})
        billing_address_form = UserBillingAddressForm(request.POST, prefix="billing")

        if job_payment_form.is_valid() and billing_address_form.is_valid():
            payment = job_payment_form.save(user, job, commit=False)
            billing_address = billing_address_form.save(user)            

            verify_call = call_authorizedotnet(
                            "%s" % unicode(job_payment_form.cleaned_data["amount"]), 
                            job_payment_form.cleaned_data["cc_number"], 
                            job_payment_form.cleaned_data["cc_exp_date"], 
                            job_payment_form.cleaned_data["cc_card_code"], 
                            "%s %s" %(billing_address.street1, billing_address.street2),
                            billing_address.city,
                            billing_address.state,
                            billing_address.zip_postal_code, 
                            billing_address.country,
                            user.first_name, 
                            user.last_name, 
                            user.id, 
                            user.email, 
                            "Job Payment", 
                            )
                        
            ##VERIFICATION WORKED, NOW CAPTURE THE TRANSACTION
            if verify_call.split('|')[0] == '1':
                job.status = True
                job.save()
                payment.save()
                payment.send_receipt()
                return HttpResponseRedirect(reverse(job_payment_thanks, kwargs={'job_id':job.id}))
           
            #VERIFICATION DIDN'T WORK
            else:   
               notice = verify_call.split('|')[3]
                    
        #ONE OF THE FORMS DIDN'T VALIDATE (DJANGO VALIDATION) 
        else:
            notice = "There were problems with the information you submitted."
    
    return render_to_response("announce/job_payment.html", {
                              "job":job,
                              "job_payment_form":job_payment_form,
                              "breadcrumb":breadcrumb,
                              "notice":notice,
                              "job_amount":job_amount,
                              "paypal_email":settings.PAYPAL_RECEIVER_EMAIL,
                              "paypal_url":settings.PAYPAL_POSTBACK_URL,
                              "billing_address_form":billing_address_form
                              }, 
                            context) 
@login_required    
def job_payment_thanks(request, job_id):
    context = RequestContext(request)
    announcement = ''
    
    job = Job.objects.get(pk = job_id, is_spam=False)
    
    if not job.status:
        job.status = True
        job.save()  
    
    if request.GET.get("tx"):
        #paypal payment, so create payment and send receipt
        amount = decimal.Decimal('25.00')
        payment = JobPostingPayment(user=request.user, job=job, amount=amount)
        payment.save()
        payment.send_receipt()

    if not job.has_been_sent_to_list():
        send_to_announce_mailing_list(job.__class__, job, created=True)

    return render_to_response("announce/job_payment_thanks.html", {"announcement":job,}, context) 
