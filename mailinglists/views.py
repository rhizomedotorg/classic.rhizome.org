import random
import urllib2

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from mailinglists.models import *
from mailinglists.forms import *
from blog.models import  get_featured_articles
from announce.models import get_latest_opps, get_latest_events
from discuss.models import DiscussionThread
from programs.models import DownloadOfTheMonth

def subscribe(request):
    context = RequestContext(request)
    breadcrumb = (('Community', '/community/'),("Subscribe", None),)

    user = request.user
    
    if user.is_authenticated():
        initial_list_data = [l.listid for l in Member.objects.filter(user=request.user, deleted = 0) ]
        subscribe_form = SubscribeForm(request.POST or None, initial={'mailinglists':initial_list_data, "email":user.email})
    else:
        subscribe_form = SubscribeForm()
    
    notice = ''
    
    if request.GET.get('e'):
        for e in  request.GET.get('e'):
            if e != ",":
                mailinglist = List.objects.get(pk = e)
                notice = notice + ("<li>You're already signed up for %s</li>" % mailinglist.title)
            
    if request.GET.get('s'):
        for s in  request.GET.get('s'):
            if s != ",":
                mailinglist = List.objects.get(pk = s)
                notice = notice + "<li>You've been registered for %s</li>" % mailinglist.title
                             
    if request.method == 'POST':
        subscribe_form = SubscribeForm(request.POST)     

        if subscribe_form.is_valid():
            notice = subscribe_form.save(request)     
            existing = ','.join([n for n in notice["existing"]])
            subscribed = ','.join([n for n in notice["subscribed"]])
            return HttpResponseRedirect("/subscribe/?e=%s&s=%s#mailinglists" % (existing, subscribed))             
            
    return render_to_response("mailinglists/subscribe.html", {
        'subscribe_form': subscribe_form,
        'notice':notice,
        'breadcrumb': breadcrumb
        },
        context
    )

def unsubscribe(request):
    context = RequestContext(request)
    notice = ''
    user =request.user
    breadcrumb = (("Unsubscribe", None),)
    
    if user.is_authenticated():
        initial_list_data = [l.listid for l in Member.objects.filter(user=request.user, deleted = 0) ]
        unsubscribe_form = UnsubscribeForm(request.POST or None, initial={'email':request.user.email, 'mailinglists':initial_list_data})
    else:
        unsubscribe_form = UnsubscribeForm()


    if request.GET.get('n'):
        for n in  request.GET.get('n'):
            if n != ",":
                mailinglist = List.objects.get(pk = n)
                notice = notice + ("<li>You're not signed up for %s</li>" % mailinglist.title)
            
    if request.GET.get('u'):
        for u in  request.GET.get('u'):
            if u != ",":
                mailinglist = List.objects.get(pk = u)
                notice = notice + "<li>You've been removed from %s</li>" % mailinglist.title
    
    
    if request.method == 'POST':
        unsubscribe_form = UnsubscribeForm(request.POST)     

        if unsubscribe_form.is_valid():
            notice = unsubscribe_form.save(request)     
            unsubscribed = ','.join([n for n in notice["unsubscribed"]])
            notsubscribed = ','.join([n for n in notice["notsubscribed"]])
            return HttpResponseRedirect("/unsubscribe/?n=%s&u=%s#mailinglists"  % (notsubscribed, unsubscribed))             

    return render_to_response("mailinglists/unsubscribe.html", {
        'unsubscribe_form': unsubscribe_form,
        'notice':notice,
        'breadcrumb': breadcrumb
        },
        context
    )

    
def confirm(request, listid):
    context = RequestContext(request)
    email = request.GET.get("email")
    breadcrumb = (("Subscribe","/subscribe/"), ("Confirm", None),)
    notice = ''
    listmember = None
    mailinglist = None

    if email and email != '':
        try:
            listmember = Member.objects.get(email= email, listid=listid)
        except:
            listmember = None
        
        if listmember:
            listmember.confirmed = 1
            listmember.approved = 1
            listmember.save()
            mailinglist = List.objects.get(pk=listid)
        else:
            notice = "<p class='red'>Uh-oh, we can't find your email address. Please try to <a href='/subscribe'>subscribe again</a>.</p>"
    else:
        notice = "<p class='red'>Uh-oh, we can't find your email address. Please try to <a href='/subscribe'>subscribe again</a>.</p>"

    return render_to_response("mailinglists/confirm.html", {
        'notice': notice,
        'listmember': listmember,
        'mailinglist':mailinglist,
        'breadcrumb': breadcrumb
        },
        context
    )
    
def newsletter(request):
    context = RequestContext(request)
    newsletter = Newsletter.objects.order_by('-created')[0]
        
    # check the nectar ads server for banner ads
    ad_url = 'http://engine.adzerk.net/s/12843/0/104/676357998653446822586'
    banner_ad = False

    try:
        resp = urllib2.urlopen(ad_url, timeout = 10)
    except urllib2.URLError, e:
        # something up with url, error or doesn't exist
        pass
    else:
        banner_ad = True 
    
    try:
        authors = newsletter.article().authors.all()
    except:
        authors = None
        
        
    return render_to_response('mailinglists/newsletter.html', {
        'article': newsletter.article(),
        'newsletter': newsletter,
        'featured_articles':get_featured_articles(5),
        'authors': authors,
        'events':get_latest_events(5),
        'opps': get_latest_opps(5),
        'threads': DiscussionThread.objects.filter(is_public=True)[:5],
        'banner_ad':banner_ad,
        'random_int': random.randrange(100, 1000),   
        },
        context
    )

def member_newsletter(request):
    context = RequestContext(request)
    try:
        member_newsletter = MemberNewsletter.objects.order_by('-created')[0]
    except:
        member_newsletter = None

    return render_to_response("mailinglists/member_newsletter.html", {
        'newsletter': member_newsletter,
        'featured_articles':get_featured_articles(5),
        'events':get_latest_events(5),
        'opps': get_latest_opps(5),
        'threads': DiscussionThread.objects.filter(is_public=True)[:5],
        'download': DownloadOfTheMonth.objects.latest('premier_date')
        },
        context
    )



