import csv

from django.contrib import admin
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse  

from orgsubs.models import *
from hitcount.models import Hit
from orgsubs.forms import OrganizationAdminForm

class OrganizationAdmin(admin.ModelAdmin):
    list_display  = ('name', 'size','get_member_count','expiration_date','email_domain','uri',)
    list_filter = ('active', 'cancelled')
    search_fields = ('name',)
    save_on_top = True
    raw_id_fields = ('country','state',)
    form = OrganizationAdminForm

admin.site.register(Organization,OrganizationAdmin)

class MonthlyStatisticsAdmin(admin.ModelAdmin):
    list_display  = ('org_sub','year_month','total_visits', 'ip_visits','member_visits')
    raw_id_fields = ('org_sub',)
    search_fields = ('org_sub__name',)
   
    def get_urls(self):
        from django.conf.urls.defaults import patterns
        return patterns('',
            (r'^run_stats_report/$', self.admin_site.admin_view(self.run_stats_report)),         
        ) + super(MonthlyStatisticsAdmin, self).get_urls()

    def run_stats_report(self, request):
        '''
        creates a csv of usage stats for an org sub
        
        '''
        context_instance = RequestContext(request)
        opts = self.model._meta
        admin_site = self.admin_site
        stats = None

        if request.method == "POST":
            request_orgsub = Organization.objects.get(id = request.POST.get('orgsub'))
            statistics = MonthlyStatistics.objects \
                .filter(org_sub = request_orgsub) \
                .order_by("year_month")


            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename="rhizome.org-visitation_stats_for_%s_%s.csv"' % \
                (str(request_orgsub.name).upper(), datetime.date.today())
            writer = csv.writer(response)
            writer.writerow(['VISITATION STATS FOR  %s (generated on %s)' % (str(request_orgsub.name).upper(), datetime.date.today())]) 
            writer.writerow(['RHIZOME.ORG'])            
            writer.writerow(
                            ['YEAR', 
                            'MONTH', 
                            'TOTAL VISITS*', 
                            'IP VISITS', 
                            'MEMBER VISITS',
                            '*note: ip visits + member visits do not add up to total visits. eg, a orgsub member could visit from an orgsub ip'
                            ]) 
            
            for stat in statistics:
                writer.writerow(
                            ['%s' % stat.year_month.year, 
                            '%s' % stat.year_month.month,
                            '%s' % stat.total_visits,
                            '%s' % stat.ip_visits,
                            '%s' % stat.member_visits
                            ]) 

            return response
            
        d = {'admin_site': admin_site.name, 
             'title': "Orgsub Stats Report", 
             'opts': "Monthly Statistics", 
             #'root_path': '/%s' % admin_site.root_path, 
             'app_label': opts.app_label,
             }
            
        return render_to_response('admin/orgsubs/organization/run_stats_report.html', d, context_instance)

admin.site.register(MonthlyStatistics, MonthlyStatisticsAdmin)

class ProspectiveUserAdmin(admin.ModelAdmin):
    list_display  = ('email','org_sub','invite_admin', 'accepted','created')
    save_on_top = True
    raw_id_fields = ('user','org_sub','invite_admin')
admin.site.register(ProspectiveUser,ProspectiveUserAdmin)

class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('org_sub','date','amount')
    raw_id_fields = ('org_sub',)
admin.site.register(Payment,PaymentAdmin)

class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ('org_sub','date','amount')
    raw_id_fields = ('org_sub',)
admin.site.register(Invoice, InvoiceAdmin)
