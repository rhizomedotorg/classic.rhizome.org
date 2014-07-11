import urllib, urllib2
import datetime

from django.contrib import admin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.conf.urls.defaults import *
from django import template
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
import django.db.models.options as options

from pychimp import PyChimp

from blog.models import *
from mailinglists.models import *

def get_page_html(url):
    page_url = urllib.urlopen(url)
    page_html = page_url.read()
    page_url.close
    return page_html       
        
class NewsletterAdmin(admin.ModelAdmin):
    model = Newsletter
    ordering = ('created',)
    raw_id_fields = ("post",)

    class Meta:
        news_actions = (('send', 'Send the News'), )
                
    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
             url(r'send/$', self.admin_site.admin_view(self.send_news), name='Send the News',),
        ) + super(NewsletterAdmin, self).get_urls()

    def send_news(self, request):

        mailchimp_api = PyChimp('3cb8530ce9770dc992d48f579b6bb09a-us1') 
        mailchimp_return_error_notice = ''
        mailchimp_return_success_notice = ''
        site = Site.objects.get(id=1)
        context_instance = RequestContext(request)
        newsletter = Newsletter.objects.order_by('-created')[0] 
        today = datetime.date.today()
        news_url = 'https://%s/editorial/news/' % site.domain
        article = newsletter.article()
        from_name = "RHIZOME NEWS"
        from_email = "news@rhizome.org"
        to_email = ""
        formatted_date =  today.strftime('%m.%d.%y')
        
        #get news and test lists
        for mailchimp_list in mailchimp_api.lists():
            if mailchimp_list["name"] == "Rhizome News":
                rhiz_news_list = mailchimp_list
            if mailchimp_list["name"] == "Test List":    
                test_list = mailchimp_list    
        
        if request.method == 'POST':
        
            mailchimp_opts = {
                "list_id": rhiz_news_list["id"],
                "subject": request.POST["subject"],
                "from_name": request.POST["from_name"],
                "from_email": request.POST["from_email"],
                "to_email": request.POST["to_email"],
                "tracking": {'opens':True, 'html_clicks':True,'text_clicks':True},
                "authenticate":True,
                "title": "RHIZOME NEWS: %s" % formatted_date,
                "generate_text": True
            }
        
            #get the news html page content
            mailchimp_content = {"url": news_url}    
                        
            #create campaign
            rhizome_news_campaign = mailchimp_api.campaignCreate("regular", mailchimp_opts, mailchimp_content)
            
            #check to see if campaign created successfully
            try:
                mailchimp_return_error_notice =  "CAMPAIGN CREATION ERROR: %s..<br />." % (rhizome_news_campaign["error"])    
            except:
                mailchimp_return_success_notice = "New Campaign Created. ID = %s <br />" % rhizome_news_campaign
            
            #send the campaign or a test depending on "to" field
            if request.POST["to_email"] == "netartnewslist@rhizome.org":            
                #send the newsletter
                send_campaign = mailchimp_api.campaignSendNow(rhizome_news_campaign)
                
                #check for sending errors
                try:
                    mailchimp_return_error_notice +=  "SENDING ERROR: %s..<br />." % (send_campaign["error"]) 
                except:
                    mailchimp_return_success_notice += "Rhizome News Successfully Sent! Sent = %s<br />" % send_campaign
            else:
                #send a test address in "to" field
                test_email_addys = ["%s" % request.POST["to_email"]]
                send_test_campaign = mailchimp_api.campaignSendTest(rhizome_news_campaign, test_email_addys);
                
                #check for sending errors
                try:
                    mailchimp_return_error_notice +=  "TEST SENDING ERROR: %s...<br />" % (send_test_campaign["error"]) 
                except:
                    mailchimp_return_success_notice += " Test email sent! Success = %s<br />" % send_test_campaign

        context = {
            'app_label': self.model._meta.app_label,
            'admin_site': self.admin_site.name, 
            'title': "Send the News", 
            'opts': "Newsletters", 
            'from_name' : from_name,
            'from_email': from_email,
            'to_email':to_email,
            'subject': article,
            'news_url' : news_url,
            'mailchimp_return_error_notice':mailchimp_return_error_notice,
            'mailchimp_return_success_notice':mailchimp_return_success_notice
            }

        return render_to_response("admin/mailinglists/send_news.html", context, context_instance)  

admin.site.register(Newsletter, NewsletterAdmin)

class MemberAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    search_fields = ['user__email', 'user__username', 'user__first_name', 'user__last_name', 'email',]
    list_display = ('email', 'user', 'confirmed', 'approved', 'deleted', 'list')
    list_filter = ('confirmed', 'approved', 'deleted', 'listid')

    def list(self, obj):
        return obj.get_list()
    list.admin_order_field = 'listid'

admin.site.register(Member, MemberAdmin)

admin.site.register(List)

class MemberNewsletterAdmin(admin.ModelAdmin):
    model = MemberNewsletter
    raw_id_fields = ("featured_exhibition",)

    class Meta:
        member_newsletter_actions = (('send', 'Send A Member Newsletter'), )
                
    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
             url(r'send/$', self.admin_site.admin_view(self.send_member_newsletter), name='send_member_newsletter',),
        ) + super(MemberNewsletterAdmin, self).get_urls()

    def send_member_newsletter(self, request):
        mailchimp_api = PyChimp('3cb8530ce9770dc992d48f579b6bb09a-us1') 
        mailchimp_return_error_notice = ''
        mailchimp_return_success_notice = ''
        site = Site.objects.get(id=1)
        context_instance = RequestContext(request)

        try:
            newsletter = MemberNewsletter.objects.order_by('-created')[0] 
        except: 
            newsletter = None

        if not newsletter:
            context = {
                'app_label': self.model._meta.app_label,
                'admin_site': self.admin_site.name, 
                'title': "Send A Member Newsletter", 
                'opts': "Member Newsletters", 
                'from_name' :'',
                'from_email': '',
                'to_email': '',
                'subject': '',
                'newsletter_url' : '',
                'mailchimp_return_error_notice': 'NO NEWSLETTERS FOUND! GO CREATE ONE!',
                'mailchimp_return_success_notice': '',
                'site': site,
                }

            return render_to_response("admin/mailinglists/send_member_newsletter.html", context, context_instance)  


        today = datetime.date.today()
        newsletter_url = 'https://%s/member-newsletter/' % site.domain
        from_name = "RHIZOME"
        from_email = "membership@rhizome.org"
        to_email = "membership@rhizome.org"
        formatted_date =  today.strftime('%m.%d.%y')
        newsletter_title =  "RHIZOME MEMBER NEWSLETTER: %s" % formatted_date

        for mailchimp_list in mailchimp_api.lists():
            if mailchimp_list["name"] == "Rhizome Members Announcements":
                members_list = mailchimp_list
            if mailchimp_list["name"] == "Test List":    
                test_list = mailchimp_list    
        
        if request.method == 'POST':
        
            mailchimp_opts = {
                "list_id": members_list["id"],
                "subject": request.POST["subject"],
                "from_name": request.POST["from_name"],
                "from_email": request.POST["from_email"],
                "to_email": request.POST["to_email"],
                "tracking": {'opens':True, 'html_clicks':True, 'text_clicks':True},
                "authenticate": True,
                "title": newsletter_title,
                "generate_text": True
            }
        
            #get the news html page content
            mailchimp_content = {"url":newsletter_url}    
                        
            #create campaign
            member_newsletter_campaign = mailchimp_api.campaignCreate("regular", mailchimp_opts, mailchimp_content)
            
            #check to see if campaign created successfully
            try:
                mailchimp_return_error_notice =  "CAMPAIGN CREATION ERROR: %s...<br />" % (member_newsletter_campaign["error"])    
            except:
                mailchimp_return_success_notice = "New Campaign Created. ID = %s <br />" % member_newsletter_campaign
            
            #send the campaign or a test depending on "to" field
            if request.POST["to_email"] == "members@rhizome.org":            
                #send the newsletter
                send_campaign = mailchimp_api.campaignSendNow(member_newsletter_campaign)
                
                #check for sending errors
                try:
                    mailchimp_return_error_notice +=  "SENDING ERROR: %s...<br />" % (send_campaign["error"]) 
                except:
                    mailchimp_return_success_notice += "Member Newsletter Successfully Sent! Sent = %s<br />" % send_campaign
            
            else:
                #send a test address in "to" field
                test_email_addys = ["%s" % request.POST["to_email"]]
                send_test_campaign = mailchimp_api.campaignSendTest(member_newsletter_campaign, test_email_addys);
                
                #check for sending errors
                try:
                    mailchimp_return_error_notice +=  "TEST SENDING ERROR: %s...<br />" % (send_test_campaign["error"]) 
                except:
                    mailchimp_return_success_notice += " Test email sent! Success = %s<br />" % send_test_campaign

        context = {
            'app_label': self.model._meta.app_label,
            'admin_site': self.admin_site.name, 
            'title': "Send A Member Newsletter", 
            'opts': "Member Newsletters", 
            'from_name' : from_name,
            'from_email': from_email,
            'to_email':to_email,
            'subject': newsletter_title,
            'newsletter_url' : newsletter_url,
            'mailchimp_return_error_notice':mailchimp_return_error_notice,
            'mailchimp_return_success_notice':mailchimp_return_success_notice,
            'site': site,
            }

        return render_to_response("admin/mailinglists/send_member_newsletter.html", context, context_instance)  

admin.site.register(MemberNewsletter, MemberNewsletterAdmin)


