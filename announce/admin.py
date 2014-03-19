import datetime

from django.contrib import admin
from django.template.context import RequestContext
from django.shortcuts import render_to_response

from announce.models import Event, Job, Opportunity, JobPostingPayment

class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','country','state')
    search_fields = ['^user__email','^user__username','^user__first_name','^user__last_name', '^user__id','title','description']
    list_display  = ['title','user','created','status','id']
    save_on_top= True
admin.site.register(Event,EventAdmin)

class OpportunityAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','country','state')
    search_fields = ['^user__email','^user__username','^user__first_name','^user__last_name', '^user__id','title','description']
    list_display  = ['title','user','created','status','id']
    save_on_top= True
    
    def moderate(self,request):
        return moderate_announcements(request,self)

    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^stats/$', self.admin_site.admin_view(self.announce_stats)), 
        ) + super(OpportunityAdmin, self).get_urls()
    
    def announce_stats(self, request):
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
        
        today =  datetime.datetime.today()
        thirty_days_ago = today - datetime.timedelta(30)
        six_months_ago = today - datetime.timedelta(183)
        one_year_ago = today - datetime.timedelta(365)
    
        one_month_opps = Opportunity.objects.values('id').filter(status = True).filter(created__gte = thirty_days_ago).count()
        one_month_jobs = Job.objects.values('id').filter(status = True).filter(created__gte = thirty_days_ago).count()
        one_month_events = Event.objects.values('id').filter(status = True).filter(created__gte = thirty_days_ago).count()
        one_month_announcements = int(one_month_opps + one_month_jobs +one_month_events)       
    
        six_month_opps = Opportunity.objects.values('id').filter(status = True).filter(created__gte = six_months_ago).count()
        six_year_jobs = Job.objects.values('id').filter(status = True).filter(created__gte = six_months_ago).count()
        six_year_events = Event.objects.values('id').filter(status = True).filter(created__gte = six_months_ago).count()
        six_month_announcements = int(six_month_opps + six_year_jobs + six_year_events)     
    
        one_year_opps = Opportunity.objects.values('id').filter(status = True).filter(created__gte = one_year_ago).count()
        one_year_jobs = Job.objects.values('id').filter(status = True).filter(created__gte = one_year_ago).count()
        one_year_events = Event.objects.values('id').filter(status = True).filter(created__gte = one_year_ago).count()     
        one_year_announcements = int(one_year_opps + one_year_jobs + one_year_events)    
    
        all_time_opps = Opportunity.objects.values('id').filter(status = True).count()
        all_time_jobs = Job.objects.values('id').filter(status = True).count()
        all_time_events = Event.objects.values('id').filter(status = True).count()     
        all_time_announcements = int(all_time_opps + all_time_jobs + all_time_events)   
                
        context = {
            'admin_site': admin_site.name, 
            'title': "Announcement Moderation", 
            'opts': "Announce", 
            'app_label': opts.app_label,
            'one_month_announcements': one_month_announcements,
            'six_month_announcements': six_month_announcements,
            'one_year_announcements': one_year_announcements,
            'all_time_announcements': all_time_announcements
        }
    
        return render_to_response("admin/announce/stats.html", context, context_instance=RequestContext(request))  
    
admin.site.register(Opportunity,OpportunityAdmin)

class JobAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','country','state')
    search_fields = ['^user__email','^user__username','^user__first_name','^user__last_name', '^user__id','title','description']
    list_display  = ['title','user','created','status','id']
    save_on_top= True
admin.site.register(Job,JobAdmin)

class JobPostingPaymentAdmin(admin.ModelAdmin):
    raw_id_fields = ('user','job')
    search_fields = ['^user__email','^user__username','^user__first_name','^user__last_name', '^user__id','job__title','job__description']
    list_display  = ['job','user','created','id']
    save_on_top= True
admin.site.register(JobPostingPayment,JobPostingPaymentAdmin)
